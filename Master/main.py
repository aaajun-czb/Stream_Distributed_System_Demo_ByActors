import logging
import sys
import socket
import multiprocessing
import contextlib

import redis_operate
import register
import inquiry

_LOGGER = logging.getLogger(__name__)

@contextlib.contextmanager
def _reserve_port(port):
    """Find and reserve a port for all subprocesses to use."""
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    if sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT) == 0:
        raise RuntimeError("Failed to set SO_REUSEPORT.")
    sock.bind(('', port))
    try:
        yield sock.getsockname()[1]
    finally:
        sock.close()

if __name__ == "__main__":
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[PID %(process)d] %(message)s')
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)
    #每次重新启动Master清空数据库
    redis_operate.init()
    redis_operate.deleteAllRedisDB()
    #使用多进程开启服务
    workers = []
    with _reserve_port(10087) as port:
        bind_address = socket.gethostbyname('master')+':{}'.format(port)
        _LOGGER.info("Binding to '%s'", bind_address)
        # NOTE: It is imperative that the worker subprocesses be forked before any gRPC servers start up.
        #See https://github.com/grpc/grpc/issues/16001 for more details.
        worker = multiprocessing.Process(target=inquiry.Inquiry_Send,args=(bind_address,))
        worker.start()
        workers.append(worker)
    with _reserve_port(10086) as port:
        bind_address = socket.gethostbyname('master')+':{}'.format(port)
        _LOGGER.info("Binding to '%s'", bind_address)
        worker = multiprocessing.Process(target=register.Register_Receive,args=(bind_address,))
        worker.start()
        workers.append(worker)
    for worker in workers:
        worker.join()