import cv2

img = cv2.imread("Quizzes/2022-08-05-15-34/Black-footed Albatross12.jpg")
cv2.imshow("sample", img)

cv2.imshow("sample", img)
print(cv2.waitKey(0))

img = cv2.putText(img, 'Black-footed Albatross', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
cv2.imshow("sample", img)
print(cv2.waitKey(0))


