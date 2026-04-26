import numpy as np
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | 
                            Qt.WindowTransparentForInput | Qt.ToolTip | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(QApplication.primaryScreen().geometry())
        
        self.coeffs = None
        self.region = None 
        self.line_color = QColor(0, 255, 136)

    def update_data(self, coeffs, data, region):
        self.coeffs = coeffs
        self.region = region
        self.update()

    def paintEvent(self, event):
        if self.coeffs is None or self.region is None:
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(self.rect(), Qt.transparent)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        a, b, c = self.coeffs
        rx, ry = self.region['left'], self.region['top']
        rw = self.region['width']

        x_start = -rw * 1.5 
        x_end = rw + 100

        def get_screen_pt(lx):
            return QPointF(rx + lx, ry + (a*lx**2 + b*lx + c))

        x_vals = np.linspace(x_start, x_end, 500)
        path_pts = [get_screen_pt(x) for x in x_vals if -500 < (a*x**2 + b*x + c) < 1500]

        if len(path_pts) < 2: return

        painter.setPen(QPen(QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), 60), 10, Qt.SolidLine, Qt.RoundCap))
        for j in range(len(path_pts)-1): painter.drawLine(path_pts[j], path_pts[j+1])
        
        painter.setPen(QPen(self.line_color, 3, Qt.SolidLine, Qt.RoundCap))
        for j in range(len(path_pts)-1): painter.drawLine(path_pts[j], path_pts[j+1])
