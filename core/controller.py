import numpy as np
import logging
import time
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

        # Initialise logging and tracking
        setup_logging()
        self.tracker = Tracker()

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
        try:
            wf_size, ADCs = self.acquisition_worker.data
        except TypeError:
            # type error occurs when recording in digitiser fails, so no error output here please!
            return
        except Exception as e:
            logging.exception("Error in data_handling(): ")

            

        # save the data (PUT IT HERE)

        # update visuals
        self.main_window.screen.update_ch(np.arange(0, wf_size, dtype=wf_size.dtype), ADCs)
        
        # ping the tracker (make this optional)
        self.tracker.track(ADCs.nbytes)
        
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
                digitiser.configure(dig_dict, rec_dict)
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
            self.digitiser.start_acquisition()
            self.worker_wait_condition.wakeAll()
        except Exception as e:
            logging.exception('Failed to start acquisition.')
        #self.digitiser.start_acquisition()
        #self.trigger_and_record()
        
    def stop_acquisition(self):
        '''
        Simple stopping of acquisition, this will end the AcquisitionWorkers loop and terminate
        '''
        self.digitiser.isAcquiring = False


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


class Tracker:
    '''
    Tracking class that keeps track of:
        - number of collected events
        - speed at which data is being collected
    '''

    def __init__(self):
        self.start_time = time.perf_counter()
        self.bytes_ps   = 0
        self.events_ps  = 0
        self.last_time  = self.start_time

    def track(self, nbytes: int = 0):
        '''
        Tracker outputting the number of events that arrive per second
        '''
        self.events_ps += 1
        self.bytes_ps += nbytes

        t_check = time.perf_counter()
        if t_check - self.last_time >= 1.0:
            MB = self.bytes_ps / 1000000
            logging.info(f'|| {self.events_ps} events/sec || {MB:.2f} MB/sec ||')
            self.last_time = t_check
            self.bytes_ps = 0
            self.events_ps = 0