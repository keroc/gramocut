# -*- coding: utf-8 -*-

'''
Gramocut entry point and main application
'''

import customtkinter as ctk
from pydub import AudioSegment

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
        self.wave = []

        self.view_start = 0
        self.view_end = 0
        self.cursor = 0

        # Initialize internal widgets
        super().__init__(root)
        self.label_frame = ctk.CTkFrame(self)
        self.start_label = ctk.CTkLabel(self.label_frame, text='start', text_color='#A0A0A0')
        self.cursor_label = ctk.CTkLabel(self.label_frame, text='cursor', text_color='#A0A0A0')
        self.end_label = ctk.CTkLabel(self.label_frame, text='end', text_color='#A0A0A0')
        self.start_label.pack(side='left')
        self.end_label.pack(side='right')
        self.cursor_label.pack(fill='x')
        self.canvas = ctk.CTkCanvas(self, height=self.height, bg='#404040')
        self.label_frame.pack(fill='x')
        self.canvas.pack(fill='x')

        self.update()

        # Bind events
        self.canvas.bind('<Configure>', self.update)
        self.canvas.bind('<Button-1>', self.click_callback)
        self.canvas.bind('<ButtonPress-3>', self.drag_start_callback)
        self.canvas.bind('<B3-Motion>', self.drag_callback)
    
    def ms_format(self, ms):
        ms_part = ms % 1000
        s_part = int(ms/1000)%60
        min_part = int(ms/60000)
        return '{:0d}m:{:02d}s:{:03d}'.format(min_part, s_part, ms_part)

    def update(self, event=None):
        self.canvas.delete('all')

        # Update time label
        self.start_label.configure(text=self.ms_format(self.view_start))
        self.end_label.configure(text=self.ms_format(self.view_end))
        self.cursor_label.configure(text='{} / {}'.format(self.ms_format(self.cursor), self.ms_format(len(self.wave))))

        if len(self.wave) == 0:
            # If no segment loaded, stop here
            return
        
        # Compute metrics
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        ms_per_pix = int((self.view_end - self.view_start) / width)
        
        # Draw waveform
        for pix in range(0,width):
            pix_start_ms = self.view_start + pix*ms_per_pix
            pix_end_ms = self.view_start + (pix+1)*ms_per_pix
            vol = max(self.wave[pix_start_ms:pix_end_ms])*height
            space = int((height-vol)/2)
            self.canvas.create_line(pix, space, pix, space+vol, fill='white')
        
        # Draw cursor if inside the canvas
        if self.view_start <= self.cursor and self.cursor < self.view_end:
            x = int((self.cursor - self.view_start) / ms_per_pix)
            self.canvas.create_line(x, 0, x, height, fill='red')
        
        
    
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

    def apply_zoom(self, zoom):
        '''
        Apply a zoom factor, if zoom < 1 it's a zoom in, if zoom > 1 it's a zoom out
        '''
        view_width = self.view_end - self.view_start
        new_width = max(zoom * view_width, 10000)
        offset = int((view_width - new_width)/2)
        
        self.view_start += offset
        if self.view_start < 0:
            self.view_start = 0
        
        self.view_end -= offset
        if self.view_end > len(self.wave):
            self.view_end = len(self.wave)

        self.update()
    
    def zoom_in(self):
        '''
        Zoom in on the waveform
        '''
        self.apply_zoom(0.8)
    
    def zoom_out(self):
        '''
        Zoom out on the waveform
        '''
        self.apply_zoom(1.2)
    
    def reset_zoom(self):
        '''
        Reset the zoom to display the whole waveform
        '''
        self.view_start = 0
        self.view_end = len(self.wave)
        self.update()
         
    def click_callback(self, event):
        # Update cursor position
        width = self.canvas.winfo_width()
        self.cursor = int((event.x / width) * (self.view_end - self.view_start)) + self.view_start
        self.update()
    
    def drag_start_callback(self, event):
        self.last_drag_x = event.x
    
    def drag_callback(self, event):
        ms_per_pix = (self.view_end - self.view_start) / self.canvas.winfo_width()
        ms_offset = int((self.last_drag_x - event.x) * ms_per_pix)

        if ms_offset < 0:
            # Limit drag to the left
            if (ms_offset * -1) > self.view_start:
                ms_offset = -1 * self.view_start
        else :
            # Limit drag to the right
            if self.view_end + ms_offset > len(self.wave) :
                ms_offset = len(self.wave) - self.view_end

        # Drag the view
        self.view_start += ms_offset
        self.view_end += ms_offset
        self.update()

        self.last_drag_x = event.x
        


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
        self.zoom_in_button = ctk.CTkButton(self.tool_frame, text="Z In", command=self.waveform.zoom_in)
        self.zoom_out_button = ctk.CTkButton(self.tool_frame, text="Z Out", command=self.waveform.zoom_out)
        self.zoom_reset_button = ctk.CTkButton(self.tool_frame, text="Z Reset", command=self.waveform.reset_zoom)
        self.zoom_in_button.pack(side='left')
        self.zoom_out_button.pack(side='left')
        self.zoom_reset_button.pack(side='left')
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