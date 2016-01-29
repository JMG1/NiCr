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
        self.serial_up = False
        self.palette = QtGui.QPalette()
        # palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.red)
        # load ui Window
        ui_w = FreeCADGui.UiLoader()
        self.w = ui_w.load(__dir__ + '/ui/ControlPanel.ui')
        # set labels
        # connnect window buttons
        self.w.btn_refresh.clicked.connect(self.connectToMachine)
        self.w.btn_send_serial_command.clicked.connect(self.sendSerialCommand)
        self.w.lineEdit_serial_command.returnPressed.connect(self.sendSerialCommand)
        self.w.btn_load_nicr_file.clicked.connect(self.selectNiCrFile)
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
            time.sleep(0.1)
            try:
                self.serial = serial.Serial(self.port_address, 115200, timeout = 1.0)
                self.palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.green)
                self.w.lb_serial_status.setPalette(self.palette)
                self.w.lb_serial_status.setText('CONNECTED')
                self.serial_up = True
                break

            except serial.SerialException:
                self.palette.setColor(QtGui.QPaltete.Foreground,QtCore.Qt.red)
                self.w.lb_serial_status.setPalette(self.palette)
                self.w.lb_serial_status.setText('Failed to connect')
                self.serial_up = False

    def sendSerialCommand(self):
        try:
            #  retrieve command from line edit
            command = self.w.lineEdit_serial_command.text()
            # erase command line text
            self.w.lineEdit_serial_command.setText('')
            # send command to machine
            self.serial.write(command)
            # read response
            r = self.serial.read(100)  # read 10000 bytes
            prev_text = self.w.textBrowser_serial_response.toPlainText()
            self.w.textBrowser_serial_response.setText(prev_text + r)

        except serial.SerialException:
            self.serial_up = False
            self.w.lb_serial_status.setText('Failed to connect')


    def selectNiCrFile(self):
        file_dir = QtGui.QFileDialog.getOpenFileName(self.w,
                                                     'Load .nicr file:',
                                                     '/home')
        nicr_file = open(file_dir[0], 'r')
        self.w.setWindowTitle('NiCr Control Panel: ' + file_dir[0])
        self.readCommandsToMachine(nicr_file)

    def readCommandsToMachine(self, nicr_file):
        line = ''
        n = 0
        while line != 'INIT' and n < 10000:
            line = nicr_file.readline()
            if line.split(':')[0] == 'PATH NAME':
                self.w.lbl_file_name.setText(line.split(':')[1])

            line_number = str(n) + '|'
            for i in xrange(10 - len(str(n) + '|')):
                line_number += ' '

            self.w.lw_commands.addItem(line_number + line[:-1])
            n += 1
