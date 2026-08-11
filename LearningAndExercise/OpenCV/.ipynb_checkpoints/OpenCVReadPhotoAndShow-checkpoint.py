import cv2

image_path = r"C:\Users\mdfar\Pictures\WhatsAppPic\WhatsApp Image 2026-06-21 at 9.49.04 PM.jpeg"

# print(os.path.exists(image_path))
image = cv2.imread(image_path)
cv2.imshow("My Image", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite('Output.jpg',image)
