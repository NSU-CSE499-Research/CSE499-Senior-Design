import cv2
Cam = cv2.VideoCapture(0)
H = int(Cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
W = int(Cam.get(cv2.CAP_PROP_FRAME_WIDTH))

codec = cv2.VideoWriter_fourcc(*'XVID')
record = cv2.VideoWriter("FVideo.avi",codec,20,(W,H))

while True:
    success , img = Cam.read()
    if not success:
        break
    record.write(img)
    cv2.imshow("Recording Live",img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Quiting....")
        break
Cam.release()
cv2.destroyAllWindows()