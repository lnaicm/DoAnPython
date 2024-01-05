import customtkinter as ctk
import numpy as np
import cv2
from image_widgets import *
from PIL import Image, ImageTk, ImageOps, ImageEnhance, ImageFilter
from menu import Menu
from rembg import remove


class App(ctk.CTk):
    def __init__(self):

        # setup
        super().__init__()
        ctk.set_appearance_mode('dark')
        self.geometry('1000x600')
        self.title('Photo Editor')
        self.minsize(800, 500)
        self.init_parameters()

        # layout
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 2, uniform = 'a')
        self.columnconfigure(1, weight = 6, uniform = 'a')

        # canvas data
        self.image_width = 0
        self.image_height = 0
        self.canvas_width = 0
        self.canvas_height = 0

        # widgets
        self.image_import = ImageImport(self, self.import_image)

        # run
        self.mainloop()

    def init_parameters(self):
        self.pos_vars = {
            'rotate': ctk.DoubleVar(value = ROTATE_DEFAULT),
            'zoom': ctk.DoubleVar(value = ZOOM_DEFAULT),
            'flip': ctk.StringVar(value = FLIP_OPTIONS[0])
        }

        self.color_vars = {
            'brightness': ctk.DoubleVar(value = BRIGHTNESS_DEFAULT),
            'grayscale': ctk.BooleanVar(value = GRAYSCALE_DEFAULT),
            'invert': ctk.BooleanVar(value = INVER_DEFAULT),
            'vibrance': ctk.DoubleVar(value = VIBRANCE_DEFAULT)
        }

        self.effect_vars = {
            'blur': ctk.DoubleVar(value = BLUR_DEFAULT),
            'contrast': ctk.IntVar(value = CONTRAST_DEFAULT),
            'effect': ctk.StringVar(value = EFFECT_OPTIONS[0])
        }

        # Connect the var to the slider
            # import_image > Menu > Frames
        # trace changes to the var
        combined_vars = list(self.pos_vars.values()) + list(self.color_vars.values()) + list(self.effect_vars.values())
        for var in combined_vars:
            var.trace('w', self.manipulate_image)
        # use the var value to change the image

    def manipulate_image(self, *args):
        self.image = self.original

        # Only apply the effect if the value is different from the default
        # rotate
        if self.pos_vars['rotate'].get() != ROTATE_DEFAULT:
            self.image = self.image.rotate(self.pos_vars['rotate'].get())

        # zoom
        if self.pos_vars['zoom'].get() != ZOOM_DEFAULT:
            self.image = ImageOps.crop(image = self.image, border = self.pos_vars['zoom'].get())

        # flip
        if self.pos_vars['flip'].get() != FLIP_OPTIONS[0]:
            if self.pos_vars['flip'].get() == 'X':
                self.image = ImageOps.mirror(self.image)
            if self.pos_vars['flip'].get() == 'Y':
                self.image = ImageOps.flip(self.image)
            if self.pos_vars['flip'].get() == 'Both':
                self.image = ImageOps.mirror(self.image)
                self.image = ImageOps.flip(self.image)

        # brightness & vibrance
        if (self.color_vars['brightness'].get != BRIGHTNESS_DEFAULT):
            # brightness_enhancer = ImageEnhance.Brightness(self.image)
            self.image = ImageEnhance.Brightness(self.image).enhance(self.color_vars['brightness'].get())
        if (self.color_vars['vibrance'].get != VIBRANCE_DEFAULT):
            # vibrance_enhancer = ImageEnhance.Color(self.image)
            self.image = ImageEnhance.Color(self.image).enhance(self.color_vars['vibrance'].get())

        # grayscale and invert color
        if self.color_vars['grayscale'].get():
            self.image = ImageOps.grayscale(self.image)
        if self.color_vars['invert'].get():
            self.image = ImageOps.invert(self.image)

        # blur, contrast, effects
        if self.effect_vars['blur'].get() != BLUR_DEFAULT:
            self.image = self.image.filter(ImageFilter.GaussianBlur(self.effect_vars['blur'].get()))
        if self.effect_vars['contrast'].get() != CONTRAST_DEFAULT:
            self.image = ImageEnhance.Contrast(self.image).enhance(self.effect_vars['contrast'].get())
        match self.effect_vars['effect'].get():
            case 'Emboss': self.image = self.image.filter(ImageFilter.EMBOSS)
            case 'Find edges': self.image = self.image.filter(ImageFilter.FIND_EDGES)
            case 'Contour': self.image = self.image.filter(ImageFilter.CONTOUR)
            case 'Edge enhance': self.image = self.image.filter(ImageFilter.EDGE_ENHANCE)
            case 'Denoise': 
                img = np.array(self.image)
                img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                dst = cv2.fastNlMeansDenoisingColored(img_bgr, None, 10, 10, 7, 21)
                dst_rgb = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
                self.image = Image.fromarray(dst_rgb)
            case 'Remove background': self.image = remove(self.image)

        self.place_image()

    def import_image(self, path):
        self.original = Image.open(path)
        self.image = self.original
        self.image_ratio = self.image.size[0]/self.image.size[1]
        # print(self.image_ratio)
        self.image_tk = ImageTk.PhotoImage(self.image)

        self.image_import.grid_forget()
        self.image_output = Image_Output(self, self.resize_image)
        self.close_button = CloseOutput(self, self.close_edit)
        self.menu = Menu(self, self.pos_vars, self.color_vars, self.effect_vars, self.export_image)

    def close_edit(self):
        # hide the image and the close button
        self.image_output.grid_forget()
        self.close_button.place_forget()
        self.menu.grid_forget()
        # recreate the import button
        self.image_import = ImageImport(self, self.import_image)

    def resize_image(self, event):
        # current canvas ratio
        canvas_ratio = event.width/event.height

        # update canvas attribute
        self.canvas_width = event.width
        self.canvas_height = event.height

        # resize image
        # if canvas is wider than image
        if canvas_ratio > self.image_ratio:
            self.image_height = int(event.height)
            self.image_width = int(self.image_height * self.image_ratio)
        # else if canvas is taller than image
        else:
            self.image_width = int(event.width)
            self.image_height = int(self.image_width / self.image_ratio)

        self.place_image()

    def place_image(self):
        # place image
        self.image_output.delete('all')
        resized_image = self.image.resize((self.image_width, self.image_height))
        self.image_tk = ImageTk.PhotoImage(resized_image)
        self.image_output.create_image(self.canvas_width/2, self.canvas_height/2, image = self.image_tk)

    def export_image(self, name, file, path):
        export_string = f'{path}/{name}.{file}'
        self.image.save(export_string)
        print(export_string)

App()
