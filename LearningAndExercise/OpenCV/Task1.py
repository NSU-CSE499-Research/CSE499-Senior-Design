import cv2

img_path = r"C:\Users\mdfar\Desktop\100DaysOfML\OpenCV\Output.jpg"
img = cv2.imread(img_path)
img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
cv2.imshow("Task_1",img)
cv2.imshow("Edited",cv2.resize(img,(300,300)))
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite("Task_1.png",img)