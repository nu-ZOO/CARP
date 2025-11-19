import logging
import time
from threading import Lock

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
