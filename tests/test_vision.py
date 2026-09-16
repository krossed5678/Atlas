import cv2
import numpy as np

from app.vision import image_features, reconstruction_score


def test_computer_vision_features_and_score(tmp_path):
    image=np.zeros((120,160,3),dtype=np.uint8)
    cv2.line(image,(5,100),(155,20),(255,255,255),2)
    cv2.line(image,(80,5),(80,115),(255,255,255),2)
    source=tmp_path/'reference.jpg'; render=tmp_path/'render.jpg'
    cv2.imwrite(str(source),image); cv2.imwrite(str(render),image)
    features=image_features(source)
    assert features['dimensions_px'] == {'width':160,'height':120}
    assert features['camera_estimate']['perspective_line_count'] > 0
    score=reconstruction_score(source,render)
    assert score['reconstruction_score'] == 100.0 and score['acceptance'] == 'PASS'
