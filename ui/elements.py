'''
jwaiton 05/25

Different UI elements for the application.
'''
import random
import logging
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QFileDialog,
    QApplication
)

class config_files(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Configuration Files", parent = parent)

        self.dig_conf = QPushButton("Digitiser Config")
        self.rec_conf = QPushButton("Recording Config")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.dig_conf)
        layout.addWidget(self.rec_conf)

        # upon pressing open up file dialog
        self.dig_conf.clicked.connect(lambda: self.find_file('dig'))
        self.rec_conf.clicked.connect(lambda: self.find_file('rec'))

    def find_file(self, conf_type):
        '''
        Open a file dialog to select a configuration file.
        '''
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Configuration File", "", "Conf Files (*.conf);;All Files (*)", options=options)
        if file_name:
            logging.info(f"Selected {conf_type} configuration file: {file_name}")
            # save config file to controller dig_config and rec_config
            if conf_type == 'dig':
                self.dig_config = file_name
            elif conf_type == 'rec':
                self.rec_config = file_name
            else:
                logging.error("Invalid configuration file type selected.")
                return
        else:
            logging.warning("No file selected.")
            return

class StatsBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Stats", parent = parent)

        self.fps_label = QLabel("FPS: 0")
        #self.events_collected = QLabel(f'evts: {self.acq.events_collected}')
        #self.rate = QLabel(f'Rate: {self.acq.rate} Hz')

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.fps_label)

class ConnectDigitiser(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Connection", parent = parent)
        self.controller = controller

        self.isConnected = False

        layout = QVBoxLayout()
        self.setLayout(layout)


        self.con        = QPushButton("Connect")
        #self.combobox_ports = QComboBox()
        self.reset_con        = QPushButton("Reset")

        layout.addWidget(self.con)
        #layout.addWidget(self.combobox_ports)
        layout.addWidget(self.reset_con)

        self.reset_con.clicked.connect(self.reset_connection)
        self.con.clicked.connect(self.controller.connect_digitiser)
    
    def reset_connection(self):
        logging.info('Resetting connection...')
        #self.combobox_ports.clear()
        # here instead add the digitiser type connected, num channels perhaps
        # for now, just add some random ports
        #self.combobox_ports.addItems([f"Port {random.randint(0,10)}", f"Port {random.randint(0,10)}", f"Port {random.randint(0,10)}"])
    
    def connect(self):
        logging.info(f'Attempting connection to {self.controller}...')
        # if not connected, try to connect.
        self.controller.connect_digitiser()


class Acquisition(QGroupBox):
    '''
    Acquisition control panel for the digitiser.
    Start and stop button to start and stop the acquisition.
    '''
    def __init__(self, controller, parent=None):
        super().__init__("Acquisition", parent = parent)
        
        self.controller = controller
        

        self.start_stop = QPushButton("Start")
        self.start_stop.setStyleSheet("background-color: green; color: black")

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.start_stop)

        self.isAcquiring = False
        self.start_stop.clicked.connect(self.toggle_acquisition)
    

    def toggle_acquisition(self):
        if self.isAcquiring:
            logging.info('Stopping acquisition...')
            self.start_stop.setText("Start")
            self.start_stop.setStyleSheet("background-color: green; color: black")
            self.isAcquiring = False
            # stop the acquisition
            # self.controller.stop_acquisition()
        else:
            logging.info('Starting acquisition...')
            self.start_stop.setText("Stop")
            self.start_stop.setStyleSheet("background-color: red; color: white")
            self.isAcquiring = True
            # start the acquisition
            # self.controller.start_acquisition()
    