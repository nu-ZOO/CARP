# location for defining all the data formats of the differing firmwares

def DPP(nch, record_length):
    '''
    DPP-DSD format
    nch - number of channels
    '''
    
    # Configure endpoint
    data_format = [
        {
            'name': 'CHANNEL',
            'type': 'U8',
            'dim' : 0,
        },
        {
            'name': 'TIMESTAMP',
            'type': 'U64',
            'dim': 0,
        },
        {
            'name': 'ENERGY',
            'type': 'U16',
            'dim': 0,
        },
        {
            'name': 'ANALOG_PROBE_1',
            'type': 'I16',
            'dim': 1,
            'shape': [record_length],
        },
        {
            'name': 'ANALOG_PROBE_1_TYPE',
            'type': 'I32',
            'dim': 0,
        },
        {
            'name': 'DIGITAL_PROBE_1',
            'type': 'U8',
            'dim': 1,
            'shape': [record_length],
        },
        {
            'name': 'DIGITAL_PROBE_1_TYPE',
            'type': 'I32',
            'dim': 0,
        },
        {
            'name': 'WAVEFORM_SIZE',
            'type': 'SIZE_T',
            'dim': 0,
        }
    ]

    return data_format