import cv2
import os

cap = cv2.VideoCapture(0)
while True:
    Ret, Fream = cap.read()
    if not Ret:
        print("Coud Not Connect")
        break
    cv2.imshow("Video",Fream)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Quiting....")
        break

cap.release()
cv2.destroyAllWindow()