from queue import Queue, Empty
from threading import Thread, Event, Lock
import logging
import time
from core.commands import CommandType, Command
from felib.digitiser import Digitiser
from core.io import read_config_file

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
        '''
        Handles commands sent to AcquisitionWorker. Currently supports the commands:
            - CONNECT
            - START
            - STOP
            - EXIT
        '''
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
        '''
        Starts digitiser acquisition. First checks to see if there is a digitiser connected.
        If not already connected, connect using the config files. Finally, tell the digitiser
        to start acquisition.
        '''
        if self.digitiser is None:
            logging.info("No digitiser instance — reconnecting before start.")
            if self.dig_config is None or self.rec_config is None:
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
        '''
        Data acquisition hot loop. Hot loop runs until stop_event is set either manually
        or via the EXIT command.
        '''
        logging.info("AcquisitionWorker thread started.")
        try:
            while not self.stop_event.is_set():
                # Handle commands
                while True:
                    try:
                        cmd = self.cmd_buffer.get(timeout=0.01)
                        self.handle_command(cmd)
                    except Empty:   # exit cmd loop if cmd buffer is empty
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

                # to avoid busy digitiser - add software timeout as member variable
                time.sleep(1)

        except Exception as e:
            logging.exception(f"Fatal error in AcquisitionWorker: {e}")

        # when stop_event() is set, call destructor of digitiser inside cleanup()
        self.cleanup()
        logging.info("AcquisitionWorker thread exited cleanly.")

    def cleanup(self):
        '''
        Cleans up digitiser by calling stop_acquisition and its destructor. 
        '''
        if self.digitiser:
            if self.digitiser.isAcquiring:
                self.digitiser.stop_acquisition()
            del self.digitiser
            self.digitiser = None
        logging.info("Digitiser fully cleaned up after STOP.")


