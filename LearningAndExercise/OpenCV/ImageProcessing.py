import cv2
Img = cv2.imread(r"C:\Users\mdfar\Desktop\100DaysOfML\OpenCV\DSC00050.JPG",cv2.IMREAD_GRAYSCALE)
Img = cv2.resize(Img,(500,500))
cv2.imshow("Image",Img)
cv2.imshow("NewImage",cv2.Canny(Img,50,150))
cv2.waitKey(0)
cv2.destroyAllWindows()