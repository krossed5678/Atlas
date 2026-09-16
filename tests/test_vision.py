import cv2
import numpy as np

from app.main import PROPERTIES
from app.vision import image_features, reconstruction_score
from app.worker import process_one


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


def test_worker_persists_cv_outputs_without_model(tmp_path, monkeypatch):
    image=np.full((100,100,3),170,dtype=np.uint8)
    source=tmp_path/'source.jpg'; cv2.imwrite(str(source),image)
    property_id='property_cv_worker'; root=PROPERTIES/property_id
    for relative in ('source/original_images','analysis'): (root/relative).mkdir(parents=True,exist_ok=True)
    (root/'source/original_images'/'room.jpg').write_bytes(source.read_bytes())
    from app.main import connect, now
    c=connect(); c.execute("insert into properties values (?,?,?,?,?,?,?)",(property_id,'','cv-worker','INTAKE_COMPLETE',now(),1,0)); c.execute("insert into jobs values (?,?,?,?,?,?,?,?,?)",('cv-job','property_analysis',property_id,'queued','intake',0,None,now(),now()));c.commit();c.close()
    monkeypatch.setattr('app.worker.ollama_health',lambda:{'reachable':False})
    result=process_one()
    assert result['status'] == 'cv_analyzed_awaiting_model'
    assert (root/'analysis'/'camera_estimates.json').is_file()
    assert (root/'analysis'/'material_estimates.json').is_file()
