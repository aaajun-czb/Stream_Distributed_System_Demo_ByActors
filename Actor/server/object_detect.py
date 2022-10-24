import cv2
import sys
import time
import base64

import shared_info
import status

sys.path.append("..")
import grpc
import code_pb2
import code_pb2_grpc

def send_mask_stream():
    time.sleep(2)
    bgsubmog = cv2.createBackgroundSubtractorMOG2()
    mask_count = 0
    while True:
        try:
            load_path='./images/test'+str(mask_count)+'.jpg'
            img_gray = cv2.imread(load_path, cv2.IMREAD_GRAYSCALE)
            mask_count += 1
            blur = cv2.GaussianBlur(img_gray, (3, 3), 5)  # 高斯去噪
            mask = bgsubmog.apply(blur)  # 去背影，获取前景物体
            content = str(base64.b64encode(mask), encoding='utf8')
            yield code_pb2.mask_trans_request(mask=content)
        except:
            break     

def pre_process():
    with grpc.insecure_channel(shared_info.worker_info_get_value('morphological_process')) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        try:
            response = client.MaskTransmission(send_mask_stream())
            print('Mask Transmission :'+response.result)
            status.set_value('Idle', '1')
        except grpc.RpcError as e:
            print('Mask Transmission '+shared_info.worker_info_get_value('morphological_process')+':'+e.details())

def send_contours_stream():
    time.sleep(2)
    mask_count = 0
    while True:
        try:
            load_path='./images/test'+str(mask_count)+'.jpg'
            mask = cv2.imread(load_path, cv2.IMREAD_GRAYSCALE)
            mask_count += 1
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5)) # 形态学kernel
            erode = cv2.erode(mask, kernel) # 腐蚀，去掉图中小斑块
            dilate = cv2.dilate(erode, kernel, iterations=3) # 膨胀，还原放大
            close = cv2.morphologyEx(dilate, cv2.MORPH_CLOSE, kernel) # 闭操作，去掉物体内部的小方块
            contours, hierarchy = cv2.findContours(close, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # 根据二值图找轮廓
            xywh=[]
            for (i, c) in enumerate(contours):
                (x,y,w,h) = cv2.boundingRect(c)
                xywh.append(code_pb2.XYWH(x=x,y=y,w=w,h=h))
            yield code_pb2.contours_trans_request(xywh=xywh)
        except:
            break

def morphological_process():
    with grpc.insecure_channel(shared_info.worker_info_get_value('master')) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        try:
            response = client.ContoursTransmission(send_contours_stream())
            print('Contours Transmission : '+response.result)
            status.set_value('Idle', '1')
        except grpc.RpcError as e:
            print('Contours Transmission '+shared_info.worker_info_get_value('master')+':'+e.details())