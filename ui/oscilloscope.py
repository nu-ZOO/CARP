'''
Oscilloscope GUI using PyQt6 and PyQtGraph.

Copied extensively from wicope:
https://github.com/diepala/wicope/
'''

import sys
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
from PySide6 import QtCore, QtGui
import pyqtgraph as pg

from ui import elements




class ControlPanel(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller

        self.setFrameShape(QFrame.StyledPanel)

        self.stats_box = elements.StatsBox()

        self.layout = QVBoxLayout()
        self.layout.addStretch()
        self.setLayout(self.layout)


class OscilloScopeScreen(pg.PlotWidget):
    def __init__(self, parent = None, plotItem = None, **kwargs):
        super().__init__(parent=parent, background='w', plotItem=plotItem, **kwargs)
        
        styles = {'color': 'k', 'font-size': '12px'}
        self.setLabel('left', 'Voltage (V)', **styles)
        self.setLabel('bottom', 'Time (s)', **styles)

        self.showGrid(x = True, y = True)
        self.setXRange(0, 1, padding = 0.02)
        self.setYRange(0, 5, padding = 0.02)

        self.pen_ch1 = pg.mkPen(color = "b", width = 1)

        self.plot_ch([0,1], [0,0])
    
    def plot_ch(self, x, y, ch = 1):
        self.data_line_ch = self.plot(x, y, pen=self.pen_ch1)

    def update_ch(self, x, y, ch = 1):
        self.data_line_ch.setData(x, y)


class MainWindow(QMainWindow):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define interactivity through controller
        self.controller = controller
        
        self.setupUI()
    
    def setupUI(self):
        self.setWindowTitle("CAEN Acqusition and Readout Program (CARP)")
        
        self.screen        = OscilloScopeScreen()
        self.control_panel = ControlPanel(self.controller)

        self.content_layout = QHBoxLayout()
        self.content_layout.addWidget(self.screen)
        self.content_layout.addWidget(self.control_panel)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.content_layout)


def init():
    '''
    Testing initialisation of the GUI
    '''
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    init()