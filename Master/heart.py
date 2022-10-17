import time
import json
import sys

import grpc
import code_pb2
import code_pb2_grpc

import redis_operate

#与已注册Actor节点建立心跳检测的函数
def Heart_Check(IPAddress, Port):
    time.sleep(10)
    print('与 %s 开始建立心跳检测.' %IPAddress)
    with grpc.insecure_channel(IPAddress+':'+Port) as channel:
        client = code_pb2_grpc.StreamStub(channel)
        retry_nums = 0
        while retry_nums < 5:
            try:
                response = client.HeartCheck(code_pb2.heartcheck_request(message='R U ok?'))
                for i in response:
                    str="".join(redis_operate.getJsonByKey(IPAddress))
                    tmp=json.loads(str)
                    tmp['Idle']=i.idle
                    redis_operate.insertRedis(IPAddress, json.dumps(tmp))
            except grpc.RpcError as e:
                print(e.details())
                status_code = e.code()
                if status_code.name == 'UNAVAILABLE':
                    #14代表unavailable，根据实测大概率是actor那边还没准备好，因为一些多进程的原因
                    #经过测试，一次连不上反复多连几次大概率就连上了
                    retry_nums += 1
                    time.sleep(10)
                else:
                    break
        #心跳连接结束了，删除IPAddress的信息
        redis_operate.deleteRedis(IPAddress)

if __name__ == "__main__":
    redis_operate.init()
    Heart_Check(sys.argv[1], sys.argv[2])