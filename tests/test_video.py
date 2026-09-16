import cv2
import numpy as np

from app.video import render_photo_promo, storyboard


def test_storyboard_uses_each_supplied_photo_once(tmp_path):
    images=[]
    for index, brightness in enumerate((40, 180, 100)):
        image=np.full((80,120,3),brightness,dtype=np.uint8)
        path=tmp_path/f"room_{index}.jpg"; cv2.imwrite(str(path),image); images.append(path)
    plan=storyboard(images,2.5)
    assert plan["duration_seconds"] == 7.5
    assert {shot["source_image"] for shot in plan["shots"]} == {image.name for image in images}
    assert all(shot["movement"] == "slow_push_in" for shot in plan["shots"])
    rendered=render_photo_promo(images[:1],tmp_path/"video",1)
    assert (tmp_path/"video"/"promotional_video.mp4").is_file()
    assert rendered["shots"] == 1
