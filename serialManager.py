import serial
import serial.tools.list_ports
import time
import re
from datetime import datetime

class SerialManager:
    def __init__(self):

        # ANSI Color for esp-idf
        self.ANSI_COLOR = {}
        self.ANSI_COLOR["0;30"] = "black"
        self.ANSI_COLOR["0;31"] = "red"
        self.ANSI_COLOR["0;32"] = "green"
        self.ANSI_COLOR["0;33"] = "yellow"
        self.ANSI_COLOR["0;34"] = "blue"
        self.ANSI_COLOR["0;35"] = "magenta"
        self.ANSI_COLOR["0;36"] = "cyan"
        self.ANSI_COLOR["0;37"] = "white"
    
        self.connection = None #Serial Object
        self.connected = False #Connection checker
        self.port = None #Serial Device port name (ex: COM2)
        self.ports = None #Serial Device list (as objects)
        self.last_data = "" #Last data received
        self.same_data_counter = 0 #Nb of times a data similar to the previous one is received
    
    def create(self, gui):
        self.gui = gui

    def receive(self):
        while True:
            if self.connected and self.gui.is_focus == False:
                try:
                    data = self.serial.readline().decode("utf-8")              
                except:
                    print("Read failed disconnect")
                    self.connected = False

                if self.last_data == data:
                    self.last_data = data
                    same_data_counter = same_data_counter + 1
                    self.gui.monitor.delete("end-2l","end-1l")
                    data = data.rstrip()
                else:
                    self.last_data = data
                    same_data_counter = 0

                if self.connected:
                    toprint = self.detect_esp32_boot(data)
                    data, color_code = self.detect_color(data)
                    if toprint:
                        if color_code is not None:
                            self.gui.monitor.tag_config(color_code, foreground=color_code)
                            self.gui.monitor.insert("end", data, color_code)
                        else:
                            self.gui.monitor.insert("end", data)
                        
                        if same_data_counter != 0:
                            self.gui.monitor.tag_config("red", background="red", foreground="white")
                            self.gui.monitor.insert("end"," ")
                            self.gui.monitor.insert("end", "(" + str(same_data_counter) + ")", "red")
                            self.gui.monitor.insert("end","\n")
                        self.gui.monitor.see('end')

    def send(self):
        data = self.gui.entry.get()
        print("Data send: " + data)
        data = data + "\r\n"
        if self.serial is not None:
            self.serial.write(data.encode())

    def reset(self):
        if self.connected == True:
            self.serial.setDTR(False)
            time.sleep(0.022)
            self.serial.setDTR(True)
            self.gui.monitor.tag_config("reset", background="red", foreground="white")
            self.gui.monitor.insert('end', "RESET\n", "reset")    

    # Get first serial device available
    # Should add other check and a way to use multiples serial Monitor
    def get_device(self):
        self.ports = list(serial.tools.list_ports.comports())
        print("<------ PORTS ------->")
        for port in self.ports:
            print(port.device)
            # Do not return if device is COM1
            if port.device != "COM1":
                return port.device
        return None
    
    def connector(self):
        while True:
            self.port = self.get_device()
            if self.connected is False and self.gui.is_focus is False:
                if(self.port is not None):
                    print("Connecting...")
                    self.serial = None
                    try:                
                        self.serial = serial.Serial(self.port, 115200)
                        self.connected = True
                        print("Connection succeed")
                    except:
                        print("Connection failed")
                        self.gui.root.title(self.port + " already in used")
                        self.connected = False
                    
                    if self.connected:
                        self.gui.monitor.tag_config("reset", background="red", foreground="white")
                        self.gui.monitor.insert('end', "START\n", "reset")   
                        self.gui.root.title(self.port)
                        #reset()
                else:
                    print("No device founded")
                    self.gui.root.title("No device")
                    ser = None
                time.sleep(1)
            else:
                if self.port != None:
                    time.sleep(5)
                else:
                    print("Serial not visible")
                    connected = False
    
    def detect_color(self, data):
        color_code = None
        if "\x1b" in data:
            color_code = re.search(r'\x1b\[(.*?)m', data)
            if color_code:
                data = data.replace(color_code.group(0), "")
                data = data.replace("\x1b[0m","");
                color_code = self.ANSI_COLOR[color_code.group(1)]
        return data, color_code

    def detect_esp32_boot(self, data):
        if "ets " in data and data[21] == ":" and data[18] == ":":
            print("Firmware date detected")
            self.gui.info["firmware_date"] = datetime.strptime(data, "ets %b %d %Y %H:%M:%S\r\n")
            print(self.gui.info)
            return False
        if "rst:" in data and ",boot:" in data:
            print("Boot detected")
            tmp = data.split(",")
            self.gui.info["reset"] = tmp[0].replace("rst:", "")
            self.gui.info["boot"] = tmp[1].strip().replace("boot:","")
            print(self.gui.info)
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

    def on_disconnect(self):
        print("Serial disconnected")
        self.connected = False
        self.gui.root.title("Disconnected")