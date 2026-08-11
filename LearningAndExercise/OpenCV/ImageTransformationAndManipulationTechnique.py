import cv2
Path =  r"C:\Users\mdfar\Desktop\100DaysOfML\OpenCV\Output.jpg"
Img = cv2.imread(Path)
cv2.imshow("RAW",Img)
cv2.imshow("Edit",cv2.resize(Img,(150,300)))
cv2.imshow("Crop",Img[100:500,200:600])
(h,w) = Img.shape[:2]
center = (w//2,h//2)
M = cv2.getRotationMatrix2D(center,45,0.1)
cv2.imshow("Rotate",cv2.warpAffine(Img,M,(w,h)))
Img1 = cv2.resize(Img,(150,300))
cv2.imshow("Vertical",cv2.flip(Img1,0))
cv2.imshow("Horizontal",cv2.flip(Img1,1))
cv2.imshow("Both",cv2.flip(Img1,-1))
cv2.waitKey(0)
cv2.destroyAllWindows()