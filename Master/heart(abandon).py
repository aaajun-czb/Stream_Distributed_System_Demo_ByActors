'''废弃的双向流连接的heart'''

import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import logging
import threading
from typing import Iterator

import grpc
import code_pb2
import code_pb2_grpc

import redis_operate

def send_stream():
    while True:
        time.sleep(1)
        yield code_pb2.heartcheck_request(message='Are U OK?')

class HeartMaker:
    def __init__(self, executor: ThreadPoolExecutor, channel: grpc.Channel, IPAddress: str, Port: str) -> None:
        self._executor = executor
        self._channel = channel
        self._stub = code_pb2_grpc.StreamStub(self._channel)
        self._ipaddress = IPAddress
        self._port = Port
        self._idle = '1'
        self._peer_responded = threading.Event()
        self._call_finished = threading.Event()
        self._consumer_future = None

    def _response_watcher(self, response_iterator: Iterator[code_pb2.heartcheck_response]) -> None:
        try:
            for response in response_iterator:
                # NOTE: All fields in Proto3 are optional. This is the recommended way
                # to check if a field is present or not, or to exam which one-of field is
                # fulfilled by this message.
                # 应该检测心跳连接连接到的服务器是否和注册的一致
                self._on_ipaddress(response.ipaddress)
                self._on_idle(response.idle)
        except Exception as e:
            self._peer_responded.set()
            raise

    def _on_ipaddress(self, ipaddress: str) -> None:
        if ipaddress != self._ipaddress:
            logging.info("IPAddress is not the same!")
            self._peer_responded.set()
            self._call_finished.set()
        

    def _on_idle(self, idle: str) -> None:
        if self._idle != idle:
            logging.info("Idle turns from [%s] to [%s]", self._idle, idle)
            self._idle = idle
            r=redis_operate.RedisJson()
            tmp=json.loads(r.getJsonByKey(self._ipaddress))
            tmp['Idle']=self._idle
            r.insertRedis(self._ipaddress, json.dumps(tmp))

    def call(self) -> None:
        request = code_pb2.heartcheck_request()
        request.message = 'R U ok?'
        response_iterator = self._stub.HeartCheck(iter((request,)))
        #不要在当前线程上使用response，而是生成一个使用线程。
        self._consumer_future = self._executor.submit(self._response_watcher, response_iterator)

    def wait_peer(self) -> bool:
        logging.info("Waiting for [%s] to connect ...", self._ipaddress)
        self._peer_responded.wait(timeout=None)
        if self._consumer_future.done():
            # If the future raises, forwards the exception here
            self._consumer_future.result()
            return False
        return True

    def del_redis(self) -> None:
        r=redis_operate.RedisJson()
        r.deleteRedis(self._ipaddress)

def process_heart_check(executor: ThreadPoolExecutor, channel: grpc.Channel, IPAddress: str, Port: str) -> None:
    heart_maker = HeartMaker(executor, channel, IPAddress, Port)
    heart_maker.call()
    if heart_maker.wait_peer():
        logging.info("Call finished!")
        heart_maker.del_redis()
    else:
        logging.info("Call failed!")
        heart_maker.del_redis()

#与已注册Actor节点建立心跳检测的函数
def Heart_Check(IPAddress, Port):
    time.sleep(3)
    print('与 %s 开始建立心跳检测.' %IPAddress)
    executor = ThreadPoolExecutor()
    with grpc.insecure_channel(IPAddress+':'+Port) as channel:
        future = executor.submit(process_heart_check, executor, channel, IPAddress, Port)
        future.result()

if __name__ == "__main__":
    Heart_Check(sys.argv[1], sys.argv[2])