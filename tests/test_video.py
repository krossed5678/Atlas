import cv2
import numpy as np
import wave

from app.audio import detect_beats
from app.video import render_photo_promo, storyboard


def test_storyboard_uses_each_supplied_photo_once(tmp_path):
    images=[]
    for index, brightness in enumerate((40, 180, 100)):
        image=np.full((80,120,3),brightness,dtype=np.uint8)
        path=tmp_path/f"room_{index}.jpg"; cv2.imwrite(str(path),image); images.append(path)
    plan=storyboard(images,2.5)
    assert plan["duration_seconds"] == 6.0
    assert {shot["source_image"] for shot in plan["shots"]} == {image.name for image in images}
    assert len({shot["movement"] for shot in plan["shots"]}) > 1
    rendered=render_photo_promo(images[:1],tmp_path/"video",1,320,180,"test.mp4")
    assert (tmp_path/"video"/"test.mp4").is_file()
    assert rendered["shots"] == 1
    rendered_two=render_photo_promo(images[:2],tmp_path/"video-two",1,320,180,"test.mp4")
    assert (tmp_path/"video-two"/"test.mp4").is_file() and rendered_two["shots"] == 2


def test_local_licensed_audio_produces_beat_map_and_attached_video(tmp_path):
    image=np.full((80,120,3),130,dtype=np.uint8); image_path=tmp_path/"room.jpg"; cv2.imwrite(str(image_path),image)
    rate=22050; samples=np.zeros(rate*2,dtype=np.int16)
    for start in (0, rate//2, rate, rate+rate//2): samples[start:start+500]=18000
    audio=tmp_path/"licensed.wav"
    with wave.open(str(audio),"wb") as output: output.setnchannels(1); output.setsampwidth(2); output.setframerate(rate); output.writeframes(samples.tobytes())
    beats=detect_beats(audio,render_photo_promo.__globals__["ffmpeg_path"]())
    assert beats["beat_times"]
    rendered=render_photo_promo([image_path],tmp_path/"video-audio",1,320,180,"test.mp4",audio,"Test track permission")
    assert rendered["music_attached"] and (tmp_path/"video-audio"/"beat_map.json").is_file()


def test_bespoke_score_is_the_default_for_property_film(tmp_path):
    image=np.full((80,120,3),130,dtype=np.uint8); image_path=tmp_path/"room.jpg"; cv2.imwrite(str(image_path),image)
    rendered=render_photo_promo([image_path],tmp_path/"bespoke",1,320,180,"test.mp4")
    assert rendered["bespoke_score"]["rights"] == "bespoke_local_generated"
    assert (tmp_path/"bespoke"/"bespoke_luxury_score.wav").is_file()
