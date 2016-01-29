import serial
import FreeCADGui
import FreeCAD
import os
import time
from PySide import QtCore, QtGui

__dir__ = os.path.dirname(__file__)
# ui control panel
class ControlPanel:
    def __init__(self):
        # variables
        self.machine_started = False
        self.machine_stop = False
        self.machine_cancel = False
        self.serial_up = False
        self.palette = QtGui.QPalette()
        # palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.red)
        # load ui Window
        ui_w = FreeCADGui.UiLoader()
        self.w = ui_w.load(__dir__ + '/ui/ControlPanel.ui')
        # set labels
        self.w.progressBar_completed.setFormat('No .nicr file loaded')
        # connnect window buttons
        self.w.btn_refresh.clicked.connect(self.connectToMachine)
        self.w.btn_send_serial_command.clicked.connect(self.sendSerialCommand)
        self.w.lineEdit_serial_command.returnPressed.connect(self.sendSerialCommand)
        self.w.btn_load_nicr_file.clicked.connect(self.selectNiCrFile)
        self.w.btn_exit_control_panel.clicked.connect(self.w.close)
        self.w.btn_cancel_program.clicked.connect(self.cancelProgram)
        self.w.btn_start_program.clicked.connect(self.startMachineProgram)
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
                self.serial = serial.Serial(self.port_address, 115200, timeout = 0.1)
                self.palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.green)
                self.w.lb_serial_status.setPalette(self.palette)
                self.w.lb_serial_status.setText('CONNECTED')
                self.serial_up = True
                break

            except serial.SerialException:
                self.palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.red)
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
            r = self.serial.read(50)  # read 10000 bytes
            prev_text = self.w.textBrowser_serial_response.toPlainText()
            self.w.textBrowser_serial_response.setText(prev_text + r)

        except serial.SerialException:
            self.serial_up = False
            self.w.lb_serial_status.setText('Failed to connect')


    def selectNiCrFile(self):
        self.file_dir = QtGui.QFileDialog.getOpenFileName(self.w,
                                                     'Load .nicr file:',
                                                     '/home')
        nicr_file = open(self.file_dir[0], 'r')
        self.w.setWindowTitle('NiCr Control Panel: ' + self.file_dir[0])
        self.w.progressBar_completed.setFormat('Awaiting start... %p%')
        self.loadNiCrFile(nicr_file)
        nicr_file.close()

    def loadNiCrFile(self, nicr_file):
        n = 0
        for line in nicr_file:
            # set progres bar
            # sucio
            # b=a.w.lw_commands.item(50)
            # b.setBackground(QtGui.QBrush(QtCore.Qt.green, QtCore.Qt.SolidPattern))
            #self.w.progressBar_completed.setFormat('Awaiting start... %p%')
            # set data values
            if line.split(':')[0] == 'PATH NAME':
                self.w.lbl_file_name.setText(line.split(':')[1])

            if line.split(':')[0] == 'Z AXIS LENGTH':
                self.w.lbl_z_length.setText(line.split(':')[1])

            if line.split(':')[0] == 'MAX CUT SPEED':
                self.w.lbl_max_cut_speed.setText(line.split(':')[1])

            if line.split(':')[0] == 'MAX WIRE TEMPERATURE':
                self.w.lbl_max_temp.setText(line.split(':')[1])

            line_number = str(n) + '|'
            for i in xrange(10 - len(str(n))):
                line_number += ' '

            self.w.lw_commands.addItem(line_number + line[:-1])
            n += 1

        self.nicr_total_lines = n
        # set current highilgh on 'INIT', in blue (awaiting start)
        for i in xrange(self.nicr_total_lines):
            line = self.w.lw_commands.item(i).text().split(' ')
            for data in line:
                if data == 'INIT':
                    itm = self.w.lw_commands.item(i)
                    itm.setBackground(QtGui.QBrush(QtCore.Qt.blue, QtCore.Qt.SolidPattern))
                    itm.setForeground(QtGui.QBrush(QtCore.Qt.white, QtCore.Qt.SolidPattern))
                    self.w.lw_commands.setCurrentRow(i + 5)
                    self.cmd_init_index = i
                    break

    def startMachineProgram(self):
        if not(self.machine_started):
            self.machine_started = True
            time.sleep(0.5)
            nicr_file = open(self.file_dir[0], 'r')
            # align file pointer to list widget pointer
            for i in xrange(self.cmd_init_index - 1):
                trash = nicr_file.readline()

            # clean serial buffer:
            trash = self.serial.read(100)
            for n in xrange(self.cmd_init_index, self.nicr_total_lines):
                # highligh current line in table widget
                itm_prev = self.w.lw_commands.item(n-1)
                itm = self.w.lw_commands.item(n)
                itm.setBackground(QtGui.QBrush(QtCore.Qt.blue, QtCore.Qt.SolidPattern))
                itm.setForeground(QtGui.QBrush(QtCore.Qt.white, QtCore.Qt.SolidPattern))
                self.w.lw_commands.setCurrentRow(i + 5)
                itm_prev.setBackground(QtGui.QBrush(QtCore.Qt.blue, QtCore.Qt.SolidPattern))
                itm_prev.setForeground(QtGui.QBrush(QtCore.Qt.white, QtCore.Qt.SolidPattern))
                # set progress bar
                self.w.progressBar_completed.setFormat('Running %p%')
                self.w.progressBar_completed.setValue(n/self.nicr_total_lines)
                FreeCAD.Console.PrintMessage('0')
                # read instruction from file
                ins = nicr_file.readline()
                FreeCAD.Console.PrintMessage('1')
                self.serial.write(ins)
                # serial_resp = ''
                # while serial_resp == '':
                serial_resp = self.serial.readline()
                FreeCAD.Console.PrintMessage('2')
                # loop to waste time if stopped
                while self.machine_stop:
                    pass

                FreeCAD.Console.PrintMessage('3')
                self.w.btn_start_program.setText('Stop')
                # abort program if button pressed
                if self.machine_cancel:
                    break

            self.machine_cancel = False

        else:
            self.machine_stop += 1
            self.w.btn_start_program.setText('Resume')
            self.w.progressBar_completed.setFormat('Paused %p%')

    def cancelProgram(self):
        self.machine_cancel = True
