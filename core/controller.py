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
from core.commands import CommandType, Command
from core.worker import AcquisitionWorker
from core.tracker import Tracker
from felib.digitiser import Digitiser
from ui import oscilloscope

from threading import Thread, Event, Lock
from queue import Queue, Empty

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
        logging.info("Controller initialising.")

        # Digitiser configuration
        self.dig_config = dig_config
        self.rec_config = rec_config

        # Thread-safe communication channels
        self.cmd_buffer = Queue(maxsize=10)
        self.display_buffer = Queue(maxsize=1024)
        self.stop_event = Event()

        # Acquisition worker
        self.worker = AcquisitionWorker(
            cmd_buffer=self.cmd_buffer,
            display_buffer=self.display_buffer,
            stop_event=self.stop_event,
        )

        # Set the callback to the controller's data_handling method
        self.worker.data_ready_callback = self.data_handling

        # Start thread and log
        self.worker.start()
        logging.info("Acquisition worker thread started.")

        # gui second
        self.app = QApplication([])
        self.main_window = oscilloscope.MainWindow(controller = self)

        self.fps_timer  = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.spf = 1 # seconds per frame

        self.connect_digitiser()


    def data_handling(self):
        '''
        Visualise data.
        '''
        while True:
            try:
                # non-blocking read from display queue
                data = self.display_buffer.get_nowait()
            except Empty:
                break

            try:
                wf_size, ADCs = data

                # update visuals
                self.main_window.screen.update_ch(np.arange(0, wf_size, dtype=wf_size.dtype), ADCs)
                
                # ping the tracker (make this optional)
                self.tracker.track(ADCs.nbytes)

            except Exception as e:
                logging.exception(f"Error updating display: {e}")


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

        Need to allow for changing config files after initial application launch.
        '''

        # Load in new configs
        # self.dig_dict = some other dig_config
        # self.rec_dict = some other rec_config

        self.cmd_buffer.put(Command(CommandType.CONNECT, (self.dig_config, self.rec_config)))

        # Only add to the main window if it exists
        if hasattr(self, 'main_window'):
            self.main_window.control_panel.acquisition.update()


    def start_acquisition(self):
        '''
        Start digitiser acquisition.
        '''
        logging.info("Starting acquisition.")
        self.cmd_buffer.put(Command(CommandType.START))
        
    def stop_acquisition(self):
        '''
        Stop digitiser acquisition.
        '''
        logging.info("Stopping acquisition.")
        self.cmd_buffer.put(Command(CommandType.STOP))

    def shutdown(self):
        '''
        Carefully shut down acquisition and worker thread.
        '''
        logging.info("Shutting down controller.")
        self.cmd_buffer.put(Command(CommandType.EXIT))
        self.stop_event.set()
        self.worker.join(timeout=2)
        if self.worker.is_alive():
            logging.warning("AcquisitionWorker did not stop cleanly.")
        else:
            logging.info("Controller shutdown complete.")
