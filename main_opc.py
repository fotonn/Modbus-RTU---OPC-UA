from opcua import ua, Server
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import pymodbus
import sys
from PyQt5.QtGui import  (QIcon,QStandardItemModel,QStandardItem)
from PyQt5.QtWidgets import (QWidget, QToolTip, QPushButton, QMessageBox,QApplication,QMainWindow, QAction, qApp,QFileDialog,QTreeView,QTreeWidgetItem,QLineEdit,QLabel,QComboBox,QFrame, QFormLayout, QTextEdit)
from PyQt5.QtWidgets import (QTreeWidgetItemIterator,QTableWidget,QTableWidgetItem)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread
import struct
from  pymodbus.client.sync import ModbusSerialClient as ModbusClient
import serial.rs485
import time
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.compat import iteritems
import threading
import gc

server = Server()
server.set_endpoint("opc.tcp://localhost:4840/")
#server.set_endpoint("opc.tcp://192.168.0.167:4840/")

# setup our own namespace, not really necessary but should as spec
uri = "http://examples.freeopcua.github.io"
idx = server.register_namespace(uri)

# get Objects node, this is where we should put our nodes
objects = server.get_objects_node()

# populating our address space; in most real use cases this should be imported from UA spec XML
myobj = objects.add_object(idx, "MyObject")
myvar = myobj.add_variable(idx, "MyVariable", 0.0)
myvar2 = myobj.add_variable(idx, "MyVariable2", 0.0)
myprop = myobj.add_property(idx, "MyProperty", 0)
mywritevar = myobj.add_variable(idx, "MyClientWrite", 0)
mywritevar.set_writable()  # Set MyVariable to be writable by clients

# starting!
server.start()

# after the UA server is started initialize the mirrored object




flList = ['Folder1', 'Folder2', 'Folder3']
PortsList = ['COM1', 'COM2', 'COM3', 'COM4']
VeloList = ['9600', '19200', '38400', '115000']
datatypes = [ua.VariantType.Boolean, ua.VariantType.Byte, ua.VariantType.Double, ua.VariantType.String, ua.VariantType.UInt16, ua.VariantType.UInt32]
datatypes2= ['Boolean', 'Byte', 'Double', 'String', 'UInt16', 'UInt32', 'Float']
flListopc =[]
variable = []
variables = []
typesfromfl = []
namesfromfl = []
values_for_transmit = [0,0,0,0]
datatype = 'string'


