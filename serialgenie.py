import serial
import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import time
import threading
#import sv_ttk
from datetime import datetime
import re
import pyautogui
import sys

ANSI_COLOR = {}
ANSI_COLOR["0;30"] = "black"
ANSI_COLOR["0;31"] = "red"
ANSI_COLOR["0;32"] = "green"
ANSI_COLOR["0;33"] = "yellow"
ANSI_COLOR["0;34"] = "blue"
ANSI_COLOR["0;35"] = "magenta"
ANSI_COLOR["0;36"] = "cyan"
ANSI_COLOR["0;37"] = "white"

ser = None
connected = False
dis_on_focus_out = False
first_device = None

"""
windows = pyautogui.getAllWindows()
for window in windows:
    print(window.title)
sys.exit(0)
"""

def get_first_device():
    ports = list(serial.tools.list_ports.comports())
    print("<------ PORTS ------->")
    for port in ports:
        print(port.device)
        if port.device != "COM1":
            return port.device
    return None


def send_data():
    global ser, connected
    data = entry.get()
    print("Data send: " + data)
    data = data + "\r\n"
    if ser is not None:
        ser.write(data.encode())

board_information = {}

def detect_color(data):
    color_code = None
    if "\x1b" in data:
        print("Colored text")
        color_code = re.search(r'\x1b\[(.*?)m', data)
        if color_code:
            data = data.replace(color_code.group(0), "")
            data = data.replace("\x1b[0m","");
            color_code = ANSI_COLOR[color_code.group(1)]
    return data, color_code

def detect_esp32_boot(data):
    if "ets " in data and data[21] == ":" and data[18] == ":":
        print("Firmware date detected")
        board_information["firmware_date"] = datetime.strptime(data, "ets %b %d %Y %H:%M:%S\r\n")
        print(board_information)
        return False
    if "rst:" in data and ",boot:" in data:
        print("Boot detected")
        tmp = data.split(",")
        board_information["reset"] = tmp[0].replace("rst:", "")
        board_information["boot"] = tmp[1].strip().replace("boot:","")
        print(board_information)
        return False
    if "clk_drv:" in data and "q_drv:" in data and "d_drv:" in data:
        return False
    if "configsip" in data and ", SPIWP:" in data:
        return False
    if "mode:" in data and ", clock div" in data:
        return False
    if "load:" in data and ",len:" in data:
        return False
    if "entry" in data and data[7] == "x":
        return False
    return True

def receive_data():
    global ser, connected, dis_on_focus_out
    while True:
        if connected and dis_on_focus_out == False:
            try:
                data = ser.readline().decode("utf-8")
            except:
                print("Read failed disconnect")
                connected = False

            if connected:
                toprint = detect_esp32_boot(data)
                data, color_code = detect_color(data)
                if toprint:
                    if color_code is not None:
                        text_widget.tag_config(color_code, foreground=color_code)
                        text_widget.insert('end', data, color_code)    
                    else:
                        text_widget.insert('end', data)
                    text_widget.see('end')

def on_focus_out(event):
    global dis_on_focus_out, connected, first_device
    if dis_on_focus_out == False and event.widget.master == None:
        print("Focus Out disconnected")
        ser.close()
        root.title(first_device + " (Pause)")
        dis_on_focus_out = True    
        connected = False
        text_widget.tag_config("reset", background="red", foreground="white")
        text_widget.insert('end', "PAUSE\n", "reset")    

def on_focus_in(event):
    global dis_on_focus_out
    if dis_on_focus_out == True:
        print("Focus in reconnect")
        dis_on_focus_out = False

def on_disconnect(ser):
    global connected
    print("Serial disconnected")
    connected = False
    root.title("Disconnected")

def reset():
    global ser
    if connected == True:
        ser.setDTR(False)
        time.sleep(0.022)
        ser.setDTR(True)
        text_widget.tag_config("reset", background="red", foreground="white")
        text_widget.insert('end', "RESET\n", "reset")    

def connection_manager():
    global ser, connected, dis_on_focus_out, first_device
    while True:
        first_device = get_first_device()
        if connected is False and dis_on_focus_out is False:
            if(first_device is not None):
                print(dis_on_focus_out)
                print("Connecting...")
                try:
                    ser = None
                    ser = serial.Serial(first_device, 115200)
                    print("Connection succeed")
                    connected = True
                    text_widget.tag_config("reset", background="red", foreground="white")
                    text_widget.insert('end', "START\n", "reset")   
                except:
                    print("Connection failed")
                    root.title("Already in used")
                    connected = False
                if connected:
                    root.title(first_device)
                    #reset()
            else:
                print("No device founded")
                root.title("No device")
                ser = None
            time.sleep(1)
        else:
            if first_device != None:
                time.sleep(5)
            else:
                print("Serial not visible")
                connected = False

bg_color = "#282c3d"
fg_color = "#bfc7d5"

root = tk.Tk()
text_frame = ttk.Frame(root)
text_frame.pack(expand=True, fill='both')

text_widget = tk.Text(text_frame)

text_widget.config(bg=bg_color, fg=fg_color)
text_widget.pack(expand=True, side="left", fill='both')

scrollbar = ttk.Scrollbar(text_frame)
scrollbar.pack(side='right', fill='y')

text_widget.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_widget.yview)

entry_frame = tk.Frame(root)
entry_frame.pack(fill='x')
entry = ttk.Entry(entry_frame, width=20)
entry.pack(side='left', fill='x', expand=True)

send_button = ttk.Button(entry_frame, text="Send", command=send_data)
send_button.pack(side='right')

reset_button = ttk.Button(entry_frame, text="Reset", command=reset)
reset_button.pack(side='right')

receive_thread = threading.Thread(target=receive_data)
receive_thread.start()

connection_thread = threading.Thread(target=connection_manager)
connection_thread.start()


root.bind("<FocusOut>", on_focus_out)
root.bind("<FocusIn>", on_focus_in)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)
# sv_ttk.use_dark_theme()
root.mainloop()

