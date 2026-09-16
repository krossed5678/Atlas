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
    moves=("slow_push_in","cinematic_drift_right","slow_pull_back","cinematic_drift_left")
    transitions=("fade","wipeleft","smoothleft","fadeblack")
    return {"format":"cinematic_photo_promo_v2","duration_seconds":round(len(ordered)*duration_seconds-.75*max(0,len(ordered)-1),1),"looks":{"grade":"warm_luxury","contrast":"gentle","detail":"subtle_sharpening","transitions":"cross_dissolve_and_motion"},"shots":[{"order":index+1,"source_image":item["image"],"duration_seconds":duration_seconds,"movement":moves[index%len(moves)],"transition":transitions[(index-1)%len(transitions)] if index else "fade_from_black","visual_evidence":{"brightness":item["image_quality"]["brightness"],"perspective_lines":item["camera_estimate"]["perspective_line_count"]},"note":"Uses the provided property photograph; no unseen room or amenity is invented."} for index,item in enumerate(ordered)]}


def render_photo_promo(images: list[Path], output_dir: Path, duration_seconds: float = 3.0, width: int = 1920, height: int = 1080, filename: str = "promotional_video_luxury.mp4") -> dict:
    output_dir.mkdir(parents=True,exist_ok=True)
    plan=storyboard(images,duration_seconds)
    (output_dir/"storyboard.json").write_text(json.dumps(plan,indent=2))
    clips=[]; executable=ffmpeg_path()
    for shot in plan["shots"]:
        source=next(image for image in images if image.name == shot["source_image"])
        clip=output_dir/f"shot_{shot['order']:03d}.mp4"; frames=max(1,round(duration_seconds*30))
        movement=shot["movement"]
        if movement == "slow_pull_back": zoom="if(eq(on,1),1.12,max(1.0,zoom-0.0009))"
        else: zoom="min(zoom+0.0009,1.12)"
        pan="iw/2-(iw/zoom/2)" if movement != "cinematic_drift_left" else "iw/2-(iw/zoom/2)-on*0.15"
        vf=f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},zoompan=z='{zoom}':x='{pan}':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps=30,eq=contrast=1.08:saturation=1.06:brightness=-0.015,unsharp=5:5:0.35:5:5:0,fade=t=in:st=0:d=0.45,fade=t=out:st={max(0,duration_seconds-.45)}:d=0.45,format=yuv420p"
        subprocess.run([executable,"-y","-loop","1","-i",str(source),"-vf",vf,"-frames:v",str(frames),"-r","30","-an",str(clip)],check=True,capture_output=True,text=True,timeout=240)
        clips.append(clip)
    working=clips[0]; merged_duration=duration_seconds
    for index, clip in enumerate(clips[1:], start=1):
        merged=output_dir/f"merge_{index:03d}.mp4"; transition=plan["shots"][index]["transition"]
        subprocess.run([executable,"-y","-i",str(working),"-i",str(clip),"-filter_complex",f"[0:v][1:v]xfade=transition={transition}:duration=0.75:offset={max(0,merged_duration-.75):.3f},format=yuv420p","-an",str(merged)],check=True,capture_output=True,text=True,timeout=240)
        working=merged; merged_duration += duration_seconds-.75
    final=output_dir/filename
    if working != final: subprocess.run([executable,"-y","-i",str(working),"-c","copy",str(final)],check=True,capture_output=True,text=True,timeout=180)
    return {"video":str(final),"storyboard":str(output_dir/"storyboard.json"),"shots":len(clips),"duration_seconds":plan["duration_seconds"],"resolution":f"{width}x{height}","look":"warm_luxury"}
