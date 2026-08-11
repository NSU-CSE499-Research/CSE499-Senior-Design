import cv2
import os

path = input("Enter full image path: ")

if not os.path.exists(path):
    print("Path does not exist. Please check the file path.")
else:
    img = cv2.imread(path)
    img = cv2.resize(img,(400,500))
    cv2.imshow("Image",img)
    color = (200,0,0)

    a = input(f"1. For text\n2. For Line\n3. For Rectangle\n4. Square\n5. Circle")
    if a is 1:
        text = input("Enter text: ")
        (p1,p2) = input("Enter starting point ")
        cv2.imshow("Text",cv2.putText(img,text,(p1,p2),cv2.FONT_HERSHEY_SIMPLEX,1.2,2,color))
    cv2.waitKey(0)
    cv2.destroyAllWindows()