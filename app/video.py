"""Local photo-set to cinematic promotional-video renderer."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .vision import image_features

DEFAULT_FFMPEG = Path(r"C:\Users\koanr\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe")


def ffmpeg_path() -> str:
    configured=os.getenv("ASTRA_FFMPEG_PATH")
    if configured and Path(configured).is_file(): return configured
    if DEFAULT_FFMPEG.is_file(): return str(DEFAULT_FFMPEG)
    raise RuntimeError("FFmpeg was not found; set ASTRA_FFMPEG_PATH")


def storyboard(images: list[Path], duration_seconds: float = 3.0) -> dict:
    if not images: raise ValueError("At least one image is required")
    evidence=[image_features(image) for image in images]
    # Lead with bright/wide-looking frames, retain every supplied photo once.
    ordered=sorted(evidence,key=lambda item:(item["image_quality"]["brightness"], item["camera_estimate"]["perspective_line_count"]),reverse=True)
    return {"format":"cinematic_photo_promo_v1","duration_seconds":round(len(ordered)*duration_seconds,1),"shots":[{"order":index+1,"source_image":item["image"],"duration_seconds":duration_seconds,"movement":"slow_push_in","transition":"cross_dissolve" if index else "fade_from_black","visual_evidence":{"brightness":item["image_quality"]["brightness"],"perspective_lines":item["camera_estimate"]["perspective_line_count"]},"note":"Uses the provided property photograph; no unseen room or amenity is invented."} for index,item in enumerate(ordered)]}


def render_photo_promo(images: list[Path], output_dir: Path, duration_seconds: float = 3.0) -> dict:
    output_dir.mkdir(parents=True,exist_ok=True)
    plan=storyboard(images,duration_seconds)
    (output_dir/"storyboard.json").write_text(json.dumps(plan,indent=2))
    clips=[]; executable=ffmpeg_path()
    for shot in plan["shots"]:
        source=next(image for image in images if image.name == shot["source_image"])
        clip=output_dir/f"shot_{shot['order']:03d}.mp4"; frames=max(1,round(duration_seconds*30))
        vf=f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,zoompan=z='min(zoom+0.0008,1.08)':d={frames}:s=1280x720:fps=30,format=yuv420p"
        subprocess.run([executable,"-y","-loop","1","-i",str(source),"-vf",vf,"-frames:v",str(frames),"-r","30","-an",str(clip)],check=True,capture_output=True,text=True,timeout=180)
        clips.append(clip)
    playlist=output_dir/"concat.txt"; playlist.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clips),encoding="utf-8")
    final=output_dir/"promotional_video.mp4"
    subprocess.run([executable,"-y","-f","concat","-safe","0","-i",str(playlist),"-c","copy",str(final)],check=True,capture_output=True,text=True,timeout=180)
    return {"video":str(final),"storyboard":str(output_dir/"storyboard.json"),"shots":len(clips),"duration_seconds":plan["duration_seconds"]}
