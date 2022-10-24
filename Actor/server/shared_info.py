'''This py to store shared infomation'''

'''ThreadPool'''
from concurrent.futures import ThreadPoolExecutor

def thread_init():  
    global executor
    executor = ThreadPoolExecutor(max_workers=4)
 
def thread_submit(function):
    executor.submit(function)

'''Worker Nodes Info'''
def worker_info_init():  
    global _global_WORKERS_INFO
    _global_WORKERS_INFO = {}
 
def worker_info_get_value(key):
    try:
        return _global_WORKERS_INFO[key]
    except:
        print('读取' + key + '失败\r\n')

def save_object_detect_info(master, morphological_process, pre_process,
                            morphological_process_backup = None, 
                            pre_process_backup = None):
    _global_WORKERS_INFO['master'] = master
    _global_WORKERS_INFO['morphological_process'] = morphological_process
    _global_WORKERS_INFO['pre_process'] = pre_process
    _global_WORKERS_INFO['morphological_process_backup'] = morphological_process_backup
    _global_WORKERS_INFO['pre_process_backup'] = pre_process_backup