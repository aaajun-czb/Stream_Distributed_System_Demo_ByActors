import cv2

cap = cv2.VideoCapture('test.avi')
fps = cap.get(cv2.CAP_PROP_FPS)
sizes = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
four_cc = cv2.VideoWriter_fourcc(*"MJPG")
video_writer = cv2.VideoWriter('output.avi', four_cc, fps, sizes)
frame_count=0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    print('frame_count: '+str(frame_count))
    frame_count += 1
    video_writer.write(frame)
video_writer.release()