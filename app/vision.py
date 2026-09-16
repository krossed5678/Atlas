"""Deterministic computer-vision signals for property reconstruction.

These measurements are evidence, not claims of exact dimensions. They feed the
local model and Blender workflow with confidence-tagged, reproducible inputs.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity


def image_features(path: Path) -> dict:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unreadable image: {path.name}")
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=max(30, min(width, height)//8), minLineLength=max(20, min(width, height)//7), maxLineGap=12)
    segments=[]
    if lines is not None:
        for x1,y1,x2,y2 in lines[:,0][:120]:
            angle=float(np.degrees(np.arctan2(y2-y1,x2-x1)))
            length=float(np.hypot(x2-x1,y2-y1))
            segments.append({"angle_degrees":round(angle,2),"length_px":round(length,1),"midpoint":[round(float((x1+x2)/2),1),round(float((y1+y2)/2),1)]})
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    brightness=float(np.mean(hsv[:,:,2])/255)
    saturation=float(np.mean(hsv[:,:,1])/255)
    dominant=np.mean(image.reshape(-1,3),axis=0)[::-1]
    horizontal=sum(1 for line in segments if abs(line["angle_degrees"]) < 12 or abs(abs(line["angle_degrees"])-180)<12)
    vertical=sum(1 for line in segments if abs(abs(line["angle_degrees"])-90)<12)
    confidence=min(.92, .25 + len(segments)/180)
    histogram=cv2.calcHist([gray],[0],None,[256],[0,256]).ravel(); probability=histogram/max(1,histogram.sum()); entropy=float(-np.sum(probability[probability>0]*np.log2(probability[probability>0]))/8)
    flipped=cv2.flip(gray,1); symmetry=float(np.corrcoef(gray.ravel(),flipped.ravel())[0,1]) if np.std(gray) and np.std(flipped) else 0.0
    brightness_fit=max(0.0,1-abs(brightness-.60)/.60)
    composition_score=float(np.clip(.35*brightness_fit+.30*entropy+.20*max(0,symmetry)+.15*min(1,len(segments)/50),0,1))
    return {
        "image":path.name,
        "dimensions_px":{"width":width,"height":height},
        "image_quality":{"edge_density":round(float(np.mean(edges>0)),4),"brightness":round(brightness,3),"saturation":round(saturation,3)},
        "camera_estimate":{"perspective_line_count":len(segments),"horizontal_line_count":horizontal,"vertical_line_count":vertical,"confidence":round(confidence,2),"note":"Line geometry supports a camera estimate; focal length and real-world scale remain uncertain without multiple views or measurements."},
        "material_color_estimate":{"mean_rgb":[round(float(value),1) for value in dominant],"confidence":0.55},
        "aesthetic_signals":{"composition_score":round(composition_score,3),"visual_entropy":round(entropy,3),"symmetry":round(symmetry,3),"brightness_fit":round(brightness_fit,3)},
        "line_segments":segments,
        "uncertainty":["No absolute scale can be inferred from a single image.","Occluded geometry requires multi-view or human review."],
    }


def reconstruction_score(reference: Path, render: Path) -> dict:
    """Score rendered/reference images using SSIM, edges, and color distance."""
    a=cv2.imread(str(reference),cv2.IMREAD_COLOR); b=cv2.imread(str(render),cv2.IMREAD_COLOR)
    if a is None or b is None: raise ValueError("Reference and render must both be readable")
    b=cv2.resize(b,(a.shape[1],a.shape[0]),interpolation=cv2.INTER_AREA)
    gray_a=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gray_b=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ssim=float(structural_similarity(gray_a,gray_b,data_range=255))
    ea=cv2.Canny(gray_a,70,160); eb=cv2.Canny(gray_b,70,160)
    edge_iou=float(np.logical_and(ea>0,eb>0).sum()/max(1,np.logical_or(ea>0,eb>0).sum()))
    color=float(1-min(1,np.mean(np.abs(a.astype(float)-b.astype(float)))/255))
    total=round(100*(.5*ssim+.3*edge_iou+.2*color),1)
    return {"reconstruction_score":total,"components":{"structural_similarity":round(ssim,3),"edge_similarity":round(edge_iou,3),"color_similarity":round(color,3)},"acceptance":"PASS" if total>=75 else "ITERATE","confidence":0.7}
