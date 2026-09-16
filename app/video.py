"""Local photo-set to cinematic promotional-video renderer."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import numpy as np

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
    # Start and end on the strongest composition, but retain each supplied image once.
    ranked=sorted(evidence,key=lambda item:item["aesthetic_signals"]["composition_score"],reverse=True)
    if len(ranked)>2:
        opening, closing=ranked[0],ranked[1]
        remaining=ranked[2:]
        ordered=[opening,*remaining,closing]
    else: ordered=ranked
    moves=("slow_push_in","cinematic_drift_right","slow_pull_back","cinematic_drift_left")
    transitions=("fade","wipeleft","smoothleft","fadeblack")
    shots=[]
    for index,item in enumerate(ordered):
        role="opening" if index==0 else ("closing" if index==len(ordered)-1 else "chapter")
        previous=ordered[index-1] if index else None
        compatibility=1.0 if not previous else 1-min(1,np.mean(np.abs(np.array(item["material_color_estimate"]["mean_rgb"])-np.array(previous["material_color_estimate"]["mean_rgb"]))/255))
        transition="fade_from_black" if not index else ("smoothleft" if compatibility>=.88 else "fade")
        shots.append({"order":index+1,"sequence_role":role,"source_image":item["image"],"duration_seconds":duration_seconds,"movement":moves[index%len(moves)],"transition":transition,"visual_evidence":{"composition_score":item["aesthetic_signals"]["composition_score"],"brightness":item["image_quality"]["brightness"],"perspective_lines":item["camera_estimate"]["perspective_line_count"],"transition_compatibility":round(float(compatibility),3)},"note":"Uses the provided property photograph; no unseen room or amenity is invented."})
    return {"format":"cinematic_photo_promo_v3","duration_seconds":round(len(ordered)*duration_seconds-.75*max(0,len(ordered)-1),1),"looks":{"grade":"warm_luxury","contrast":"gentle","detail":"subtle_sharpening","transitions":"composition_aware"},"shots":shots}


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
