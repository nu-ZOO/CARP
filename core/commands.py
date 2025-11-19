from enum import Enum, auto
from dataclasses import dataclass

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

