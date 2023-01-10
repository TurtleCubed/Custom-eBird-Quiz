import cv2

img = cv2.imread("Quizzes/2022-08-05-15-34/Black-footed Albatross12.jpg")
target_height = 500
height_factor = target_height / img.shape[0]
h_new = target_height
w_new = int(img.shape[1] * height_factor)
img = cv2.resize(img, (w_new, h_new))
cv2.imshow("sample", img)

cv2.imshow("sample", img)
print(cv2.waitKey(0))

img = cv2.putText(img, 'Black-footed Albatross', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
cv2.imshow("sample", img)
print(cv2.waitKey(0))


