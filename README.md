<a href="https://github.com/jwaiton/CARP">
    <img src="assets/CARP.png" alt="CARP" style="display: block; margin: 0;"/>
</a>

#
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/) [![test_linux](https://github.com/jwaiton/CARP/actions/workflows/test_init_linux.yml/badge.svg)](https://github.com/jwaiton/CARP/actions) [![test_macOS](https://github.com/jwaiton/CARP/actions/workflows/test_init_macOS.yml/badge.svg)](https://github.com/jwaiton/CARP/actions) [![test_windows](https://github.com/jwaiton/CARP/actions/workflows/test_init_windows.yml/badge.svg)](https://github.com/jwaiton/CARP/actions)
### What is CARP?

**CARP** is a readout and acquisition program for CAEN digitisers (generation 1 and 2), using the [CAEN FELib](https://pypi.org/project/caen-felib/) python bindings and Qt6.

### Getting started

To initialise CARP, simply run `source setup.sh`.

CARP, like MULE uses a config based system. The configs consist of 2 components:

#### Digitiser settings
These consist of settings related to the connection type (USB, Optical, A4818), the digitiser in use (DT5730, etc).

#### Recording settings
These consist of settings related to the recording window, amount of time post trigger, etc.

#### Usage

To run CARP with a config, simply initialise CARP and run:
```carp config.conf```


