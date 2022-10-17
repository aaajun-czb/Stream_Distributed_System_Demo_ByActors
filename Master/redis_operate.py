import redis
import socket

host = socket.gethostbyname("redis") # redis服务地址
port = 6379  # redis服务端口

# class RedisJson(object):
#     def __init__(self):
#         self.host = host
#         self.port = port
#         self.pool = redis.ConnectionPool(host=self.host, port=self.port, password='123456', decode_responses=True)
#         self.r = redis.StrictRedis(connection_pool=self.pool)

#     #把json存入redis中
#     def insertRedis(self, keyName, jsonStr):
#         if self.r.exists(keyName):
#             self.r.delete(keyName)
#         self.r.lpush(keyName, jsonStr)

#     #删除redis中的某个key的键值对
#     def deleteRedis(self, keyName): 
#         self.r.delete(keyName)

#     #取得某个key的json
#     def getJsonByKey(self, keyName):
#         if self.r.exists(keyName):
#             return self.r.lrange(keyName, 0, self.r.llen(keyName))
#         return None

#     #取得所有的key，返回的是list
#     def getAllKeys(self):
#         return self.r.keys()

#     #删库跑路
#     def deleteAllRedisDB(self):
#         self.r.flushdb()

def init():
    global _global_REDIS
    _global_REDIS = redis.StrictRedis(host=host, port=port, password='123456', decode_responses=True)

def insertRedis(keyName, jsonStr):
    if _global_REDIS.exists(keyName):
        _global_REDIS.delete(keyName)
    _global_REDIS.lpush(keyName, jsonStr)

def deleteRedis(keyName): 
    _global_REDIS.delete(keyName)

def getJsonByKey(keyName):
    if _global_REDIS.exists(keyName):
        return _global_REDIS.lrange(keyName, 0, _global_REDIS.llen(keyName))
    return None

def getAllKeys():
    return _global_REDIS.keys()

def deleteAllRedisDB():
    _global_REDIS.flushdb()