import logging
import time
import cv2
import numpy as np
import base64

import grpc
import code_pb2
import code_pb2_grpc

def send_frame_stream(cap):
    count = 0
    while True:
        ret, frame = cap.read()
        time.sleep(1)
        count += 1
        if(ret == True):
            try:
                str = base64.b64encode(frame)
                yield code_pb2.frame_trans_request(image=str)
                if(count ==5):
                    break
            except grpc.RpcError as e:
                print(e.details())
                continue
        else:
            break

def Video_Transmission(path, bind_address) -> None:
    cap = cv2.VideoCapture(path)
    with grpc.insecure_channel(bind_address) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        response = client.Frame_Transmission(send_frame_stream(cap), timeout=5)
        print(response.result)
    cap.release()

if __name__ == '__main__':
    logging.basicConfig()
    Video_Transmission('test.avi', '192.168.0.5:10086')