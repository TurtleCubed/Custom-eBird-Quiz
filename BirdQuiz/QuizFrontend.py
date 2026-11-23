"""Tkinter interface for the browser-backed BirdQuiz."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk
from pathlib import Path
from queue import Empty
import webbrowser

from PIL import Image

from QuizBackend import MediaRecord, QuizBackend, QuizFetchError
from species_validation import Validate, normalize_name
from zoom import ZoomableImageCanvas


BASE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = BASE_DIR / "resources"


class AutocompleteInput(ttk.Frame):
    """Entry with case-insensitive taxonomy suggestions and keyboard selection."""

    def __init__(self, master, validator, values=None, on_choose=None,
                 on_return=None, entry_font=None, list_font=None):
        super().__init__(master)
        self.validator = validator
        self.values = values
        self.on_choose = on_choose
        self.on_return = on_return

        self.entry = ttk.Entry(self, font=entry_font)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        self.suggestions = tk.Listbox(
            self, height=6, exportselection=False, font=list_font,
            activestyle="dotbox",
        )
        self.suggestions.grid(row=1, column=0, sticky="ew")
        self.suggestions.grid_remove()

        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Down>", self._focus_suggestions)
        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Escape>", self._hide_suggestions)
        self.suggestions.bind("<ButtonRelease-1>", self._accept_click)
        self.suggestions.bind("<Return>", self._accept_return)
        self.suggestions.bind("<Escape>", self._return_to_entry)

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._hide_suggestions()

    def clear(self):
        self.entry.delete(0, tk.END)
        self._hide_suggestions()

    def focus_set(self):
        self.entry.focus_set()

    def _on_key_release(self, event):
        if event.keysym in {
            "Return", "Escape", "Up", "Down", "Left", "Right",
            "Shift_L", "Shift_R", "Control_L", "Control_R",
        }:
            return
        query = self.get().strip()
        if not query:
            self._hide_suggestions()
            return
        canonical = self.validator.canonicalize(query)
        if canonical and normalize_name(canonical) == normalize_name(query):
            self._hide_suggestions()
            return

        if self.values is None:
            options = self.validator.suggest(query, size=8)
        else:
            normalized_query = normalize_name(query)
            options = [
                value for value in self.values
                if normalize_name(value).startswith(normalized_query)
            ][:8]
        self.suggestions.delete(0, tk.END)
        for option in options:
            self.suggestions.insert(tk.END, option)
        if options:
            self.suggestions.grid()
        else:
            self._hide_suggestions()

    def _focus_suggestions(self, _event):
        if self.suggestions.winfo_ismapped() and self.suggestions.size():
            self.suggestions.selection_clear(0, tk.END)
            self.suggestions.selection_set(0)
            self.suggestions.activate(0)
            self.suggestions.focus_set()
            return "break"
        return None

    def _on_return(self, event):
        if self.suggestions.winfo_ismapped() and self.suggestions.size():
            selection = self.suggestions.curselection()
            self._accept_index(selection[0] if selection else 0)
            return "break"
        if self.on_return:
            return self.on_return(event) or "break"
        return "break"

    def _accept_click(self, _event):
        selection = self.suggestions.curselection()
        if selection:
            self._accept_index(selection[0])

    def _accept_return(self, _event):
        selection = self.suggestions.curselection()
        if selection:
            self._accept_index(selection[0])
        elif self.suggestions.size():
            self._accept_index(0)
        return "break"

    def _accept_index(self, index):
        value = self.suggestions.get(index)
        self.set(value)
        if self.on_choose:
            self.on_choose(value)

    def _return_to_entry(self, _event):
        self._hide_suggestions()
        self.entry.focus_set()
        return "break"

    def _hide_suggestions(self, _event=None):
        self.suggestions.grid_remove()
        return "break"


class ScrollableFrame(ttk.Frame):
    """A vertically scrollable content frame for long quiz summaries."""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.content = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.content.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_content)

    def _update_scrollregion(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)


class QuizFrontend:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("BirdQuiz")
        self.root.geometry("1250x820")
        self.root.minsize(850, 600)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.validator = Validate()
        self.backend = QuizBackend(taxonomy_records=self.validator.species_by_key)
        self.selected_species = []
        for name in self.backend.alpha_species:
            canonical = self.validator.canonicalize(name)
            if canonical and canonical not in self.selected_species:
                self.selected_species.append(canonical)

        self.questions_var = tk.StringVar(value=str(self.backend.questions))
        self.start_month_var = tk.StringVar(value="1")
        self.end_month_var = tk.StringVar(value="12")
        self.black_white_var = tk.BooleanVar(value=False)
        self.ui_font_size = 11
        self.ui_font = tkfont.Font(root=self.root, family="Segoe UI", size=self.ui_font_size)
        self.heading_font = tkfont.Font(
            root=self.root, family="Segoe UI", size=self.ui_font_size + 6, weight="bold"
        )
        self.style = ttk.Style(self.root)
        self._configure_styles()

        self.screen = None
        self.status_var = tk.StringVar()
        self.current_index = 0
        self.image_viewer = None
        self._loading_active = False
        self._quiz_started = False
        self._waiting_for_question = False
        self._build_intro()

    def run(self):
        self.root.mainloop()

    def _configure_styles(self):
        self.style.configure(".", font=self.ui_font)
        self.style.configure("TLabel", font=self.ui_font)
        self.style.configure("TButton", font=self.ui_font, padding=(7, 4))
        self.style.configure("TCheckbutton", font=self.ui_font)
        self.style.configure("TEntry", font=self.ui_font)
        self.style.configure("TSpinbox", font=self.ui_font)
        self.style.configure("Heading.TLabel", font=self.heading_font)
        self.style.configure("Feedback.TLabel", font=self.heading_font)

    def _change_font(self, amount):
        self.ui_font_size = min(24, max(8, self.ui_font_size + amount))
        self.ui_font.configure(size=self.ui_font_size)
        self.heading_font.configure(size=self.ui_font_size + 6)

    def _clear_screen(self):
        if self.screen is not None:
            self.screen.destroy()
        self.screen = ttk.Frame(self.root, padding=10)
        self.screen.grid(row=0, column=0, sticky="nsew")
        self.screen.rowconfigure(1, weight=1)
        self.screen.columnconfigure(0, weight=1)
        self.status_var.set("")

    def _make_image_panel(self, parent, initial_image=None):
        panel = ttk.Frame(parent)
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        canvas = ZoomableImageCanvas(panel)
        vertical = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        horizontal = ttk.Scrollbar(panel, orient="horizontal", command=canvas.xview)
        canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        tools = ttk.Frame(panel)
        tools.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(tools, text="−", width=4, command=canvas.zoom_out).pack(side="left")
        ttk.Button(tools, text="Reset zoom", command=canvas.reset_zoom).pack(side="left", padx=4)
        ttk.Button(tools, text="+", width=4, command=canvas.zoom_in).pack(side="left")
        ttk.Label(tools, text="Scroll to zoom · drag to pan · double-click to reset").pack(
            side="left", padx=8
        )
        if initial_image is not None:
            canvas.set_image(initial_image)
        return panel, canvas

    def _build_intro(self):
        self.root.unbind("<Return>")
        self._clear_screen()
        self.screen.rowconfigure(1, weight=1)
        header = ttk.Frame(self.screen)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="Welcome to BirdQuiz",
            style="Heading.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Choose a species list, then identify each randomly selected photo.",
        ).grid(row=1, column=0, sticky="w")

        controls = ttk.Frame(header)
        controls.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(controls, text="A−", width=4,
                   command=lambda: self._change_font(-1)).pack(side="left", padx=2)
        ttk.Button(controls, text="A+", width=4,
                   command=lambda: self._change_font(1)).pack(side="left", padx=2)

        panes = ttk.Panedwindow(self.screen, orient="horizontal")
        panes.grid(row=1, column=0, sticky="nsew")
        left = ttk.Frame(panes, padding=(0, 0, 5, 0))
        right = ttk.Frame(panes, padding=(8, 0, 0, 0))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        try:
            intro = Image.open(RESOURCE_DIR / "intro.jpg").convert("RGB")
        except OSError:
            intro = None
        image_panel, self.image_viewer = self._make_image_panel(left, intro)
        image_panel.grid(row=0, column=0, sticky="nsew")
        panes.add(left, weight=3)
        panes.add(right, weight=2)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)
        ttk.Label(right, text="Species to include", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            right, text="Type a name; matching is case-insensitive."
        ).grid(row=1, column=0, sticky="w", pady=(2, 5))

        self.intro_input = AutocompleteInput(
            right,
            self.validator,
            on_choose=self.add_species,
            on_return=lambda _event: self.add_species(self.intro_input.get()),
            entry_font=self.ui_font,
            list_font=self.ui_font,
        )
        self.intro_input.grid(row=2, column=0, sticky="ew")
        ttk.Button(
            right,
            text="Add species",
            command=lambda: self.add_species(self.intro_input.get()),
        ).grid(row=3, column=0, sticky="w", pady=5)

        list_frame = ttk.Frame(right)
        list_frame.grid(row=4, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.species_list = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            exportselection=False,
            font=self.ui_font,
            height=12,
        )
        species_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.species_list.yview
        )
        self.species_list.configure(yscrollcommand=species_scroll.set)
        self.species_list.grid(row=0, column=0, sticky="nsew")
        species_scroll.grid(row=0, column=1, sticky="ns")
        self._refresh_species_list()

        list_buttons = ttk.Frame(right)
        list_buttons.grid(row=5, column=0, sticky="ew", pady=(5, 0))
        ttk.Button(
            list_buttons,
            text="Remove selected",
            command=self.remove_selected_species,
        ).pack(side="left")
        self.intro_status = ttk.Label(
            right, textvariable=self.status_var, wraplength=420
        )
        self.intro_status.grid(row=6, column=0, sticky="ew", pady=(4, 0))

        settings = ttk.Frame(self.screen, padding=(0, 8, 0, 0))
        settings.grid(row=2, column=0, sticky="ew")
        ttk.Label(settings, text="Questions").pack(side="left")
        ttk.Spinbox(
            settings, from_=1, to=500, width=5, textvariable=self.questions_var
        ).pack(side="left", padx=(4, 12))
        ttk.Label(settings, text="Start month").pack(side="left")
        ttk.Spinbox(
            settings, from_=1, to=12, width=4, textvariable=self.start_month_var
        ).pack(side="left", padx=(4, 12))
        ttk.Label(settings, text="End month").pack(side="left")
        ttk.Spinbox(
            settings, from_=1, to=12, width=4, textvariable=self.end_month_var
        ).pack(side="left", padx=(4, 12))
        ttk.Checkbutton(
            settings, text="Black and white", variable=self.black_white_var
        ).pack(side="left", padx=6)
        ttk.Button(settings, text="Play", command=self.start_game).pack(
            side="right", padx=(8, 0)
        )
        ttk.Label(
            self.screen,
            textvariable=self.status_var,
            foreground="#9b1c1c",
        ).grid(row=3, column=0, sticky="w", pady=(4, 0))

    def _refresh_species_list(self):
        if not hasattr(self, "species_list"):
            return
        self.species_list.delete(0, tk.END)
        for name in self.selected_species:
            self.species_list.insert(tk.END, name)

    def add_species(self, typed_name):
        canonical = self.validator.canonicalize(typed_name)
        if canonical is None:
            self.status_var.set(
                f"“{typed_name.strip()}” is not in the local eBird taxonomy. Choose a suggestion."
            )
            return
        existing = {normalize_name(name) for name in self.selected_species}
        if normalize_name(canonical) in existing:
            self.status_var.set(f"{canonical} is already in the list.")
            self.intro_input.clear()
            return
        self.selected_species.append(canonical)
        self.selected_species.sort(key=str.casefold)
        self._refresh_species_list()
        self.intro_input.clear()
        self.status_var.set(f"Added {canonical}.")

    def remove_selected_species(self):
        selected = list(self.species_list.curselection())
        for index in reversed(selected):
            del self.selected_species[index]
        self._refresh_species_list()

    def start_game(self):
        species = []
        for name in self.selected_species:
            canonical = self.validator.canonicalize(name)
            if canonical and canonical not in species:
                species.append(canonical)
        if not species:
            self.status_var.set("Add at least one valid species before playing.")
            return
        try:
            questions = int(self.questions_var.get())
            start_month = int(self.start_month_var.get())
            end_month = int(self.end_month_var.get())
        except ValueError:
            self.status_var.set("Questions and months must be whole numbers.")
            return
        if questions < 1 or questions > 500:
            self.status_var.set("Choose between 1 and 500 questions.")
            return
        if not 1 <= start_month <= 12 or not 1 <= end_month <= 12:
            self.status_var.set("Months must be between 1 and 12.")
            return

        self.backend = QuizBackend(
            questions=questions,
            begin_month=start_month,
            end_month=end_month,
            taxonomy_records=self.validator.species_by_key,
        )
        self.backend.alpha_species = species
        if self.black_white_var.get():
            self.backend.add_black_white()
        try:
            self.backend.begin_thread()
        except QuizFetchError as exc:
            self.status_var.set(str(exc))
            return
        self._loading_active = True
        self._quiz_started = False
        self._waiting_for_question = False
        self._build_loading_screen()
        self.root.after(100, self._poll_backend)

    def _build_loading_screen(self):
        self.root.unbind("<Return>")
        self._clear_screen()
        ttk.Label(
            self.screen, text="Preparing your quiz…", style="Heading.TLabel"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.screen,
            text="Chrome will open for the Macaulay Library search. "
                 "If verification appears, complete it in that window.",
            wraplength=800,
        ).grid(row=1, column=0, sticky="w", pady=8)
        ttk.Label(
            self.screen, textvariable=self.status_var, wraplength=900
        ).grid(row=2, column=0, sticky="w")
        ttk.Button(
            self.screen, text="Cancel", command=self._cancel_loading
        ).grid(row=3, column=0, sticky="w", pady=10)

    def _cancel_loading(self):
        self._loading_active = False
        if self.backend:
            self.backend.cancel()
        self._build_intro()

    def _poll_backend(self):
        if not self.root.winfo_exists() or not self._loading_active:
            return
        while True:
            try:
                event, value = self.backend.status_queue.get_nowait()
            except Empty:
                break
            if event == "status":
                self.status_var.set(value)
            elif event == "error":
                self._loading_active = False
                if not self._quiz_started:
                    messagebox.showerror("Could not prepare quiz", value, parent=self.root)
                    self._build_intro()
                    return
                self.status_var.set(value)
            elif event == "question_ready":
                index = value
                if not self._quiz_started and index == 0:
                    self._quiz_started = True
                    self._build_quiz_screen()
                    self.show_question()
                elif (
                    self._quiz_started
                    and self._waiting_for_question
                    and index == self.current_index
                ):
                    self._waiting_for_question = False
                    self.show_question()
                self._refresh_continue_button()
            elif event == "complete":
                self._loading_active = False
                self._on_quiz_complete(value)
        self.root.after(150, self._poll_backend)

    def _on_quiz_complete(self, details):
        missing = details.get("missing_species", [])
        replacement_count = details.get("replacement_count", 0)
        status_parts = []
        if missing:
            status_parts.append(
                f"No photos for {', '.join(missing)}; "
                f"{replacement_count} question(s) use another selected species."
            )
        if details.get("warning"):
            status_parts.append(details["warning"])
        if not self._quiz_started:
            messagebox.showerror(
                "Could not prepare quiz",
                "The first photo could not be loaded.",
                parent=self.root,
            )
            self._build_intro()
        elif status_parts:
            self.status_var.set(" ".join(status_parts))

    def _build_quiz_screen(self):
        self._clear_screen()
        header = ttk.Frame(self.screen)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        self.question_counter = ttk.Label(
            header, text="", style="Heading.TLabel"
        )
        self.question_counter.grid(row=0, column=0, sticky="w")
        self.score_label = ttk.Label(header, text="")
        self.score_label.grid(row=0, column=1, sticky="e", padx=8)
        font_controls = ttk.Frame(header)
        font_controls.grid(row=0, column=2, sticky="e")
        ttk.Button(font_controls, text="A−", width=4,
                   command=lambda: self._change_font(-1)).pack(side="left", padx=2)
        ttk.Button(font_controls, text="A+", width=4,
                   command=lambda: self._change_font(1)).pack(side="left", padx=2)

        panes = ttk.Panedwindow(self.screen, orient="horizontal")
        panes.grid(row=1, column=0, sticky="nsew")
        image_frame = ttk.Frame(panes)
        answer_frame = ttk.Frame(panes, padding=12)
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        image_panel, self.image_viewer = self._make_image_panel(image_frame)
        image_panel.grid(row=0, column=0, sticky="nsew")
        panes.add(image_frame, weight=3)
        panes.add(answer_frame, weight=2)

        answer_frame.columnconfigure(0, weight=1)
        self.prompt_label = ttk.Label(
            answer_frame, text="Your answer", style="Heading.TLabel"
        )
        self.prompt_label.grid(row=0, column=0, sticky="w")
        self.answer_input = AutocompleteInput(
            answer_frame,
            self.validator,
            on_return=self.submit_answer,
            entry_font=self.ui_font,
            list_font=self.ui_font,
        )
        self.answer_input.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        actions = ttk.Frame(answer_frame)
        actions.grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Button(actions, text="Submit", command=self.submit_answer).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(
            actions, text="Skip and reveal", command=self.skip_question
        ).pack(side="left")

        self.feedback_label = ttk.Label(
            answer_frame, text="", style="Feedback.TLabel", wraplength=420
        )
        self.feedback_label.grid(row=3, column=0, sticky="w", pady=(12, 5))
        self.credit_label = ttk.Label(answer_frame, text="", wraplength=420)
        self.credit_label.grid(row=4, column=0, sticky="w")
        self.view_photo_button = ttk.Button(
            answer_frame, text="View photo in Macaulay Library",
            command=self.open_current_photo,
        )
        self.view_photo_button.grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.continue_button = ttk.Button(
            answer_frame, text="Continue", command=self.continue_quiz
        )
        self.continue_button.grid(row=6, column=0, sticky="w", pady=(12, 0))
        self.exclude_button = ttk.Button(
            answer_frame, text="Don't count this question",
            command=self.exclude_question,
        )
        self.exclude_button.grid(row=7, column=0, sticky="w", pady=(5, 0))
        self.exclude_button.grid_remove()
        self.feedback_label.grid_remove()
        self.credit_label.grid_remove()
        self.view_photo_button.grid_remove()
        self.continue_button.grid_remove()

        self.quiz_status = ttk.Label(
            self.screen, textvariable=self.status_var, wraplength=1000
        )
        self.quiz_status.grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _update_score(self):
        self.score_label.configure(
            text=f"Score {self.backend.correct}/{self.backend.counted_questions}"
                 f" · {self.backend.uncounted_questions} not counted"
        )

    def show_question(self):
        self.root.unbind("<Return>")
        self._waiting_for_question = False
        index = self.current_index
        self.backend.i = index
        self.question_counter.configure(
            text=f"Question {index + 1} of {self.backend.questions}"
        )
        self._update_score()
        self.status_var.set("")
        self.feedback_label.grid_remove()
        self.credit_label.grid_remove()
        self.view_photo_button.grid_remove()
        self.continue_button.grid_remove()
        self.exclude_button.grid_remove()
        self.answer_input.grid()
        self.answer_input.clear()
        self.prompt_label.configure(text="Your answer")
        image = self.backend.get_current()
        if image is None:
            self.status_var.set("This question has no image. You can skip it.")
        self.image_viewer.set_image(image)
        self.answer_input.focus_set()

    def _show_waiting_question(self):
        self.root.unbind("<Return>")
        self._waiting_for_question = True
        self.backend.i = self.current_index
        self.question_counter.configure(
            text=f"Question {self.current_index + 1} of {self.backend.questions}"
        )
        self._update_score()
        self.image_viewer.set_image(None)
        self.answer_input.grid_remove()
        self.prompt_label.configure(text="Loading photo")
        self.feedback_label.configure(text="Searching for this species in the background…")
        self.feedback_label.grid()
        self.credit_label.grid_remove()
        self.view_photo_button.grid_remove()
        self.continue_button.grid_remove()
        self.exclude_button.grid_remove()
        self.status_var.set("")

    def _refresh_continue_button(self):
        if not self._quiz_started or not hasattr(self, "continue_button"):
            return
        if self.current_index + 1 >= self.backend.questions:
            self.continue_button.configure(text="See results", state="normal")
            return
        next_index = self.current_index + 1
        if self.backend.media_records[next_index] is None:
            self.continue_button.configure(
                text="Loading next photo…", state="disabled"
            )
        else:
            self.continue_button.configure(text="Continue", state="normal")

    def submit_answer(self, _event=None):
        answer = self.answer_input.get().strip()
        if not answer:
            self.status_var.set("Enter an answer or use Skip and reveal.")
            self.answer_input.focus_set()
            return "break"
        correct = self.backend.check(answer)
        actual = self.backend.get_species()
        if correct:
            self.feedback_label.configure(text=f"{actual} is correct.")
            self.exclude_button.grid_remove()
        else:
            self.feedback_label.configure(
                text=f"Your answer: {answer}\nThis photo shows: {actual}"
            )
            self.exclude_button.grid()
        self._show_reveal()
        return "break"

    def skip_question(self):
        self.backend.skip_current()
        self.feedback_label.configure(
            text=f"Skipped — this question does not count.\n"
                 f"The photo shows: {self.backend.get_species()}"
        )
        self.exclude_button.grid_remove()
        self._show_reveal()

    def _show_reveal(self):
        self.root.bind("<Return>", lambda _event: self.continue_quiz())
        self.answer_input.grid_remove()
        self.prompt_label.configure(text="Answer")
        self.feedback_label.grid()
        record = self.backend.get_current_media()
        credit_parts = []
        if record and record.contributor:
            credit_parts.append(f"Photo by {record.contributor}")
        if record and record.catalog_number:
            credit_parts.append(record.catalog_number)
        if credit_parts:
            credit_parts.append("Macaulay Library")
            self.credit_label.configure(text=" · ".join(credit_parts))
            self.credit_label.grid()
        else:
            self.credit_label.grid_remove()
        self.view_photo_button.configure(
            state=("normal" if record and record.page_url else "disabled")
        )
        self.view_photo_button.grid()
        self.continue_button.grid()
        self._update_score()
        self._refresh_continue_button()

    def exclude_question(self):
        self.backend.exclude_current()
        self.feedback_label.configure(
            text=f"This question will not count.\n"
                 f"The photo shows: {self.backend.get_species()}"
        )
        self.exclude_button.grid_remove()
        self._update_score()

    def open_current_photo(self):
        record = self.backend.get_current_media()
        if record and record.page_url:
            webbrowser.open_new_tab(record.page_url)

    def continue_quiz(self):
        if self.current_index + 1 >= self.backend.questions:
            self.show_end_screen()
            return
        self.current_index += 1
        self.backend.i = self.current_index
        if self.backend.media_records[self.current_index] is None:
            self._show_waiting_question()
        else:
            self.show_question()

    def show_end_screen(self):
        self.root.unbind("<Return>")
        self._clear_screen()
        self.screen.rowconfigure(2, weight=1)
        ttk.Label(self.screen, text="Quiz results", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        skipped = sum(outcome == "skipped" for outcome in self.backend.outcomes)
        excluded = sum(outcome == "excluded" for outcome in self.backend.outcomes)
        summary = (
            f"Score: {self.backend.correct}/{self.backend.counted_questions}"
            f"   ·   Skipped: {skipped}"
            f"   ·   Not counted: {excluded}"
        )
        ttk.Label(self.screen, text=summary).grid(
            row=1, column=0, sticky="w", pady=(3, 8)
        )

        results = ScrollableFrame(self.screen)
        results.grid(row=2, column=0, sticky="nsew")
        results.content.columnconfigure(1, weight=1)
        for column, title in enumerate(
            ("#", "Your answer", "Actual species", "Result", "Photo")
        ):
            ttk.Label(
                results.content, text=title, style="Heading.TLabel"
            ).grid(row=0, column=column, sticky="w", padx=5, pady=4)

        for index, (guess, actual, outcome, record) in enumerate(zip(
            self.backend.guesses,
            self.backend.species,
            self.backend.outcomes,
            self.backend.media_records,
        ), start=1):
            row = ttk.Frame(results.content, padding=(2, 4))
            row.grid(row=index, column=0, columnspan=5, sticky="ew")
            row.columnconfigure(2, weight=1)
            ttk.Label(row, text=str(index)).grid(row=0, column=0, sticky="w", padx=5)
            ttk.Label(row, text=guess or "—", wraplength=220).grid(
                row=0, column=1, sticky="w", padx=5
            )
            ttk.Label(row, text=actual, wraplength=260).grid(
                row=0, column=2, sticky="w", padx=5
            )
            status = {
                "correct": "Correct",
                "wrong": "Wrong",
                "skipped": "Skipped",
                "excluded": "Not counted",
            }.get(outcome, "—")
            ttk.Label(row, text=status).grid(row=0, column=3, sticky="w", padx=5)
            link = ttk.Button(
                row,
                text=(record.catalog_number or "Open photo"),
                command=lambda media=record: self._open_media(media),
                state=("normal" if record and record.page_url else "disabled"),
            )
            link.grid(row=0, column=4, sticky="w", padx=5)
            credit = ""
            if record:
                if record.contributor:
                    credit = f"Photo by {record.contributor}"
                if record.catalog_number:
                    credit = (credit + " · " if credit else "") + record.catalog_number
            if credit:
                ttk.Label(
                    row, text=f"{credit} · Macaulay Library",
                ).grid(row=1, column=1, columnspan=4, sticky="w", padx=5)

        buttons = ttk.Frame(self.screen)
        buttons.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Play again", command=self._play_again).pack(side="left")
        ttk.Button(buttons, text="Close", command=self.root.destroy).pack(side="right")

    @staticmethod
    def _open_media(record: MediaRecord | None):
        if record and record.page_url:
            webbrowser.open_new_tab(record.page_url)

    def _play_again(self):
        previous = self.backend
        self.backend = QuizBackend(
            taxonomy_records=self.validator.species_by_key
        )
        self.backend.alpha_species = list(self.selected_species)
        self.questions_var.set(str(previous.questions))
        self.black_white_var.set(previous._transform_black_white)
        self._build_intro()


if __name__ == "__main__":
    QuizFrontend().run()
