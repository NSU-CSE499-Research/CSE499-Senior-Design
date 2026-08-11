import cv2

Img = cv2.imread(r"C:\Users\mdfar\Pictures\WhatsAppPic\IMG_20260623_113024446.jpg.jpeg")
Img = cv2.resize(Img,(500,700))
cv2.imshow("Image",Img)
# print(Img.shape)
p1 = (100,200)
p2 = (300,300)
color = (200,0,0)
thickness = 6
# cv2.imshow("Line",cv2.line(Img,p1,p2,color,thickness))
# cv2.imshow("Rectangle",cv2.rectangle(Img,p1,p2,color,thickness))
# cv2.imshow("Circle",cv2.circle(Img,(250,350),150,color,-1))
# cv2.imshow("Square",cv2.rectangle(Img,(200,200),(400,400),color,thickness))
cv2.imshow("Text",cv2.putText(Img,"I love Mukta",(10,20),cv2.FONT_HERSHEY_SIMPLEX,1.2,2,color))
cv2.waitKey(0)
cv2.destroyAllWindows()