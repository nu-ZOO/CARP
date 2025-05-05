import numpy as np
#from caen_felib import lib, device, error
from typing import Optional
from core.io import read_config_file

def generate_digitiser_uri(dig_gen           :  str,
                           con_type          :  str,
                           link_num          :  Optional[int] = 0,
                           conet_node        :  Optional[int] = 0,
                           vme_base_address  :  Optional[int] = 0,
                           dig_authority     :  Optional[str] = 'caen.internal',
                           ) -> str:
    """
    Generate a URI for the digitiser based on the provided scheme, authority, query, and path.

    Parameters:
    ----------

        dig_gen (str)           :  The digitiser generation (1 or 2)
        con_type (str)          :  The connection type (e.g., 'USB', 'VME', 'CONET')
        link_num (int)          :  The link number for the connection
        conet_node (int)        :  The CONET node number (default is 0)
        vme_base_address (int)  :  The VME base address (default is 0)
        dig_authority (str)     :  The authority for the digitiser (default is 'caen.internal')

    Returns:
    -------
        str: A URI string representing the digitiser connection.
    """

    return f'{dig_scheme}://{dig_authority}/{dig_path}?{dig_query}'

def connect_and_readout(dig_config  :  str,
                        rec_config  :  str
                        ) -> None:
    """
    Connect to the digitiser and read out data based on the provided configuration files.

    This lifts heavily from the dig1_demo_scope.py example provided by CAEN.
    https://github.com/caenspa/py-caen-felib

    Parameters:
    ----------
        dig_config (str)  :  Path to the digitiser configuration file.
        rec_config (str)  :  Path to the recording configuration file.

    Returns:
    -------
        None
    """

    # Load in configs
    dig_dict = read_config_file(dig_config)
    rec_dict = read_config_file(rec_config)

    # Get the digitiser URI
    dig_uri = generate_digitiser_uri(
        dig_gen=dig_dict.get(dig_gen),
        con_type=dig_dict.get(con_type),
        link_num=dig_dict.get(link_num, 0),
        conet_node=dig_dict.get(conet_node, 0),
        vme_base_address=dig_dict.get(vme_base_address, 0),
        dig_authority=dig_dict.get(dig_authority, 'caen.internal')
    )

    # Connect to the digitiser
    with device.connect(dig_uri) as dig:
        
        dig.cmd.RESET()

        # Extract board info
        n_ch     = int(dig.par.NUMCH.value)
        smp_rate = int(dig.par.ADC_SAMPLERATE.value) # in Msps
        ADCs     = int(dig.par.ADC_NBITS.value)

        sampling_period = int(1e3 / smp_rate) # in ns
        record_length   = rec_dict.get(record_length, 0) # in ns
        pre_trigger     = rec_dict.get(pre_trigger, 0) # in ns
        trig_type       = rec_dict.get(trig_type, 'SWTRG') # software, or based on channels and such. tbc 

        # Configure the digitiser
        dig.par.RECORDLENGTHT.value = f'{record_length}'
        dig.par.PRETRIGGERT.value = f'{pre_trigger}'
        dig.par.ACQTRIGGERSOURCE.value = trig_type

        # Compute record length in samples
        record_length = int(dig.par.RECORDLENGTHT.value)
        record_len    = record_length // sampling_period

        # Configure endpoint TO BE DONE