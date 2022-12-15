import cv2
import random
import os


class QuizFromFile():

    def __init__(self):
        title = "Custom eBird Quiz"
        # Count the number of species in the folder

        # Get species list from folder names in Photo Library
        species = os.listdir("PhotoLibrary")
        print(species)

        random_subset = random.sample(species, 20)
        for i in range(len(random_subset)):
            print(str(i) + ": " + random_subset[i])

        quiz_length = 20
        # Grab species list
        if not os.path.isfile("species.txt"):
            raise FileNotFoundError("no species.txt file found")
        f = open("species.txt")
        species_list = f.readlines()
        for i in range(len(species_list)):
            species_list[i] = species_list[i][:-1]

        # Figure out how many images of each species needs to be pulled
        list_length = int(quiz_length / len(species_list))
        length_dict = {}
        for species in species_list:
            length_dict[species] = list_length
        for species in random.sample(species_list, quiz_length % len(species_list)):
            length_dict[species] += 1

        # Generate lists of indexes of images to pull
        index_dict = {}
        for species in length_dict:
            index_dict[species] = random.sample(range(1, 31), length_dict[species])

        # Show quiz opening
        img_height = 720
        img = cv2.imread("PhotoLibrary\\Laysan Albatross\\17.jpg")
        # Resize Image
        img = self.scale_height(img, img_height)
        img = cv2.putText(img, 'Press any key to get started or press Esc to exit',
                          (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
        cv2.imshow(title, img)
        keypress = cv2.waitKey(0)

        num_correct = 0
        question_number = 0
        for species in random_subset:
            if keypress == 27:
                break
            # Grab the next photo
            random_int = random.randint(1, 30)
            img = cv2.imread("PhotoLibrary\\" + species + "\\" + str(random_int) + ".jpg")
            img = self.scale_height(img, img_height)
            img = cv2.putText(img, str(num_correct) + "/" + str(question_number),
                              (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            img = cv2.putText(img, "Press any key to reveal the bird",
                              (5, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(title, img)
            keypress = cv2.waitKey(0)
            if keypress == 27:
                break

            # Clear text and reveal
            img = cv2.imread("PhotoLibrary\\" + species + "\\" + str(random_int) + ".jpg")
            img = self.scale_height(img, img_height)
            img = cv2.putText(img, str(num_correct) + "/" + str(question_number),
                              (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            img = cv2.putText(img, species, (5, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
            img = cv2.putText(img, "Press enter if you guessed correctly",
                              (5, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(title, img)
            keypress = cv2.waitKey(0)
            if keypress == 13:
                num_correct += 1
            question_number += 1



    def scale_height(self, image, target_height):
        height_factor = target_height / image.shape[0]
        h_new = target_height
        w_new = int(image.shape[1] * height_factor)
        image = cv2.resize(image, (w_new, h_new))
        return image

if __name__ == "__main__":
    a = QuizFromFile()
