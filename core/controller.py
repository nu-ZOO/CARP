import numpy as np
import logging
#from caen_felib import lib, device, error
from typing import Optional

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
    QApplication
)

from PySide6.QtCore import QTimer, QWaitCondition, QMutex, Signal, QThread, QObject

from caen_felib import lib, device, error

from core.io import read_config_file
from core.logging import setup_logging
from felib.digitiser import Digitiser
from ui import oscilloscope

class Controller:
    def __init__(self, 
                 dig_config: Optional[str] = None, 
                 rec_config: Optional[str] = None):
        '''
        Initialise controller for GUI and digitiser
        '''

        # Initialise logging
        setup_logging()


        # digitiser connection first
        self.dig_config = dig_config
        self.rec_config = rec_config

        if dig_config is None:
            logging.warning("No digitiser configuration file provided. Digitiser will not be connected.")
            self.digitiser = None
        else:
            self.digitiser = self.connect_digitiser()

        # check digitiser connection, if valid set isConnected to True
        if self.digitiser is not None:
            self.digitiser.isConnected = True
            logging.info(f"Digitiser connected: {self.digitiser.URI}")
        else:
            logging.warning("Digitiser not connected.")


        # gui second
        self.app = QApplication([])
        self.main_window = oscilloscope.MainWindow(controller = self)

        self.fps_timer  = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.spf = 1 # seconds per frame


        # worker third
        if self.digitiser is not None and self.digitiser.isConnected:
            self.initialise_worker()

    def initialise_worker(self):
        '''
        Initialise the worker thread.
        This in turn should begin the data collection (I think?)
        '''

        # create thread to manage data output
        self.worker_wait_condition = QWaitCondition()
        self.acquisition_worker    = AcquisitionWorker(self.worker_wait_condition, digitiser = self.digitiser)
        self.acquisition_thread    = QThread()
        self.acquisition_worker.moveToThread(self.acquisition_thread)
        self.acquisition_thread.started.connect(self.acquisition_worker.run)
        self.acquisition_worker.data_ready.connect(self.data_handling)
        self.acquisition_thread.start()


    def data_handling(self):
        # visualise (and at some point, collect in a file)
        wf_size, ADCs = self.data
        self.main_window.screen.update_ch(np.arange(0, wf_size, dtype=wf_size.dtype), ADCs)
        # prep the next thread
        if self.digitiser.isAcquiring:
            self.worker_wait_condition.notify_one()


    def update_fps(self):
        '''
        Update the FPS label in the GUI
        '''
        fps = 1 / self.spf
        self.main_window.stats_box.fps_label.setText(f"FPS: {fps:.2f}")

    def run_app(self):
        self.main_window.show()
        return self.app.exec()
    
    def connect_digitiser(self):
        '''
        Connect to the digitiser using the provided configuration file.
        This is a placeholder function and should be replaced with actual
        digitiser connection logic.
        '''

        # Load in configs
        dig_dict = read_config_file(self.dig_config)
        rec_dict = read_config_file(self.rec_config)
        
        if dig_dict is None:
            logging.error("Digitiser configuration file not found or invalid.")
            #raise ValueError("Digitiser configuration file not found or invalid.")
        else:
            digitiser = Digitiser(dig_dict)
            digitiser.connect()
            # Only add to the main window if it exists
            if hasattr(self, 'main_window'):
                self.main_window.control_panel.acquisition.update()

        # once connected, configure recording setup
        if rec_dict is None:
            logging.warning("No recording configuration file provided.")
        else:
            if (digitiser is not None) and digitiser.isConnected:
                digitiser.configure(rec_dict)
        return digitiser              
            

    def start_acquisition(self):
        '''
        Start the acquisition in multiple steps:
            - Start the digitiser acquisition based on whatever trigger
              settings are applied,
            - Initialise the data reader,
            - Initialise the output visuals.
        '''
        try:
            self.acquisition_thread.start()
        except Exception as e:
            logging.exception('Failed to start acquisition.')
        #self.digitiser.start_acquisition()
        #self.trigger_and_record()
        
    def stop_acquisition(self):
        '''
        Simple stopping of acquisition, this will end the AcquisitionWorkers loop and terminate
        '''
        self.digitiser.isAcquiring = False

    def trigger_and_record(self):
        '''
        Apply whatever trigger is designated and record.
        Needs to also print occasionally to output.
        '''
        if self.digitiser.isAcquiring:
            evt_cnt = 0
            match self.digitiser.trigger_mode:
                case 'SWTRIG':
                    self.SW_record()
                case _:
                    logging.info(f'Trigger mode {self.trigger_mode} not currently implemented.')
                    self.stop_acquisition()    

        # check after running if isAcquiring is still enabled.
        if not self.digitiser.isAcquiring:
            self.digitiser.stop_acquisition()
            logging.info(f'Stopped acquisition.')


    def SW_record(self):
        # spam triggers as fast as possible here
        evt_counter = 0
        while self.digitiser.isAcquiring:
            self.digitiser.dig.cmd.SENDSWTRIGGER()

            try:
                self.digitiser.endpoint.read_data(100, self.digitiser.data) # timeout first number in ms
            except error.Error as ex:
                logging.exception("Error in readout:")
                if ex.code is error.ErrorCode.TIMEOUT:
                    continue
                if ex.code is error.ErrorCode.STOP:
                    break
                raise ex
        
            # ensure the input and trigger are acceptable (I think?)
            #assert self.data[3].value == 1 # VPROBE INPUT? I need to understand this
            #assert self.data[6].value == 1 # VPROBE TRIGGER?
            waveform_size = self.digitiser.data[7].value
            valid_sample_range = np.arange(0, waveform_size, dtype = waveform_size.dtype)

            # increase the event counter
            evt_counter += 1

            if (evt_counter % 100) == 0:
                self.main_window.screen.update_ch(valid_sample_range, (self.digitiser.data[3].value))



class AcquisitionWorker(QObject):

    data_ready = Signal()

    def __init__(self, wait_condition, digitiser, parent=None):
        super().__init__(parent=parent)
        self.wait_condition = wait_condition
        self.digitiser = digitiser
        self.mutex = QMutex()
        # ensure on initial startup that you're not acquiring.
        self.digitiser.isAcquiring = False
    
    
    def run(self):

        self.digitiser.start_acquisition()
        
        while True:
            self.mutex.lock()
            if not self.digitiser.isAcquiring:
                self.wait_condition.wait(self.mutex)
            self.mutex.unlock()
            

            self.data = self.digitiser.acquire()
            self.data_ready.emit()
        
        self.stop()

    def stop(self):
        self.digitiser.stop_acquisition()
        self.wait_condition.wakeAll()