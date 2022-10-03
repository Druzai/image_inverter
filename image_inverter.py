import os
import sys
import tkinter as tk
from contextlib import suppress
from datetime import datetime
from os import path
from pathlib import Path
from tkinter import ttk, Canvas, filedialog
from tkinter.constants import CENTER, HORIZONTAL, VERTICAL, BOTH, RIGHT, BOTTOM, X, Y, N, S
from typing import Optional

from PIL import Image, ImageTk, UnidentifiedImageError, ImageGrab
from tkinterdnd2 import DND_FILES, TkinterDnD

from config import Config, save_to_yaml, read_from_yaml
from logic import invert_image_with_blend, to_clipboard

VERSION = "0.1"


class App(ttk.Frame):
    def convert_placeholder_image_to_theme(self):
        if self.original_placeholder_image is None:
            self.original_placeholder_image = placeholder_image = Image.open("clipboard_placeholder.png")
        else:
            placeholder_image = self.original_placeholder_image
        if Config.config.theme == "dark":
            placeholder_image = invert_image_with_blend(placeholder_image, 85)
        return placeholder_image

    def set_placeholder_image(self):
        if self.original_image is None:
            self.placeholder_image = ImageTk.PhotoImage(self.convert_placeholder_image_to_theme())
            self.canvas.delete("img")
            self.canvas.create_image((200, 150), anchor=CENTER, image=self.placeholder_image, tag="img")

    def __init__(self, parent: tk.Tk):
        ttk.Frame.__init__(self)
        self.parent = parent
        self.help_window: Optional[tk.Toplevel] = None

        self.original_image_name: Optional[str] = None
        self.original_image: Optional[Image.Image] = None
        self.inverted_image: Optional[Image.Image] = None
        self.original_placeholder_image: Optional[Image.Image] = None
        self.placeholder_image = ImageTk.PhotoImage(self.convert_placeholder_image_to_theme())
        self.process_image = tk.PhotoImage(
            data="iVBORw0KGgoAAAANSUhEUgAAACMAAAAjAQMAAAAkFyEaAAAABlBMVEUAAADw0gCjrW2CAAAAI0lEQVQI"
                 "12NgQAL2////byCFPPihHg9JqmkHGOrxkHj1IgEAZH9nDhQLxPMAAAAASUVORK5CYII="
        )

        # Create value lists
        self.theme_combo_list = ["Dark theme", "Light theme"]

        # Create control variables
        self.theme_value = tk.StringVar()
        self.inversion_value = tk.IntVar(value=Config.config.invert_value)

        # Create widgets :)
        self.setup_widgets()

        # Set up key binds
        self.parent.bind('<Control-v>', lambda e: self.process_image_from_clipboard())
        self.parent.bind('<Shift-Insert>', lambda e: self.process_image_from_clipboard())
        self.parent.bind('<Control-c>', lambda e: self.save_image_to_clipboard())

    def setup_widgets(self):
        # Menu
        self.theme_combo = ttk.Combobox(
            self, state="readonly", values=self.theme_combo_list, textvariable=self.theme_value
        )
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        self.theme_combo.current(Config.config.theme != "dark")
        self.theme_combo.pack(fill=BOTH, anchor=N)

        # Image in canvas
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(expand=True, fill=BOTH, anchor=CENTER)

        self.canvas = Canvas(self.canvas_frame, width=620, height=340, scrollregion=(0, 0, 620, 340))
        self.canvas.create_image((310, 170), anchor=CENTER, image=self.placeholder_image, tag="img")

        hbar = tk.Scrollbar(self.canvas_frame, orient=HORIZONTAL)
        hbar.pack(side=BOTTOM, fill=X)
        hbar.config(command=self.canvas.xview)
        vbar = tk.Scrollbar(self.canvas_frame, orient=VERTICAL)
        vbar.pack(side=RIGHT, fill=Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(expand=True, fill=BOTH)

        # register the canvas as a drop target
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.process_grabbed_image)

        self.parent.bind("<MouseWheel>", self.on_mousewheel_y)
        self.parent.bind("<Control-MouseWheel>", self.on_mousewheel_x)

        # Buttons
        self.settings_frame = ttk.Frame(self)
        self.settings_frame.pack(fill=BOTH, anchor=S)

        for index in range(4):
            self.settings_frame.columnconfigure(index=index, weight=1)

        for index in range(2):
            self.settings_frame.rowconfigure(index=index, weight=1)

        self.button_from_clipboard = ttk.Button(
            self.settings_frame, text="From clipboard", command=self.process_image_from_clipboard
        )
        self.button_from_clipboard.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")

        self.button_to_clipboard = ttk.Button(
            self.settings_frame, text="To clipboard", command=self.save_image_to_clipboard
        )
        self.button_to_clipboard.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")

        self.button_save_as = ttk.Button(
            self.settings_frame, text="Save as", command=self.save_image_to_disk
        )
        self.button_save_as.grid(row=1, column=1, padx=5, pady=10, sticky="nsew")

        # Scale for inversion
        self.scale = ttk.Scale(
            self.settings_frame,
            from_=0,
            to=100,
            variable=self.inversion_value,
            command=self.change_inversion
        )
        self.scale.grid(row=0, column=1, padx=20, pady=20, sticky="ew", columnspan=2)

        self.parent.bind("<Left>", lambda e: self.scale.set(self.scale.get() - 1))
        self.parent.bind("<Right>", lambda e: self.scale.set(self.scale.get() + 1))

        # Label for inversion
        self.label = ttk.Label(
            self.settings_frame,
            text=f"Inversion: {self.inversion_value.get()}%",
            justify="center",
            font=("-size", 10, "-weight", "bold"),
        )
        self.label.grid(row=0, column=3, pady=10, padx=10)

        self.button_help = ttk.Button(
            self.settings_frame, text="Help", command=self.show_help
        )
        self.button_help.grid(row=1, column=2, padx=5, pady=10, sticky="nsew")

        # Label for errors
        self.errors_label = ttk.Label(
            self.settings_frame,
            text="",
            justify="center",
            font=("-size", 10, "-weight", "bold"),
        )
        self.errors_label.grid(row=1, column=3, pady=10, padx=10)

    def change_theme(self, event):
        force_dark = self.theme_combo.get() == self.theme_combo_list[0]
        force_light = self.theme_combo.get() == self.theme_combo_list[1]
        if force_dark and self.parent.tk.call("ttk::style", "theme", "use") != "azure-dark":
            # Set dark theme
            self.parent.tk.call("set_theme", "dark")
            Config.config.theme = "dark"
            self.set_placeholder_image()
            save_to_yaml()
        elif force_light and self.parent.tk.call("ttk::style", "theme", "use") != "azure-light":
            # Set light theme
            self.parent.tk.call("set_theme", "light")
            Config.config.theme = "light"
            self.set_placeholder_image()
            save_to_yaml()

    def process_grabbed_image(self, event):
        image_path = event.data.strip("{}")
        try:
            self.set_image_to_canvas(Image.open(image_path))
            self.original_image_name = path.basename(image_path).split(".", maxsplit=1)[0]
            self.apply_inversion()
            self.errors_label.config(text="")
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            self.errors_label.config(text="Couldn't get image from file drop!")

    def process_image_from_clipboard(self):
        processed = False
        images = ImageGrab.grabclipboard()
        if images is not None and isinstance(images, list):
            for image in images:
                with suppress(FileNotFoundError, UnidentifiedImageError):
                    self.set_image_to_canvas(Image.open(image))
                    self.original_image_name = f"Image-{datetime.now().strftime('%d-%m-%Y %H%M%S')}"
                    self.apply_inversion()
                    processed = True
                    break
        elif images is not None and isinstance(images, Image.Image):
            self.set_image_to_canvas(images)
            self.original_image_name = f"Image-{datetime.now().strftime('%d-%m-%Y %H%M%S')}"
            self.apply_inversion()
            processed = True

        if not processed:
            self.errors_label.config(text="Couldn't get image from clipboard!")
        else:
            self.errors_label.config(text="")

    def save_image_to_clipboard(self):
        if self.original_image is not None:
            to_clipboard(self.inverted_image if self.inverted_image is not None else self.original_image)
            self.errors_label.config(text="")
        else:
            self.errors_label.config(text="Couldn't save image to clipboard!")

    def set_image_to_canvas(self, image: Image, set_as_inverted=False):
        if set_as_inverted:
            self.inverted_image = image
        else:
            self.original_image = image
            self.inverted_image = None
        self.process_image = ImageTk.PhotoImage(image)
        self.canvas.delete("img")
        img_width = image.width // 2
        img_height = image.height // 2
        self.canvas.config(scrollregion=(0, 0, image.width, image.height))
        self.canvas.create_image((img_width, img_height), anchor=CENTER, image=self.process_image, tag="img")

    def change_inversion(self, event):
        self.label.config(text=f"Inversion: {int(self.scale.get())}%")
        Config.config.invert_value = int(self.scale.get())
        save_to_yaml()
        self.apply_inversion()

    def apply_inversion(self):
        if self.original_image is not None:
            self.set_image_to_canvas(
                invert_image_with_blend(self.original_image, self.inversion_value.get()), set_as_inverted=True
            )

    def save_image_to_disk(self):
        if self.original_image is not None:
            image = self.inverted_image if self.inverted_image is not None else self.original_image
            filetypes = [('PNG', '.png')]
            if image.mode != "RGBA":
                filetypes.append(('JPG', '.jpg'))
            filename = filedialog.asksaveasfilename(
                filetypes=filetypes,
                defaultextension=filetypes[-1][1],
                initialfile=self.original_image_name
            )
            if not filename:
                return

            image.save(fp=filename)

    def on_mousewheel_y(self, event):  # TODO: set '-2' as defined value via readonly combobox
        self.canvas.yview_scroll(int(-2 * (event.delta / 120)), "units")

    def on_mousewheel_x(self, event):
        # https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        self.canvas.xview_scroll(int(-2 * (event.delta / 120)), "units")

    def show_help(self):
        if not HelpWindow.alive:
            HelpWindow(
                x=self.parent.winfo_x() + (self.parent.winfo_width() // 2),
                y=self.parent.winfo_y() + (self.parent.winfo_height() // 2)
            )


class HelpWindow(tk.Toplevel):
    alive = False

    def __init__(self, x, y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("About program")

        for index in range(4):
            self.columnconfigure(index=index, weight=1)
            self.rowconfigure(index=index, weight=1)

        self.setup_widgets()

        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())
        self.maxsize(self.winfo_width(), self.winfo_height())
        self.geometry("+{}+{}".format(x - (self.winfo_width() // 2), y - 20 - (self.winfo_height() // 2)))

        self.focus()
        self.grab_set()
        self.__class__.alive = True

    def setup_widgets(self):
        self.label = ttk.Label(
            self,
            text=f"Image Inverter v{VERSION} by Druzai\n\n"
                 "Keybindings:\n"
                 "'Ctrl + V' or 'Shift + Insert' - Insert image from clipboard\n"
                 "'Ctrl + C' - Copy image to clipboard\n"
                 "'Arrow Right/Left' - Change inversion value by 1%\n"
                 "'MouseWheel' and 'Ctrl + MouseWheel' - Scroll image in preview",
            justify="center",
            font=("-size", 10, "-weight", "bold"),
        )
        self.label.grid(row=0, column=1, pady=10, padx=10, columnspan=2, rowspan=3)

        self.button_close = ttk.Button(
            self,
            text="Close window",
            command=self.destroy
        )
        self.button_close.grid(row=3, column=1, padx=5, pady=10, sticky="nsew", columnspan=2)

    def destroy(self):
        self.__class__.alive = False
        return super().destroy()


def startup():
    if not path.exists(Path(os.getcwd(), Config.config_name)):
        Config.config.theme = "dark"
        Config.config.invert_value = 85
        save_to_yaml(instant_save=True)
    else:
        read_from_yaml()
        if Config.config.theme not in ["dark", "light"]:
            Config.config.theme = "dark"
            save_to_yaml(instant_save=True)
    Config.config_saving_thread.start()


if __name__ == "__main__":
    # TODO: And add checkbox for sepia
    startup()
    root = TkinterDnD.Tk()
    root.title(Config.title)

    if getattr(sys, 'frozen', False) and getattr(sys, '_MEIPASS', False):
        application_path = sys._MEIPASS
    else:
        application_path = path.dirname(__file__)

    root.iconbitmap(default=path.join(application_path, Config.icon_file))

    # Set the theme
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", Config.config.theme)

    app = App(root)
    app.pack(fill=BOTH, expand=True)

    # Set a minsize for the window, and place it in the middle
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate - 20))

    root.mainloop()
