'''
jwaiton 05/25

Different UI elements for the application.
'''
import random

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


class StatsBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Stats", parent = parent)

        self.fps_label = QLabel("FPS: 0")

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Refresh Rate:"))
        layout.addWidget(self.fps_label)

class ConnectDigitiser(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Connect Digitiser", parent = parent)

        self.connect        = QPushButton("Connect")
        self.combobox_ports = QComboBox()
        self.reset_con        = QPushButton("Reset")

        layout.addWidget(self.connect)
        layout.addWidget(self.combobox_ports)
        layout.addWidget(self.reset_con)

        self.refresh.clicked.connect(self.reset_connection)
        self.refresh.clicked.connect(self.connect)
    
    def reset_connection(self):
        
        self.combobox_ports.clear()
        # here instead add the digitiser type connected, num channels perhaps
        # for now, just add some random ports
        self.combobox_ports.addItems([f"Port {random.randint(0,10)}", f"Port {random.randint(0,10)}", f"Port {random.randint(0,10)}"])
    
    def connect(self):

        # if not connected, try to connect.
        self.connect_digitiser()
