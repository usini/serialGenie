import serial
import tkinter as tk
import serial.tools.list_ports
import time
import threading

def get_first_device():
    ports = list(serial.tools.list_ports.comports())
    if len(ports) != 0:
        for port in ports:
            if port.device != "COM1":
                return port.device
            else:
                return None
ser = None

def send_data():
    data = entry.get()
    if ser is not None:
        ser.write(data.encode())

def receive_data():
    while True:
        if ser is not None:
            data = ser.readline().decode()
            text_widget.insert('end', data)

def on_disconnect(ser):
    print("Serial disconnected")

def connection_manager():
    global ser
    while True:
        first_device = get_first_device()
        if(first_device is not None):
            ser = serial.Serial(first_device, 115200)
            ser.close = lambda: on_disconnect(ser) and ser.close()
        time.sleep(1)



root = tk.Tk()
text_frame = tk.Frame(root)
text_frame.pack(expand=True, fill='both')

text_widget = tk.Text(text_frame)
text_widget.pack(expand=True, side="left", fill='both')

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side='right', fill='y')

text_widget.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_widget.yview)

entry_frame = tk.Frame(root)
entry_frame.pack(fill='x')
entry = tk.Entry(entry_frame, width=20)
entry.pack(side='left', fill='x', expand=True)
send_button = tk.Button(entry_frame, text="Send", command=send_data)
send_button.pack(side='right')

receive_thread = threading.Thread(target=receive_data)
receive_thread.start()

root.mainloop()

