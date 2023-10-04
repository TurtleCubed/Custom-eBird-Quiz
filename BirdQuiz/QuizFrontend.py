from tkinter import *
from PIL import ImageTk, Image
from QuizBackend import QuizBackend
from species_validation import Validate
from ttkwidgets.autocomplete import AutocompleteEntryListbox
from pathlib import Path

# TODO impossible: birdie style
# TODO hard Case insensitive autofill?, zoom
# TODO easy: photo start/end screen, nice answer right or wrong, colors on words
# TODO doesn't count! bad photo.
# TODO add species validity verification

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
        self.name_validator = Validate()
        # Begin the quiz!
        self.show_intro()

    def show_intro(self):
        """Set various window parameters and show the intro screen where you can configure settings."""
        self.root.title("BirdQuiz")
        self.root.geometry('1280x720')
        self.label.configure(text = "Welcome to BirdQuiz! Press play to begin:")

        im = self.resize_to_tk(Image.open(Path("resources", "intro.jpg")))
        self.image = Label(self.root, image=im)
        self.image.photo = im

        self.label.grid(row = 0, column = 0, sticky = W, pady = 2)
        self.button.grid(row=0, column=1, sticky=W, pady=2)
        self.image.grid(row=1, column=0, columnspan=4, rowspan=2, padx=5, pady=5)

        self.set_backend()

        # List of species and input box for additional species
        inputbox = Text(self.root, width=30, height=1)
        inputbox.grid(row=1, column=4)
        listbox = Listbox(self.root, width=30, height=28, selectmode="multiple")
        listbox.grid(row=2, column=4, columnspan=3, padx=5, pady=5)
        listbox.insert(0, *self.backend.alpha_species)
        # Buttons to add/remove species
        addbutton = Button(self.root, width=1, height=1)
        addbutton.grid(row=1, column=5)
        addbutton.configure(text = '+', bd = '4', command=lambda i=inputbox, l=listbox: self.add_to_listbox(i, l))
        self.root.bind('<Return>', lambda i=inputbox, l=listbox: self.add_to_listbox(i, l))
        rmbutton = Button(self.root, width=1, height=1)
        rmbutton.grid(row=1, column=6)
        rmbutton.configure(text = '-', bd = '4', command = lambda: [listbox.delete(x) for x in reversed(listbox.curselection())])

        # Black and white checkbox
        self.bw_var = IntVar()
        bw_checkbox = Checkbutton(self.root, text="Black and White", variable=self.bw_var, onvalue=1, offvalue=0)
        bw_checkbox.grid(row=3, column=0)

        # Number of questions
        num_q_label = Label(self.root, text="Num Questions:")
        num_q_label.grid(row=0, column=2)
        self.num_q = Text(self.root, width=3, height=1)
        self.num_q.grid(row=0, column=3)
        self.num_q.insert("end", str(self.backend.questions))

        self.intro_widgets = [inputbox, listbox, addbutton, rmbutton, bw_checkbox, self.num_q, num_q_label]

        self.button.configure(text = 'Play', bd = '5', command = lambda : self.start_game(listbox.get(0, "end")))

        self.root.mainloop()

    def start_game(self, species):
        """Begin the game, by removing intro screen information and booting the backend."""
        self.backend.questions = int(self.num_q.get("1.0", "end").strip())
        if self.bw_var.get() == 1:
            self.backend.add_black_white()
        for w in self.intro_widgets:
            w.destroy()
        self.button.configure(text = "Loading...")
        self.backend.alpha_species = sorted(set(species))
        self.backend.begin_thread()

        self.button.grid_forget()
        self.label.configure(text = "Your Answer:")
        self.field.configure(width = 30, height=28, completevalues=self.backend.alpha_species)
        self.label.grid(row = 1, column = 1, sticky="ew")
        self.field.grid(row = 2, column = 1, sticky="ew")
        self.score.grid(row=0, column=1, sticky="ew")
        self.image.grid(row=0, column=0, columnspan=1, rowspan=3, padx=5, pady=5)
        self.mid_quiz = True
        self.next_question()

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
        self.image.photo = Image
        self.answer_text.grid_forget()
        self.label.grid(row=1, column=1, sticky="ew")
        self.field.grid(row = 2, column = 1, sticky = "ew")
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
        self.label.grid_forget()
        self.answer_text.grid(row = 1, column = 1, sticky="ew")
        
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

    
    def add_to_listbox(self, inputbox, listbox):
        """Moves text from the inputbox to the listbox with some text validation"""
        text = inputbox.get("1.0", "end").strip()
        if self.name_validator.validate(text):
            listbox.insert(0, text)
        else:
            print(text + " is an invalid species name")
        inputbox.delete("1.0", "end")


if __name__ == "__main__":
    a = QuizFrontend()
