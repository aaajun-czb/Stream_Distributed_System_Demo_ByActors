import cv2
import numpy as np
import base64
from concurrent.futures import ThreadPoolExecutor
import time

import grpc
import code_pb2
import code_pb2_grpc

import status
import worker_info

global executor
executor = ThreadPoolExecutor(max_workers=2)

class Worker_Info(object):
    def __init__(self, 
                master,morphological_process, pre_process,
                morphological_process_backup = None, 
                pre_process_backup = None):
        self.morphological_process=morphological_process
        self.pre_process=pre_process
        self.morphological_process_backup=morphological_process_backup
        self.pre_process_backup=pre_process_backup
        self.master=master
    
    def save_info(self):
        worker_info.set_value('master', self.master)
        worker_info.set_value('morphological_process', self.morphological_process)
        worker_info.set_value('pre_process', self.pre_process)
        worker_info.set_value('morphological_process_backup', self.morphological_process_backup)
        worker_info.set_value('pre_process_backup', self.pre_process_backup)

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
    with grpc.insecure_channel(worker_info.get_value('morphological_process')) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        try:
            response = client.MaskTransmission(send_mask_stream())
            print('Mask Transmission :'+response.result)
        except grpc.RpcError as e:
            print('Mask Transmission '+worker_info.get_value('morphological_process')+':'+e.details())

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
            print(mask_count)
            yield code_pb2.contours_trans_request(xywh=xywh)
        except:
            break

def morphological_process():
    with grpc.insecure_channel(worker_info.get_value('master')) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        try:
            response = client.ContoursTransmission(send_contours_stream())
            print('Contours Transmission : '+response.result)
        except grpc.RpcError as e:
            print('Contours Transmission '+worker_info.get_value('master')+':'+e.details())

class Task(code_pb2_grpc.TaskServicer): 
    def IdleAsk(self, request, context):
        if status.get_value('Idle')=='1':
            status.set_value('Idle', 0)
            return code_pb2.idleask_response(message='ok')
        else:
            return code_pb2.idleask_response(message='sorry')

    def WorkerNodesInfo(self, request, context):
        worker_info.init()
        _Worker_Info = Worker_Info(request.worker_nodes_info['master'],
                                   request.worker_nodes_info['morphological_process'],
                                   request.worker_nodes_info['pre_process'],
                                   request.worker_nodes_info['morphological_process_backup'],
                                   request.worker_nodes_info['pre_process_backup'])
        _Worker_Info.save_info()
        return code_pb2.worker_nodes_info_response(result='ok')

    def FrameTransmission(self, request_iterator, context):
        executor.submit(pre_process)
        frame_count=0
        for i in request_iterator:
            img_data = base64.b64decode(bytes(i.image, encoding='utf8'))
            save_path='./images/test'+str(frame_count)+'.jpg'
            with open(save_path, 'wb') as f:
                f.write(img_data)
            frame_count += 1
        return code_pb2.frame_trans_response(result='ok')

    def MaskTransmission(self, request_iterator, context):
        executor.submit(morphological_process)
        mask_count=0
        for i in request_iterator:
            mask_data = base64.b64decode(bytes(i.mask, encoding='utf8'))
            mask_array = np.fromstring(mask_data, np.uint8)
            mask = mask_array.reshape(480,854)
            save_path='./images/test'+str(mask_count)+'.jpg'
            cv2.imwrite(save_path, mask)
            mask_count += 1
        return code_pb2.mask_trans_response(result='ok')

    def ContoursTransmission(self, request_iterator, context):
        # min_w = 90; min_h = 90
        cap = cv2.VideoCapture('test.avi')
        fps = cap.get(cv2.CAP_PROP_FPS)
        sizes = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        four_cc = cv2.VideoWriter_fourcc(*"MJPG")
        video_writer = cv2.VideoWriter('output.avi', four_cc, fps, sizes)
        frame_count = 0
        for i in request_iterator:
            ret, frame = cap.read()
            print('frame_count: '+str(frame_count))
            frame_count += 1
            for object in i.xywh:
                (x,y,w,h)=(object.x,object.y,object.w,object.h)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
            video_writer.write(frame)
        video_writer.release()
        return code_pb2.contours_trans_response(result='ok')
