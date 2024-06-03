# -*- coding: utf-8 -*-

'''
Gramocut entry point and main application
'''

import customtkinter as ctk
from pydub import AudioSegment, effects

class VinylWidget(ctk.CTkCanvas):
    '''
    Icon of a vinyl disc to visualize tracks
    '''
    def __init__(self, root, start=-0.1, end=1.1, tagColor='red', trackColor='blue'):
        self.size = 80
        self.diskRadius = int(0.4 * self.size)
        self.tagRadius = int(0.2 * self.diskRadius)

        self.start = start
        self.end = end
        self.tagColor = tagColor
        self.trackColor = trackColor
        
        super().__init__(root, width=self.size, height=self.size, bg='#404040')
        self.update()

    def drawDisk(self, radius, color):
        self.create_aa_circle(x_pos=self.size/2, y_pos=self.size/2, radius=radius, fill=color)
    
    def convert_to_radius(self, percent):
        return int((1.0-percent) * (self.diskRadius - self.tagRadius) + self.tagRadius)

    def update(self):
        self.delete('all')

        # Draw all the vinyl
        self.drawDisk(self.diskRadius, 'black')

        # Draw the track start
        if self.start >= 0 and self.start <= 1:
            self.drawDisk(self.convert_to_radius(self.start), self.trackColor)

        # Draw the track end
        if self.end >= 0 and self.end <= 1:
            self.drawDisk(self.convert_to_radius(self.end), 'black')

        # Draw the central tag
        self.drawDisk(self.tagRadius, self.tagColor)
        self.drawDisk(int(0.2*self.tagRadius), 'black')

class Waveform(ctk.CTkFrame):
    def __init__(self, root, height=100):
        self.height = height
        self.wave = None

        self.view_start = 0
        self.view_end = 0
        self.cursor = 0

        super().__init__(root)
        self.canvas = ctk.CTkCanvas(self, height=self.height, bg='#404040')
        self.scroll = ctk.CTkScrollbar(self, orientation='horizontal')
        self.canvas.pack(fill='x')
        self.scroll.pack(fill='x')

        self.update()

        # Update on each size change
        self.canvas.bind('<Configure>', self.update)

    def update(self, event=None):
        self.canvas.delete('all')

        if self.wave is None:
            # If no segment loaded, stop here
            return
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        ms_per_pix = int((self.view_end - self.view_start) / width)
        
        for pix in range(0,width):
            pix_start_ms = self.view_start + pix*ms_per_pix
            pix_end_ms = self.view_start + (pix+1)*ms_per_pix
            vol = max(self.wave[pix_start_ms:pix_end_ms])*height
            space = int((height-vol)/2)
            self.canvas.create_line(pix, space, pix, space+vol, fill='white')
        
        
    
    def set_audio(self, audio):
        # Build a simplified waveform of the source (normalized max volume of each ms)
        mono = audio.set_channels(1)
        max_sample = mono.max
        self.wave = [ms.max / max_sample for ms in mono]

        # Initialize view
        self.view_start = 0
        self.view_end = len(self.wave)
        self.cursor = 0

        self.update()


class SourceFrame(ctk.CTkFrame):
    '''
    Frame to handle the source music sample in the App
    '''
    def __init__(self, root):
        super().__init__(root)

        self.root = root

        # Build the source frame with widgets
        self.vinyl = VinylWidget(self)
        self.vinyl.grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        self.info_frame = ctk.CTkFrame(self)
        self.open_button = ctk.CTkButton(self.info_frame, text="Open", command=self.load_from_file)
        self.source_label = ctk.CTkLabel(self.info_frame, text="<No source selected>")
        self.open_button.pack(side='left', padx=5)
        self.source_label.pack(side='left', padx=5, fill='x')
        self.info_frame.grid(row=0, column=1, padx=5, pady=5, sticky='WE')

        self.waveform = Waveform(self)
        self.waveform.grid(row=1, column=1, padx=5, pady=5, sticky='WE')

        self.tool_frame = ctk.CTkFrame(self)
        self.play_button = ctk.CTkButton(self.tool_frame, text="play")
        self.play_button.pack(side='left')
        self.tool_frame.grid(row=2, column=1, padx=5, pady=5, sticky='WE')

        self.columnconfigure(1, weight=1)
    
    def load_from_file(self):
        filename = ctk.filedialog.askopenfilename()
        if filename != () and filename != "":
            self.root.source_segment = AudioSegment.from_file(filename)
            self.waveform.set_audio(self.root.source_segment)
            self.source_label.configure(text=filename)


# Application class (root widget)
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.source_segment = None

        # Add the source frame
        self.srcFrame = SourceFrame(self)
        self.srcFrame.pack(padx=5, pady=5, fill="x")


# Entry point
if __name__ == '__main__':

    # Custom Tkinter general configuration
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("dark-blue")

    # Start the App
    app = App()
    app.mainloop()