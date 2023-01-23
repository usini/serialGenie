import tkinter as tk
from tkinter import ttk
import threading
import os

class GuiManager:
    def __init__(self):
       
        # Background / Foreground color for serial message
        self.bg_color = "#282c3d"
        self.fg_color = "#bfc7d5"

        # To upload code, we need the serial monitor to be disconnected
        # The easiest way to do this is to disconnect when app is not focus
        self.is_focus = False 
        self.disable_auto_pause = False # Disable auto pause mode  

        self.info = {} # Board information

    def create(self, ser):
            self.serialManager = ser
            self.root = tk.Tk()
            self.text_frame = ttk.Frame(self.root)
            self.text_frame.pack(expand=True, fill='both')

            self.monitor = tk.Text(self.text_frame)

            self.monitor.config(bg=self.bg_color, fg=self.fg_color)
            self.monitor.pack(expand=True, side="left", fill='both')

            self.scrollbar = ttk.Scrollbar(self.text_frame)
            self.scrollbar.pack(side='right', fill='y')

            self.monitor.config(yscrollcommand=self.scrollbar.set)
            self.scrollbar.config(command=self.monitor.yview)

            self.entry_frame = tk.Frame(self.root)
            self.entry_frame.pack(fill='x')
            self.entry = ttk.Entry(self.entry_frame, width=20)
            self.entry.pack(side='left', fill='x', expand=True)

            self.send_button = ttk.Button(self.entry_frame, text="Send", command=self.serialManager.send)
            self.send_button.pack(side='right')

            self.reset_button = ttk.Button(self.entry_frame, text="Reset", command=self.serialManager.reset)
            self.reset_button.pack(side='right')

            self.receive_thread = threading.Thread(target=self.serialManager.receive)
            self.receive_thread.start()

            self.connection_thread = threading.Thread(target=self.serialManager.connector)
            self.connection_thread.start()

            self.root.bind("<FocusOut>", self.on_focus_out)
            self.root.bind("<FocusIn>", self.on_focus_in)
            self.root.attributes("-topmost", True)
            self.root.attributes("-alpha", 0.95)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
    
    def on_focus_out(self, event):
        if self.is_focus == False and event.widget.master == None and self.disable_auto_pause == False:
            print("Focus Out disconnected")
            self.serialManager.serial.close()
            self.root.title(self.serialManager.port + " (Pause)")
            self.is_focus = True    
            self.serialManager.connected = False
            self.monitor.tag_config("reset", background="red", foreground="white")
            self.monitor.insert('end', "PAUSE\n", "reset")    

    def on_focus_in(self, event):
        if self.is_focus == True and self.disable_auto_pause == False:
            print("Focus in reconnect")
            self.is_focus = False
    
    def on_closing(self):
        print("On closing")
        self.serialManager.serial.close()
        self.root.destroy()
        os._exit(0)  