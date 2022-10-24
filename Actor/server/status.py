# -*- coding: utf-8 -*-
import socket
 
def init():  
    global _global_STATUS
    _global_STATUS = {}
    _global_STATUS['IPAddress']=socket.gethostbyname(socket.gethostname())
    _global_STATUS['Port']='10086'
    _global_STATUS['Name']=socket.gethostname()
    _global_STATUS['Idle']='1'
    _global_STATUS['Memory']='512M'
    _global_STATUS['CPU']='1'
 
 
def set_value(key, value):
    # 定义一个全局变量
    _global_STATUS[key] = value
 
 
def get_value(key):
    # 获得一个全局变量，不存在则提示读取对应变量失败
    try:
        return _global_STATUS[key]
    except:
        print('读取' + key + '失败\r\n')
 