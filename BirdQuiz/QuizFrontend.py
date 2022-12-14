from tkinter import *
from PIL import ImageTk, Image
from QuizBackend import QuizBackend
from ttkwidgets.autocomplete import AutocompleteEntryListbox

# TODO impossible: birdie style
# TODO hard Case insensitive autofill?, zoom
# TODO easy: photo start/end screen, nice answer right or wrong, colors on words

class QuizFrontend:
    def __init__(self):
        """Initialize the quiz frontend with windows and labels, then begin the quiz."""
        # create root window
        self.root = Tk()
        self.backend = None
        # Generate labels to be reused
        self.answer_text = Label(self.root)
        self.score = Label(self.root)
        self.label = Label(self.root)
        self.image = Label(self.root)
        self.field = AutocompleteEntryListbox(self.root)
        self.button = Button(self.root)
        # Variable stating whether the quiz has begun
        self.mid_quiz = False
        # Being the quiz!
        self.show_intro()

    def show_intro(self):
        """Set various window parameters and show the intro screen, 
        and begin looking up bird images in the background."""
        self.root.title("BirdQuiz")
        self.root.geometry('1280x720')
        self.label.configure(text = "Welcome to BirdQuiz! Press play to begin:")
        self.button.configure(text = 'Play', bd = '5', command = self.next_question)

        im = self.resize_to_tk(Image.open("./resources/intro.jpg"))
        self.image = Label(self.root, image=im)
        self.image.photo = im

        self.label.grid(row = 0, column = 0, sticky = W, pady = 2)
        self.button.grid(row=0, column=1, sticky=W, pady=2)
        self.image.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.root.after(1, self.set_backend())
        self.root.mainloop()

    def set_backend(self):
        """Called lazily"""
        self.backend = QuizBackend()

    def get_tkimg(self):
        """Return the current species image which has been reformatted."""
        return self.resize_to_tk(self.backend.get_current())

    def resize_to_tk(self, im):
        """Reformat, resize, and return image."""
        w, h = im.size
        return ImageTk.PhotoImage(image=im.resize((int(w * (480 / h)), 480)))

    def next_question(self, img=None):
        """Go to next question. If we just came from the intro screen, 
        set everything up. Otherwise just change existing variables."""
        if img is None:
            img = self.get_tkimg()
        self.image.configure(image=img)
        self.image.photo = img
        if not self.mid_quiz:
            self.button.grid_forget()
            self.label.configure(text = "Your Answer:")
            self.field.configure(width = 30, completevalues=self.backend.alpha_species)
            self.label.grid(row = 0, column = 0, sticky = W, pady = 2)
            self.field.grid(row = 0, column = 1, sticky = W, pady = 2)
            self.score.grid(row=0, column=2, sticky = W, pady = 2)
            self.image.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
            self.mid_quiz = True
        else:
            self.answer_text.grid_forget()
            self.field.grid(row = 0, column = 1, sticky = W, pady = 2)
            self.score.configure(text="{}/{}".format(self.backend.correct, self.backend.i))
        self.root.bind('<Return>', lambda x: self.submit())
        self.root.mainloop()

    def submit(self):
        """After submitting an answer:
        Check if the answer is correct, and display based on that.
        Then either go to end screen or next question.
        """
        # Check the answer
        correct = self.backend.check(self.field.get())
        self.field.grid_forget()

        # Show if correct or not
        if correct:
            self.answer_text.configure(text="{} is correct!".format(self.field.get()))
        else:
            self.answer_text.configure(text="{} is wrong, it's actually {}!".format(self.field.get(), self.backend.get_species()))
        self.score.configure(text="{}/{}, Enter to continue.".format(self.backend.correct, self.backend.i + 1))
        self.answer_text.grid(row = 0, column = 1, sticky = W, pady = 2)
        
        # Reset for next question
        if self.backend.i + 1 < self.backend.questions:
            self.root.bind('<Return>', lambda x: self.next_question())
        else:
            self.root.bind('<Return>', lambda x: self.end())
        self.field.entry.delete(0, END)        
        self.backend.next_species()
        self.root.mainloop()

    def end(self):
        """End screen. Show final score, guesses and correct.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
        Label(self.root, text="Your Score: {}/{}".format(self.backend.correct, self.backend.i)).grid(row=0, column=0)
        Label(self.root, text="Your Guess").grid(row=1, column=0)
        Label(self.root, text="Actual Species").grid(row=1, column=1)
        Label(self.root, text="Actual Species").grid(row=1, column=1)

        for i in range(len(self.backend.guesses)):
            Label(self.root, text=self.backend.guesses[i]).grid(row=i+2, column=0)
            Label(self.root, text=self.backend.species[i]).grid(row=i+2, column=1)

        im = self.resize_to_tk(Image.open("./resources/outro.jpg"))
        out_im = Label(self.root)
        out_im.configure(image=im)
        out_im.photo = im
        out_im.grid(row=0, column=2, rowspan=len(self.backend.guesses)+3, padx=5, pady=5)
        self.root.bind('<Return>', lambda x: self.root.destroy())    
        self.root.mainloop()

    

    

    

a = QuizFrontend()