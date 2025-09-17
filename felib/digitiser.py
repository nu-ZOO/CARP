'''
jwaiton 05/25

Class(es) to handle the digitiser connection and acquisition.
'''
import logging
from typing import Optional

from felib.dig1_utils import generate_digitiser_uri

from caen_felib import lib, device, error


class Digitiser():
    def __init__(self, dig_dict : dict):
        '''
        Create the digitiser object and generate the URI
        needed to connect.
        '''
        self.dig_dict = dig_dict
        self.dig_name = dig_dict.get('dig_name')
        self.dig_gen = int(dig_dict.get('dig_gen'))

        # check for debugger
        if self.dig_name == 'debug':
            logging.debug('Debugging mode enabled. Digitiser will fake connection')

        if self.dig_gen == 1:
            self.con_type = dig_dict.get('con_type')
            self.link_num = int(dig_dict.get('link_num', 0))
            self.conet_node = int(dig_dict.get('conet_node', 0))
            self.vme_base_address = dig_dict.get('vme_base_address', 0)
            self.dig_authority = dig_dict.get('dig_authority', 'caen.internal')
        elif self.dig_gen == 2:
            # not implemented yet, raise error
            logging.error("Digitiser generation 2 not implemented yet.")
            #raise NotImplementedError("Digitiser generation 2 not implemented yet.")
        else:
            logging.error("Invalid digitiser generation specified in the configuration.")
            #raise ValueError("Invalid digitiser generation specified in the configuration.")
        
        self.URI = self.generate_uri()
        self.isAcquiring = False
        self.isConnected = False

    def generate_uri(self):
        '''
        Generate the URI needed to connect to the digitiser.
        This is a wrapper for the generate_digitiser_uri function.
        '''
        # generate URI for each generation
        if self.dig_gen == 1:
            return generate_digitiser_uri(
                dig_gen=self.dig_gen,
                con_type=self.con_type,
                link_num=self.link_num,
                conet_node=self.conet_node,
                vme_base_address=self.vme_base_address,
                dig_authority=self.dig_authority
            )
        elif self.dig_gen == 2:
            # not implemented yet, raise error
            # you should never reach this code
            logging.error("Digitiser generation 2 not implemented yet.")
            #raise NotImplementedError("Digitiser generation 2 not implemented yet.")
        else:
            logging.error("Invalid digitiser generation specified in the configuration.")
            #raise ValueError("Invalid digitiser generation specified in the configuration.")
        

    def connect(self):
        '''
        Connect to the digitiser using the generated URI.
        '''
        
        logging.info(f'Attemping connection to digitiser {self.dig_name} at {self.URI}.')
        
        # fake connection for debugging
        if self.dig_name == 'debug':
            self.dig = None
            self.isConnected = True
            self.dig_info = {
                'n_ch'        : 4,
                'sample_rate' : 1000,
                'ADCs'        : 12,
                'firmware'    : 'debug',
            }
            logging.info(f'Digitiser connected in debug mode.\n{self.dig_info}')
            return None

        try:
            self.dig = device.connect(self.URI)
            self.dig.cmd.RESET()
            self.isConnected = True
            # extract relevant information from the digitiser
            self.dig_info = {
                'n_ch'        : int(self.dig.par.NUMCH.value),
                'sample_rate' : float(self.dig.par.ADC_SAMPLRATE.value),
                'ADCs'        : int(self.dig.par.ADC_NBIT.value),
                'firmware'    : self.dig.par.FWTYPE.value,
            }
            logging.info(f'Digitiser connected.\n{self.dig_info}')
        except Exception as e:
            logging.exception(f"Failed to connect to digitiser.")
            self.dig = None
            return None
            #raise ConnectionError(f"Failed to connect to the digitiser.\n{e}")
        finally:
            # close the connection if it exists
            if self.dig is not None:
                self.dig.close()


    def configure(self, rec_dict : dict):
                  #record_length: Optional[int] = 0,
                  #pre_trigger: Optional[int] = 0,
                  #trigger_level: Optional[str] = 'SWTRG'):
        '''
        Configure the digitiser with the provided settings and calibrate it.
        '''        

        self.record_length = rec_dict.get('record_length')
        self.pre_trigger   = rec_dict.get('pre_trigger')
        self.trigger_mode  = rec_dict.get('trigger_mode')

        try:

            self.dig.par.RECLEN.value = f'{self.record_length}'

            if self.trigger_mode == 'SWTRIG':
                self.dig.par.TRG_SW_ENABLE.value = 'TRUE'
                self.dig.par.STARTMODE.value = 'START_MODE_SW'

            # configure channels
            for i, ch in enumerate(self.dig.ch):
                ch.par.CH_ENABLED.value = 'TRUE' if i == 0 else 'FALSE' # only channel 0 atm
                ch.par.CH_PRETRG.value = f'{self.pre_trigger}'

            #self.dig.par.PRETRIGGERT.value = f'{self.pre_trigger}'
            #self.dig.par.ACQTRIGGERSOURCE.value = self.triggerlevel

            # if DPP, need to specify that you're looking at waveforms specifically.
            if self.dig.par.FWTYPE == 'DPP':
                self.dig.par.WAVEFORMS.value = 'TRUE'
            logging.info(f"Digitiser configured with record length {self.record_length}, pre-trigger {self.pre_trigger}, trigger level {self.triggerlevel}.")
        except Exception as e:
            logging.exception(f"Failed to configure recording parameters.\n{e}")


        try:
            self.dig.cmd.CALIBRATEADC()
            logging.info("Digitiser calibrated.")
        except Exception as e:
            logging.exception(f"Failed to calibrate digitiser.\n{e}")
            #raise RuntimeError(f"Failed to calibrate digitiser.\n{e}")


    def start_acquisition(self):
        '''
        Start the digitiser acquisition.
        '''
        self.isAcquiring = True
        #try:
            #self.dig.cmd.START()
            #self.collect = True    
            #print("Digitiser acquisition started.")
        #except Exception as e:
        #    raise RuntimeError(f"Failed to start digitiser acquisition.\n{e}")
             #self.collect = True
        
    
    def stop_acquisition(self):
        '''
        Stop the digitiser acquisition.
        '''
        #self.dig.cmd.STOP() # This in reality looks like dig.cmd.DISARMACQUISITION()
        self.isAcquiring = False
        logging.info("Digitiser acquisition stopped.")


    def __del__(self):
        '''
        Destructor for the digitiser object.
        '''
        if self.isAcquiring:
            self.stop_acquisition()
        if hasattr(self, 'dig') and self.dig is not None:
            logging.info("Closing digitiser connection.")
            self.dig.close()