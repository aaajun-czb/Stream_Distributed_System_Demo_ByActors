from concurrent import futures
import json
import logging
import time

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

#定义Stream类
class Stream(code_pb2_grpc.StreamServicer):
    #用于发送节点信息
    def Inquiry(self, request_iterator, context):
        #获取Redis中注册信息并转换成List拼接
        actor_nodes_IP=redis_operate.getAllKeys()
        actor_nodes=[]
        for i in actor_nodes_IP:
            str="".join(redis_operate.getJsonByKey(i))
            tmp=json.loads(str)
            #如果空闲就拼接进去
            if tmp['Idle']=='1':
                tmp['IPAddress']=i
                actor_nodes.append(tmp)
        #将List转换成json格式写入Nodes.json文件中
        with open('Nodes.json','w+') as f:
            json.dump(actor_nodes,f)
        #传输Nodes.json文件
        with open('Nodes.json', 'rb') as f:
            n = 0
            while True:
                content = f.read(1024)
                if content:
                    n = n + 1
                    yield code_pb2.inquiry_response(data=content)
                else:
                    break

def Inquiry_Send(bind_address):
    """Start a inquiry server in a subprocess."""
    _LOGGER.info('Starting inquiry server.')
    options = (('grpc.so_reuseport', 1),)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4,),options=options)
    code_pb2_grpc.add_StreamServicer_to_server(Stream(), server)
    server.add_insecure_port(bind_address)
    server.start()
    _wait_forever(server)