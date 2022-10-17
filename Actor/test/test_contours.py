import cv2

import code_pb2
import code_pb2_grpc

load_path='./images/test2.jpg'
mask = cv2.imread(load_path, cv2.IMREAD_GRAYSCALE)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5)) # 形态学kernel
erode = cv2.erode(mask, kernel) # 腐蚀，去掉图中小斑块
dilate = cv2.dilate(erode, kernel, iterations=3) # 膨胀，还原放大
close = cv2.morphologyEx(dilate, cv2.MORPH_CLOSE, kernel) # 闭操作，去掉物体内部的小方块
contours, hierarchy = cv2.findContours(close, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) # 根据二值图找轮廓
xywh=[]
for (i, c) in enumerate(contours):
    (x,y,w,h) = cv2.boundingRect(c)
    xywh.append(code_pb2.XYWH(x=x,y=y,w=w,h=h))
print(xywh)
# tuple里带不同size的ndarray，传输非常麻烦，一堆编解码最后还不知道size
# contours_list = []
# for i in contours:
#     contours_list.append(str(i.tobytes()))
# contours_json = json.dumps(contours_list)
# cnts = base64.b64encode(bytes(contours_json, encoding='utf8'))
# cnts_data = str(base64.b64decode(cnts), encoding='utf8')
# cnts_list = json.loads(cnts_data)
# for i in cnts_list:
#     i = np.frombuffer(bytes(i.encode()), np.uint8)
# cnts = tuple(cnts)
# print(cnts)