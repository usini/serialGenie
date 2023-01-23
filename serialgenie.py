from guiManager import GuiManager
from serialManager import SerialManager

ser = SerialManager()
gui = GuiManager()
ser.create(gui)
gui.create(ser)
