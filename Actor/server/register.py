import socket
import sys

import status

sys.path.append("..")
import grpc
import code_pb2
import code_pb2_grpc

#注册的函数
def Register_Send():
    with grpc.insecure_channel(socket.gethostbyname("master")+':10086') as channel:
        client = code_pb2_grpc.UnaryStub(channel)
        response = client.Register(code_pb2.register_request(data=status._global_STATUS))
        print('注册结果:', response.message)
    return response.message