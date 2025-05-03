import pandas as pd

import h5py
import ast
import configparser



def read_config_file(file_path  :  str) -> dict:
    '''
    Read config file and extract relevant information returned as a dictionary.
    
    Extracted explicitly from MULE:
    https://github.com/nu-ZOO/MULE/blob/abeab70/packs/core/io.py#L68

    Parameters
    ----------

    file_path (str)  :  Path to config file

    Returns
    -------

    arg_dict (dict)  :  Dictionary of relevant arguments for the pack
    '''
    # setup config parser
    config = configparser.ConfigParser()

    # read in arguments, require the required ones
    config.read(file_path)
    arg_dict = {}
    for section in config.sections():
        for key in config[section]:
            # the config should be written in such a way that the python evaluator
            # can determine its type
            #
            # we can setup stricter rules at some other time
            arg_dict[key] = ast.literal_eval(config[section][key])

    return arg_dict