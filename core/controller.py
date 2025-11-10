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

from threading import Thread, Event, Lock
from enum import Enum, auto
from dataclasses import dataclass
from queue import Queue, Empty


class CommandType(Enum):
    START = 0
    STOP = 1
    CONNECT = auto()
    UPDATE = auto()
    CH_DISPLAY = auto()
    
@dataclass
class Command:
    type: CommandType
    args: tuple = ()


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

class AcquisitionWorker(Thread):
    '''
    Handles digitiser I/O in a background thread.

    This class is designed to be thread-safe and independent from Qt threading.
    All commands and data flow through thread-safe mechanisms (queue, locks, events).
    '''

    def __init__(self, cmd_buffer: Queue, display_buffer: Queue, stop_event: Event):
        super().__init__(daemon=True)
        self.digitiser = None
        self.stop_event = stop_event
        self.cmd_buffer = cmd_buffer
        self.display_buffer = display_buffer
        self.data_buffer = Queue()
        self.data_ready_callback = None  # set by Controller
        self.dig_config = None
        self.rec_config = None

    def enqueue_cmd(self, cmd_type: CommandType, *args):
        '''
        Global interface for Controller.
        '''
        self.cmd_buffer.put(Command(cmd_type, args))

    def handle_command(self, cmd: Command):
        logging.debug(f"Handling command: {cmd.type}")
        args = cmd.args
        try:
            match cmd.type:
                case CommandType.CONNECT:
                    self.connect_digitiser(*args)
                case CommandType.START:
                    self.start_acquisition()
                case CommandType.STOP:
                    self.cleanup()
                case CommandType.EXIT:
                    self.stop_event.set()
                case _:
                    logging.warning(f"Unknown command: {cmd.type}")
        except Exception as e:
            logging.exception(f"Command {cmd.type} failed: {e}")

    def start_acquisition(self):
        if not self.digitiser:
            logging.info("No digitiser instance — reconnecting before start.")
            if not (self.dig_config and self.rec_config):
                logging.error("No stored configuration — cannot reconnect digitiser.")
                return
            self.connect_digitiser(self.dig_config, self.rec_config)
        try:
            self.digitiser.start_acquisition()
            logging.info("Digitiser acquisition started successfully.")
        except Exception as e:
            logging.exception(f"Start acquisition failed: {e}")
    
    def connect_digitiser(self, dig_config, rec_config):
        '''
        Connect to digitiser with given configs.
        '''
        # cache configs
        self.dig_config = dig_config
        self.rec_config = rec_config

        # Load in configs
        dig_dict = read_config_file(dig_config)
        rec_dict = read_config_file(rec_config)

        if dig_dict is None:
            logging.error("Digitiser configuration file not found or invalid.")
            return

        self.digitiser = Digitiser(dig_dict)
        self.digitiser.connect()

        # once connected, configure recording setup
        if rec_dict is None:
            logging.warning("No recording configuration file provided.")
        else:
            if (self.digitiser is not None) and self.digitiser.isConnected:
                self.digitiser.configure(dig_dict, rec_dict)

    def run(self):
        logging.info("AcquisitionWorker thread started.")
        try:
            while not self.stop_event.is_set():
                # Handle commands
                while True:
                    try:
                        cmd = self.cmd_buffer.get(timeout=0.01)
                        self.handle_command(cmd)
                    except Empty:
                        break

                # Acquire data if running
                if self.digitiser and self.digitiser.isAcquiring:
                    try:
                        data = self.digitiser.acquire()
                        if data is None:
                            continue

                        # Non-blocking put to visual buffer
                        if self.display_buffer.full():
                            try:
                                self.display_buffer.get_nowait()  # discard oldest
                            except Empty:
                                pass

                        # Push to display buffer (etc.)
                        if not self.display_buffer.full():
                            self.display_buffer.put_nowait(data)

                        # Notify controller/UI
                        if self.data_ready_callback:
                            self.data_ready_callback()

                    except Exception as e:
                        logging.exception(f"Acquisition error: {e}")

                #time.sleep(1)

        except Exception as e:
            logging.exception(f"Fatal error in AcquisitionWorker: {e}")

        self.cleanup()
        logging.info("AcquisitionWorker thread exited cleanly.")

    def cleanup(self):
        if self.digitiser:
            if self.digitiser.isAcquiring:
                self.digitiser.stop_acquisition()
            del self.digitiser
            self.digitiser = None
        logging.info("Digitiser fully cleaned up after STOP.")


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
        self.lock       = Lock()

    def track(self, nbytes: int = 0):
        '''
        Tracker outputting the number of events that arrive per second
        '''
        with self.lock:
            self.events_ps += 1
            self.bytes_ps += nbytes

            t_check = time.perf_counter()
            if t_check - self.last_time >= 1.0:
                MB = self.bytes_ps / 1000000
                logging.info(f'|| {self.events_ps} events/sec || {MB:.2f} MB/sec ||')
                self.last_time = t_check
                self.bytes_ps = 0
                self.events_ps = 0
