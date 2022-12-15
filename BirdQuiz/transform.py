import cv2
import numpy as np

def flyout(img, factor=0.98):
    cv2.namedWindow("birdmove", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("birdmove", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    frame = np.zeros(img.shape, np.uint8)
    while img.shape[0] * img.shape[1] > 100:
        frame.fill(0)
        img = cv2.resize(img, (int(img.shape[1] * factor), int(img.shape[0] * factor)), interpolation=cv2.INTER_CUBIC)
        frame += np.pad(img, ((frame.shape[0] - img.shape[0], 0), (frame.shape[1] - img.shape[1], 0), (0, 0)), mode="constant")
        cv2.imshow('birdmove', frame)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            break

#im = cv2.imread("./Quizzes/2022-08-09-17-18/Arctic Tern12.jpg")
#print(im.shape)
#print(np.pad(im, ((2000 - im.shape[0], 0), (2000 - im.shape[1], 0), (0, 0)), mode="constant").shape)
flyout(cv2.imread("./Quizzes/2022-08-09-17-18/Arctic Tern12.jpg"))