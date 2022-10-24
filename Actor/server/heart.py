import time
import sys

import status

sys.path.append("..")
import code_pb2
import code_pb2_grpc

def create_response() -> code_pb2.heartcheck_response:
    response = code_pb2.heartcheck_response()
    response.ipaddress = status.get_value('IPAddress')
    response.idle =  status.get_value('Idle')
    return response

class Heart(code_pb2_grpc.StreamServicer):
    def __init__(self):
        self._id_counter = 0

    def HeartCheck(self, request,context):
        try:
            print("Received a heart check request: [%s]",request.message)
        except StopIteration:
            raise RuntimeError("Failed to receive call request")
        #after the acceptance of request
        while True:
            time.sleep(3)
            try:
                # print('I have sent heartcheck')
                yield create_response()
            except StopIteration:
                break
        print("heart check finished.")
