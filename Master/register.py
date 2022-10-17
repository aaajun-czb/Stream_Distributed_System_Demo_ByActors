from concurrent import futures
import json
import logging
import time
import subprocess

import grpc
import code_pb2
import code_pb2_grpc

import redis_operate

_LOGGER = logging.getLogger(__name__)

def _wait_forever(server):
    try:
        while True:
            time.sleep(60*60*24)
    except KeyboardInterrupt:
        server.stop(None)

#定义一个Actor节点类
class Actor_Node(object):
    def __init__(self, IPAddress, Port, Name, Idle, Memory, CPU):
        self.IPAddress=IPAddress
        self.Port=Port
        # self.HeartPort=HeartPort
        # self.TaskPort=TaskPort
        self.Name=Name
        self.Idle=Idle
        self.Memory=Memory
        self.CPU=CPU
    
    def returnList(self):
        return {
            'Name':self.Name,
            'Port':self.Port,
            'Idle':self.Idle,'Memory':self.Memory,'CPU':self.CPU
        }

#定义处理Request的类
class Unary(code_pb2_grpc.UnaryServicer):
    #用于接受注册信息
    def Register(self, request, context):
        print('接收到来自 %s 的注册信息.' %request.data['IPAddress'])
        register_node = Actor_Node(request.data['IPAddress'],
                                   request.data['Port'],
                                   request.data['Name'],
                                   request.data['Idle'],
                                   request.data['Memory'],
                                   request.data['CPU'])
        redis_operate.insertRedis(register_node.IPAddress, json.dumps(register_node.returnList()))
        child1 = subprocess.Popen(
            ['python', 'heart.py', register_node.IPAddress, register_node.Port], 
            stdout=subprocess.PIPE
        )
        return code_pb2.register_response(message='ok')

def Register_Receive(bind_address):
    """Start a register server in a subprocess."""
    _LOGGER.info('Starting register server.')
    options = (('grpc.so_reuseport', 1),)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4,),options=options)
    code_pb2_grpc.add_UnaryServicer_to_server(Unary(), server)
    server.add_insecure_port(bind_address)
    server.start()
    _wait_forever(server)