status = False
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        global flList
        global datatypes
        self.versionPr = 'FOTON OPC v 0.10'
        self.setGeometry(400, 200, 1000, 520)
        self.setWindowTitle(self.versionPr)
        #self.setWindowIcon(QIcon(self.imgPath + 'gnome-monitor.png'))
        self.h = self.frameGeometry().height()

        font = QFont()
        font.setPointSize(12)

        self.label0 = QLabel(self)
        self.label0.setFont(font)
        self.label0.move(50, 20)
        self.label0.resize(300, 25)
        self.label0.setText("IP сервера:")

        self.tty = QLineEdit(self)
        self.tty.setFont(font)
        self.tty.move(50,50)
        self.tty.resize(150, 25)

        self.label0 = QLabel(self)
        self.label0.setFont(font)
        self.label0.move(50, 80)
        self.label0.resize(300, 25)
        self.label0.setText("Порт:")

        self.port = QLineEdit(self)
        self.port.setFont(font)
        self.port.move(50, 110)
        self.port.resize(150, 25)

        self.labelv = QLabel(self)
        self.labelv.setFont(font)
        self.labelv.move(50, 140)
        self.labelv.resize(300, 25)
        self.labelv.setText("Переменная:")

        self.labelv = QLabel(self)
        self.labelv.setFont(font)
        self.labelv.move(50, 220)
        self.labelv.resize(300, 25)
        self.labelv.setText("Значение:")

        self.labelt = QLabel(self)
        self.labelt.setFont(font)
        self.labelt.move(250, 140)
        self.labelt.resize(300, 25)
        self.labelt.setText("Тип данных:")

        self.modlabel = QLabel(self)
        self.modlabel.setFont(font)
        self.modlabel.move(520, 20)
        self.modlabel.resize(300, 25)
        self.modlabel.setText("Modbus устройство:")

        self.variable = QLineEdit(self)
        self.variable.setFont(font)
        self.variable.move(50, 180)
        self.variable.resize(150, 25)

        self.value = QLineEdit(self)
        self.value.setFont(font)
        self.value.move(50, 250)
        self.value.resize(150, 25)

        self.button1 = QPushButton ("Start", self)
        self.button1.move(50, 290)
        self.button1.clicked.connect(self.button_click)

        self.button2 = QPushButton("Stop", self)
        self.button2.move(150, 290)
        self.button2.clicked.connect(self.button_click2)

        self.buttonadd = QPushButton("Add", self)
        self.buttonadd.move(250, 290)
        self.buttonadd.clicked.connect(self.button_add)

        self.buttonsave = QPushButton("Save", self)
        self.buttonsave.move(350, 290)
        self.buttonsave.clicked.connect(self.button_save)

        self.buttonmod = QPushButton("Listen Modbus", self)
        self.buttonmod.move(650, 290)
        self.buttonmod.clicked.connect(self.startModbus)

        self.buttoncon = QPushButton("Connect", self)
        self.buttoncon.move(550, 290)
        self.buttoncon.clicked.connect(self.connect)

        self.buttonupd = QPushButton("Update", self)
        self.buttonupd.move(750, 290)
        self.buttonupd.clicked.connect(self.Update)

        self.folders = QComboBox(self)
        self.folders.move(250, 110)
        self.folders.setFont(font)
        self.folders.resize(120, 25)
        self.folders.addItems(flList)

        self.datatypes = QComboBox(self)
        self.datatypes.move(250, 180)
        self.datatypes.setFont(font)
        self.datatypes.resize(120, 25)
        self.datatypes.addItems(datatypes2)

        self.ports = QComboBox(self)
        self.ports.move(550, 50)
        self.ports.setFont(font)
        self.ports.resize(120, 25)
        self.ports.addItems(PortsList)

        self.velocity = QComboBox(self)
        self.velocity.move(550, 80)
        self.velocity.setFont(font)
        self.velocity.resize(120, 25)
        self.velocity.addItems(VeloList)






        self.frameTable = QFrame(self)
        self.frameTable.move(50, 350)
        self.frameTable.setFont(font)
        self.frameTable.resize(1350, 950)
        self.frameTable.setVisible(True)
        self.treeTable = QTableWidget(self.frameTable)
        fontTable = QFont()
        fontTable.setPointSize(10)
        self.treeTable.setFont(fontTable)
        self.treeTable.resize(1000,200)
        self.treeTable.setColumnCount(3)
        self.treeTable.setRowCount(1)
        self.treeTable.setHorizontalHeaderLabels(['Имя переменной', 'Значение', 'Тип данных'])
        self.treeTable.resizeColumnsToContents()
        self.treeTable.setColumnWidth(0, 380)
        self.treeTable.setColumnWidth(1, 400)


        #self.thread = QThread()
        #self.thread.started.connect(self.getModbus)
        #self.thread.start()


        openFile = QAction(QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        fileMenu.addAction(openFile)


        self.show()

    def showDialog(self):
        global typesfromfl
        global namesfromfl

        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')[0]

        f = open(fname, 'r')

        e = ET.parse(fname)
        doc = e.getroot()

        for v in e.findall('var'):
            typesfromfl.append(v.get('type'))
            namesfromfl.append( v.get('name'))
            new_var = [v.get('name'), 'value', v.get('type')]
            variables.append(new_var)
        print(variables)
        self.treeTable.setRowCount(len(variables))
        for i in range(0, len(variables)):
            self.treeTable.setItem(i, 0, QTableWidgetItem(variables[i][0]))
            self.treeTable.setItem(i, 1, QTableWidgetItem(variables[i][1]))
            self.treeTable.setItem(i, 2, QTableWidgetItem(variables[i][2]))
            i += 1
        #with f:
            #data = f.read()
            #print(data)
    def button_click(self):

        a = self.port.text()
        print(a)
        global status
        status = True
        print(status)
    def connect(self):
        ind = self.ports.currentIndex()
        port = PortsList[ind]
        baud = self.velocity.currentIndex()
        portbaud = int(VeloList[baud])
        connect(port, portbaud)

    def button_click2(self):
        global status
        status = False
        print(status)
        disconnect()

    datatypes2 = ['Boolean', 'Byte', 'Double', 'String', 'UInt16', 'UInt32', 'Float']

    def startModbus(self):
        self.myThread = ModbusThread()
        self.myThread.start()

    def button_save(self):
        createXML()


    def Update(self):
        index = self.folders.currentIndex()
        try:
         dv = ua.DataValue(ua.Variant(5.5, ua.VariantType.Double))
         myvar = flListopc[index].get_child(["0:Objects", "Folder1"])
         print(myvar)
         myvar.set_value(dv)
        except Exception as ex:
         print(ex)


    def button_add (self):
        global idx
        global objects
        global datatype
        global variable
        global variables
        global values_for_transmit
        indexdt = self.datatypes.currentIndex()
        name = self.variable.text()
        a = name

        print(name)
        value = self.value.text()
        print(value)

        index = self.folders.currentIndex()


        if indexdt == 0:
           value = bool(value)
           a = flListopc[index].add_variable(idx, name, value, ua.VariantType.Boolean)
           datatype = 'bool'
        if indexdt == 1:
            value = int(value)
            a = flListopc[index].add_variable(idx, name, value, ua.VariantType.Byte)
            datatype = 'byte'
        if indexdt == 2:
            value = int(value)
            a = flListopc[index].add_variable(idx, name, value, ua.VariantType.Double)
            a.set_writable()
            datatype = 'double'
        if indexdt == 3:
            value = str(value)
            a = flListopc[index].add_variable(idx, name, value, ua.VariantType.String)

            datatype = 'string'
        if indexdt == 4:
            value = int(value)
            a = flListopc[index].add_variable(idx, name, value, ua.VariantType.UInt16)
            datatype ='UInt16'

        if indexdt == 5:
            value = int(value)
            a = flListopc[index].add_variable(idx, name, value, ua.VariantType.UInt32)
            datatype='UInt32'

        if indexdt == 6:

           try:
            for val in values_for_transmit:

             a = flListopc[index].add_variable(idx, 'value'+str(values_for_transmit.index(val)), val, ua.VariantType.Float)
             datatype='Float'
           except Exception as e:
               print(e)
        print(a, value, name, datatype)
        new_var = [name, value, datatype]
        variables.append(new_var)
        print(variables)
        self.treeTable.setRowCount(len(variables))
        for i in range(0, len(variables)):
            self.treeTable.setItem(i, 0, QTableWidgetItem(variables[i][0]))
            self.treeTable.setItem(i, 1, QTableWidgetItem(variables[i][1]))
            self.treeTable.setItem(i, 2, QTableWidgetItem(variables[i][2]))
            i += 1
        #variable.append(name, value,datatype)
        #variables.append(variable)
        #print(variables)

def getModbus():
 global values_for_transmit

 while True:

    try:
          rr = client.read_holding_registers(0x00, 8, unit=1)
          #decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)

          arr = [rr.registers[i:i + 2] for i in range(0, len(rr.registers), 2)]
          print(arr)


          for x in arr:
            decoder = BinaryPayloadDecoder.fromRegisters(x, endian=Endian.Little)
            print(decoder.decode_32bit_float())
            #values_for_transmit[arr.index(x)] = decoder.decode_32bit_float()
            #print(values_for_transmit)
            t = x
            packed_string = struct.pack("HH", *t)
            unpacked_float = struct.unpack("f", packed_string)[0]
            print(unpacked_float)
            print(arr.index(x))

            values_for_transmit[arr.index(x)] = unpacked_float

    except Exception as e:
          print(e)
    print(values_for_transmit)

 # setup our server
def connect(port, baudrate):
    global server
    global myobj
    global client
    my_python_obj = MyObj(server, myobj)

    client = ModbusClient(method='rtu', port=port, timeout=0.5, baudrate=baudrate)
    client.connect()
    rs485_mode = serial.rs485.RS485Settings(delay_before_tx=0, delay_before_rx=0, rts_level_for_tx=True,
                                            rts_level_for_rx=False, loopback=False)
    # client.socket.rs485_mode = rs485_mode
    builder = BinaryPayloadBuilder(endian=Endian.Big)
    print('connected')

 #finally:
     # close connection, remove subscriptions, etc
     #server.stop()

 #try:
  #server.set_endpoint("opc.tcp://localhost:4840/")
  #server.set_server_name("Server")

  #a = len(flList)
  #print(a)
  #for i in flList:
    #global objects
    #i = objects.add_object(idx,i)
    #flListopc.append(i)
    #print(flListopc)
 #Object_1 = objects.add_object(idx,'MyFirstObject')

 #Object_2 = objects.add_object(idx,'MySecondObject')
 #Object_3 = objects.add_object(idx,'MyThirdObject')

 #myfolder = server.nodes.objects.add_folder(idx, "myEmptyFolder")
 #Analog_3 = Object_3.add_variable(idx, 'Analog_3', 50)

  #server.start()
 #except Exception as ex:
  #   print(ex)

def disconnect():
    global server
    server.stop()


def createXML():
    """
    Создаем XML файл.
    """
    # создаем дочерний суб-элемент.
    Variables = ET.Element("Variables")

    for i in range(0, len(variables)):
     ET.SubElement(Variables, "var", name=variables[i][0], type = variables[i][2]).text = "variable_1"

    tree = ET.ElementTree(Variables)
    tree.write('ser'+".xml")


class ModbusThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        global values_for_transmit
        global my_python_obj

        while True:

            try:
                rr = client.read_holding_registers(400, 8, unit=1)
                # decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, endian=Endian.Little)

                arr = [rr.registers[i:i + 2] for i in range(0, len(rr.registers), 2)]
                print(arr)

                for x in arr:
                    decoder = BinaryPayloadDecoder.fromRegisters(x, endian=Endian.Little)
                    print(decoder.decode_32bit_float())
                    # values_for_transmit[arr.index(x)] = decoder.decode_32bit_float()
                    # print(values_for_transmit)
                    t = x
                    packed_string = struct.pack("HH", *t)
                    unpacked_float = struct.unpack("f", packed_string)[0]
                    print(unpacked_float)
                    print(arr.index(x))

                    values_for_transmit[arr.index(x)] = unpacked_float

                    #my_python_obj.MyVariable = values_for_transmit[1]
                    #my_python_obj.write('MyVariable')
                    dv = ua.DataValue(ua.Variant(values_for_transmit[0], ua.VariantType.Float))
                    my_python_obj.nodes['MyVariable'].set_value(dv)
                    dv = ua.DataValue(ua.Variant(values_for_transmit[1], ua.VariantType.Float))
                    my_python_obj.nodes['MyVariable2'].set_value(dv)

            except Exception as e:
                print(e)

            print(values_for_transmit)


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription.
    The handler forwards updates to it's referenced python object
    """

    def __init__(self, obj):
        self.obj = obj

    def datachange_notification(self, node, val, data):
        # print("Python: New data change event", node, val, data)

        _node_name = node.get_browse_name()
        setattr(self.obj, _node_name.Name, data.monitored_item.Value.Value.Value)


class UaObject(object):
    """
    Python object which mirrors an OPC UA object
    Child UA variables/properties are auto subscribed to to synchronize python with UA server
    Python can write to children via write method, which will trigger an update for UA clients
    """

    def __init__(self, opcua_server, ua_node):
        self.opcua_server = opcua_server
        self.nodes = {}
        self.b_name = ua_node.get_browse_name().Name

        # keep track of the children of this object (in case python needs to write, or get more info from UA server)
        for _child in ua_node.get_children():
            _child_name = _child.get_browse_name()
            self.nodes[_child_name.Name] = _child

        # find all children which can be subscribed to (python object is kept up to date via subscription)
        sub_children = ua_node.get_properties()
        sub_children.extend(ua_node.get_variables())

        # subscribe to properties/variables
        handler = SubHandler(self)
        sub = opcua_server.create_subscription(500, handler)
        handle = sub.subscribe_data_change(sub_children)

    def write(self, attr=None):
        # if a specific attr isn't passed to write, write all OPC UA children
        if attr is None:
            for k, node in self.nodes.items():
                node_class = node.get_node_class()
                if node_class == ua.NodeClass.Variable:
                    node.set_value(getattr(self, k))
        # only update a specific attr
        else:
            self.nodes[attr].set_value(getattr(self, attr))


class MyObj(UaObject):
    """
    Definition of OPC UA object which represents a object to be mirrored in python
    This class mirrors it's UA counterpart and semi-configures itself according to the UA model (generally from XML)
    """

    def __init__(self, opcua_server, ua_node):
        # properties and variables; must mirror UA model (based on browsename!)
        self.MyVariable = 0
        self.MyProperty = 0
        self.MyClientWrite = 0

        # init the UaObject super class to connect the python object to the UA object
        super().__init__(opcua_server, ua_node)

        # local values only for use inside python
        self.testval = 'python only'


if __name__ == '__main__':

     app = QApplication(sys.argv)
     ex = App()
     my_python_obj = MyObj(server, myobj)
     sys.exit(app.exec_())



