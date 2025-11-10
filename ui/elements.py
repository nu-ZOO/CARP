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
    def __init__(self, controller, parent=None):
        super().__init__("Configuration Files", parent = parent)

        self.controller = controller

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
                self.controller.dig_config = file_name
            elif conf_type == 'rec':
                self.controller.rec_config = file_name
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


class Acquisition(QGroupBox):
    '''
    Acquisition control panel for the digitiser.
    Start and stop button to start and stop the acquisition.
    '''
    def __init__(self, controller, parent=None):
        super().__init__("Acquisition", parent = parent)
        
        self.controller = controller
        
        # local flags (rather than using digitiser flags <-- race condition) 
        self.acquiring = False
        self.recording = False

        self.start_stop = QPushButton("Start")
        self.record     = QPushButton("Record")
        

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.start_stop)
        layout.addWidget(self.record)
        # update button based on digitiser state

        self.update()
    

    def update(self): 
        '''
        Update the acquisition status based on the digitiser state.
        '''
        # this needs fixing
        if not self.acquiring:
            self.start_stop.setStyleSheet("background-color: grey; color: black")
        if not self.recording:
            self.record.setStyleSheet("background-color: grey; color: black")
        else:
            # start stop
            self.start_stop.setStyleSheet("background-color: green; color: black")
            self.start_stop.clicked.connect(self.toggle_acquisition)
            # recording...
            self.record.setStyleSheet("background-color: red; color: black")
            self.record.clicked.connect(self.toggle_recording)
        

    def toggle_acquisition(self):
        if self.acquiring:
            logging.info('Stopping acquisition...')
            self.start_stop.setText("Start")
            self.start_stop.setStyleSheet("background-color: green; color: black")
            self.acquiring = False
            # stop the acquisition
            self.controller.stop_acquisition()
        else:
            logging.info('Starting acquisition...')
            self.start_stop.setText("Stop")
            self.start_stop.setStyleSheet("background-color: red; color: white")
            self.acquiring = True
            # start the acquisition
            self.controller.start_acquisition()
            
    def toggle_recording(self):
        '''
        if digitiser exists, must force digitiser.isAcquiring
        then enables digitiser.isRecording also
        '''
