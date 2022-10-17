from concurrent import futures
import logging
import sys
import contextlib
import socket
import time

import grpc
import code_pb2
import code_pb2_grpc


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

def _wait_forever(server):
    try:
        while True:
            time.sleep(60*60*24)
    except KeyboardInterrupt:
        server.stop(None)

class Task(code_pb2_grpc.TaskServicer):
    def Frame_Transmission(self, request, context):
        return code_pb2.frame_trans_response(result='ok')

if __name__ == '__main__':
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[PID %(process)d] %(message)s')
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)
    with _reserve_port(10086) as port:
        bind_address = socket.gethostbyname(socket.gethostname())+':{}'.format(port)
        _LOGGER.info("Binding to '%s'", bind_address)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10,),options=(('grpc.so_reuseport', 1),))
        code_pb2_grpc.add_TaskServicer_to_server(Task(), server)
        server.add_insecure_port(bind_address)
        server.start()
        _wait_forever(server)