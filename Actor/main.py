from concurrent import futures
import logging
import sys
import contextlib
import socket
import time

import grpc
import code_pb2
import code_pb2_grpc

import register
import heart
import mailbox
import status

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

if __name__ == '__main__':
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[PID %(process)d] %(message)s')
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)
    status.init()
    if register.Register_Send() == 'ok':
        with _reserve_port(10086) as port:
            status.set_value('Port', port)
            bind_address = socket.gethostbyname(socket.gethostname())+':{}'.format(port)
            _LOGGER.info("Binding to '%s'", bind_address)
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10,),options=(('grpc.so_reuseport', 1),))
            code_pb2_grpc.add_StreamServicer_to_server(heart.Heart(), server)
            code_pb2_grpc.add_TaskServicer_to_server(mailbox.Task(), server)
            server.add_insecure_port(bind_address)
            server.start()
            _wait_forever(server)
        # with ProcessPoolExecutor(max_workers=3) as executor:
        #     futures = {}
        #     with _reserve_port(10086) as port:
        #         status.set_value('MailboxPort', port)
        #         bind_address = socket.gethostbyname(socket.gethostname())+':{}'.format(port)
        #         _LOGGER.info("Binding to '%s'", bind_address)
        #         mailbox = executor.submit(mailbox.Mailbox, bind_address)
        #         futures[mailbox] = 'mailbox'
        #     with _reserve_port(10087) as port:
        #         status.set_value('HeartPort', port)
        #         bind_address = socket.gethostbyname(socket.gethostname())+':{}'.format(port)
        #         _LOGGER.info("Binding to '%s'", bind_address)
        #         heart = executor.submit(heart.Heart_Check, bind_address)
        #         futures[heart] = 'heart'
        #     with _reserve_port(10088) as port:
        #         status.set_value('TaskPort', port)
        #         bind_address = socket.gethostbyname(socket.gethostname())+':{}'.format(port)
        #         _LOGGER.info("Binding to '%s'", bind_address)
        #         task = executor.submit(task.Task, bind_address)
        #         futures[task] = 'task'
        #     for f in as_completed(futures):
        #         try:
        #             print('the server %s is done.' %futures[f])
        #         except Exception as e:
        #             print(e)
    else:
        print('Fall!')