import serial
import FreeCADGui
import os
import time
from PySide import QtCore, QtGui

__dir__ = os.path.dirname(__file__)
# ui control panel
class ControlPanel:
    def __init__(self):
        # variables
        # load ui Window
        ui_w = FreeCADGui.UiLoader()
        self.w = ui_w.load(__dir__ + '/ui/ControlPanel.ui')
        # connnect window buttons
        self.w.btn_refresh.clicked.connect(self.connectToMachine)
        self.w.btn_send_serial_command.clicked.connect(self.sendSerialCommand)
        # try to connect to machine
        self.connectToMachine()
        # show control panel window
        self.w.show()

    def connectToMachine(self):
        for n in xrange(10):
            self.w.lb_serial_status.setText('Establishing connection...')
            # USB(INT) for Arduino nano, ACM(int)for mega/uno
            self.port_address = '/dev/ttyUSB' + str(n)
            self.w.lb_serial_adress.setText(self.port_address)
            time.sleep(0.5)
            try:
                self.serial = serial.Serial(self.port_address, 115200, timeout = 2.0)
                self.w.lb_serial_status.setText('CONNECTED')
                break

            except serial.SerialException:
                self.w.lb_serial_status.setText('Failed to connect')

    def sendSerialCommand(self):
        # retrieve command from line edit
        command = self.w.lineEdit_serial_command.text()
        # erase command line text
        self.w.lineEdit_serial_command.setText('')
        # send command to machine
        self.serial.write(command)
        # read response
        r = self.serial.read(100) # read 10000 bytes
        self.w.textBrowser_serial_response.setText(r)
