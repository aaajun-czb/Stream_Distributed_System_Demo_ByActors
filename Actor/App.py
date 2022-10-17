import logging
import json
import socket
import cv2
import base64

import grpc
import code_pb2
import code_pb2_grpc

import status

#询问注册的Actor节点函数
def Inquiry():
    with grpc.insecure_channel(socket.gethostbyname("master")+':10087', options=[
        ('grpc.max_send_message_length', 256 * 1024 * 1024),
        ('grpc.max_receive_message_length', 256 * 1024 * 1024),
    ]) as channel:
        client = code_pb2_grpc.StreamStub(channel)
        response = client.Inquiry(code_pb2.inquiry_request(message="Please give me register nodes!"))  # 返回结果是一个迭代器
        with open('Nodes.json', 'wb') as f:
            for i in response:
                f.write(i.data)
        print('接收完成')

#轮询占据Actor节点
def Nodes_Occupy() -> list:
    with open('Nodes.json','rb') as f:
        actor_nodes = json.load(f)
    #先轮询询问是否Idle，之后再改成多线程请求并行性
    idle_nodes=[]
    for node in actor_nodes:
        with grpc.insecure_channel(node['IPAddress']+':'+node['Port']) as channel:
            client = code_pb2_grpc.TaskStub(channel)
            try:
                response = client.IdleAsk(code_pb2.idleask_request(message='Are U Idle?')) 
                if response.message=='ok':
                    print('Nodes Occupy '+node['IPAddress']+'is ok')
                    idle_nodes.append(node)
            except grpc.RpcError as e:
                print(node['IPAddress']+':'+e.details())
    return idle_nodes

def Design_Roles_Nodes(idle_nodes) -> dict:
    worker_nodes = {}
    nodes_count = 0
    selected_nodes = []
    for node in idle_nodes:
        if(node['IPAddress'] != socket.gethostbyname(socket.gethostname())):
            nodes_count += 1
            node['CPU'] = float(node['CPU'])
            selected_nodes.append(node)
        if(nodes_count == 4):
            break
    if(nodes_count < 2):
        return None
    selected_nodes = sorted(selected_nodes,key = lambda e:e.__getitem__('CPU'), reverse = True)
    if(nodes_count == 2):
        worker_nodes['morphological_process'] = selected_nodes[0]['IPAddress']+':'+selected_nodes[0]['Port']
        worker_nodes['pre_process'] = selected_nodes[1]['IPAddress']+':'+selected_nodes[1]['Port']
    elif(nodes_count == 3):
        worker_nodes['morphological_process'] = selected_nodes[0]['IPAddress']+':'+selected_nodes[0]['Port']
        worker_nodes['morphological_process_backup'] = selected_nodes[1]['IPAddress']+':'+selected_nodes[1]['Port']
        worker_nodes['pre_process'] = selected_nodes[2]['IPAddress']+':'+selected_nodes[2]['Port']
    elif(nodes_count == 4):
        worker_nodes['morphological_process'] = selected_nodes[0]['IPAddress']+':'+selected_nodes[0]['Port']
        worker_nodes['morphological_process_backup'] = selected_nodes[1]['IPAddress']+':'+selected_nodes[1]['Port']
        worker_nodes['pre_process'] = selected_nodes[2]['IPAddress']+':'+selected_nodes[2]['Port']
        worker_nodes['pre_process_backup'] = selected_nodes[3]['IPAddress']+':'+selected_nodes[3]['Port']
    worker_nodes['master'] = socket.gethostbyname(socket.gethostname())+':10086'
    return worker_nodes


def send_frame_stream(cap):
    count=0
    while True:
        ret, frame = cap.read()
        if(ret == True):
            save_path='./images/test'+str(count)+'.jpg'
            cv2.imwrite(save_path, frame)
            with open(save_path, 'rb') as f:
                content = f.read()
            content = str(base64.b64encode(content), encoding='utf8')
            count +=1
            yield code_pb2.frame_trans_request(image=content)
        else:
            break

def Video_Transmission(path, worker_nodes) -> None:
    cap = cv2.VideoCapture(path)
    with grpc.insecure_channel(worker_nodes['pre_process']) as channel:
        client = code_pb2_grpc.TaskStub(channel)
        try:
            response = client.FrameTransmission(send_frame_stream(cap))
            print('Video Transmission :'+response.result)
        except grpc.RpcError as e:
            print('Video Transmission '+worker_nodes['pre_process']+':'+e.details())
    cap.release()

# My Task
def Object_Detect(idle_nodes) -> None:
    '''I should design the roles of workers here '''
    worker_nodes = Design_Roles_Nodes(idle_nodes)
    '''I should connect and tell nodes info to let them connect mutually here'''
    if worker_nodes == None:
        print('Do not have enough nodes!')
        return
    for node_address in worker_nodes.values():
        with grpc.insecure_channel(node_address) as channel:
            client = code_pb2_grpc.TaskStub(channel)
            try:
                response = client.WorkerNodesInfo(code_pb2.worker_nodes_info_request(worker_nodes_info=worker_nodes)) 
                if response.result=='ok':
                    print('Nodes Info '+node_address+'is ok')
            except grpc.RpcError as e:
                print(node_address+':'+e.details())
    '''I should push video data frame by frame here to simulate real-time here'''
    Video_Transmission('test.avi', worker_nodes)

if __name__ == '__main__':
    logging.basicConfig()
    Inquiry()
    Object_Detect(Nodes_Occupy())