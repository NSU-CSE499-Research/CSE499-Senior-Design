import cv2
Img = cv2.imread(r'C:\Users\mdfar\Desktop\100DaysOfML\OpenCV\DSC00022.JPG')
Img = cv2.resize(Img,(500,500))
gray = cv2.cvtColor(Img,cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

contours,heirarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
cv2.drawContours(Img,contours,-1,(0,255,0),3)
cv2.imshow("Contors",Img)
cv2.waitKey(0)
cv2.destroyAllWindows()