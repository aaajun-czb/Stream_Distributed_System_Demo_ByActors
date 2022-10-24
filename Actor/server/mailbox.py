import cv2
import numpy as np
import base64
import time
import sys
import json

import shared_info
import status
import object_detect

sys.path.append("..")
import grpc
import code_pb2
import code_pb2_grpc

def WorkingCheck():
    time.sleep(60)
    if status.get_value('Working') == '0':
        status.set_value('Idle', '1')
        print('No request, release the occupation')

class Task(code_pb2_grpc.TaskServicer): 
    def IdleAsk(self, request, context):
        if status.get_value('Idle')=='1':
            status.set_value('Idle', '0')
            status.set_value('Working', '0')
            shared_info.thread_init()
            shared_info.thread_submit(WorkingCheck)
            return code_pb2.idleask_response(message='ok')
        else:
            return code_pb2.idleask_response(message='sorry')

    def WorkerNodesInfo(self, request, context):
        if status.get_value('Idle') == '1':
            response_data = {"sub_code": 40301, "message": 'The Node is not occupied!'}
            context.set_details(json.dumps(response_data))  # 设置报错信息
            context.set_code(grpc.StatusCode.PremissionDenied)     # 指定状态码错误类型
            raise context
        shared_info.init()
        shared_info.save_object_detect_info(request.worker_nodes_info['master'],
                                   request.worker_nodes_info['morphological_process'],
                                   request.worker_nodes_info['pre_process'],
                                   request.worker_nodes_info['morphological_process_backup'],
                                   request.worker_nodes_info['pre_process_backup'])
        return code_pb2.worker_nodes_info_response(result='ok')

    def FrameTransmission(self, request_iterator, context):
        if status.get_value('Idle') == '1':
            response_data = {"sub_code": 40301, "message": 'The Node is not occupied!'}
            context.set_details(json.dumps(response_data))  # 设置报错信息
            context.set_code(grpc.StatusCode.PremissionDenied)     # 指定状态码错误类型
            raise context
        status.set_value('Working', '1')
        shared_info.thread_submit(object_detect.pre_process)
        frame_count=0
        for i in request_iterator:
            img_data = base64.b64decode(bytes(i.image, encoding='utf8'))
            save_path='./images/test'+str(frame_count)+'.jpg'
            with open(save_path, 'wb') as f:
                f.write(img_data)
            frame_count += 1
        return code_pb2.frame_trans_response(result='ok')

    def MaskTransmission(self, request_iterator, context):
        if status.get_value('Idle') == '1':
            response_data = {"sub_code": 40301, "message": 'The Node is not occupied!'}
            context.set_details(json.dumps(response_data))  # 设置报错信息
            context.set_code(grpc.StatusCode.PremissionDenied)     # 指定状态码错误类型
            raise context
        status.set_value('Working', '1')
        shared_info.thread_submit(object_detect.morphological_process)
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
        for i in request_iterator:
            ret, frame = cap.read()
            for object in i.xywh:
                (x,y,w,h)=(object.x,object.y,object.w,object.h)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
            video_writer.write(frame)
        video_writer.release()
        print('Video has been output!')
        return code_pb2.contours_trans_response(result='ok')
