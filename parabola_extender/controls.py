import psutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSlider, QColorDialog, QFileDialog, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QColor, QPainter, QPen

class RegionSelector(QWidget):
    region_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        screen_geo = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geo)
        self.setCursor(Qt.CrossCursor)
        
        self.begin = None
        self.end = None
        self.is_selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        # 투명한 레이어 채우기
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1)) 
        
        if self.begin and self.end:
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.SolidLine))
            painter.setBrush(QColor(255, 0, 0, 40))
            rect = QRect(self.begin, self.end).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        if self.begin and self.end:
            rect = QRect(self.begin, self.end).normalized()
            if rect.width() > 10 and rect.height() > 10:
                region = {
                    "top": rect.y(),
                    "left": rect.x(),
                    "width": rect.width(),
                    "height": rect.height()
                }
                self.region_selected.emit(region)
                self.close()

class ControlPanel(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    region_request = pyqtSignal()
    params_changed = pyqtSignal(dict)
    save_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parabola Controls")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setFixedWidth(280)
        self.init_ui()
        
        self.cpu_timer = QTimer()
        self.cpu_timer.timeout.connect(self.update_cpu)
        self.cpu_timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_region = QPushButton("Select Region")
        self.btn_region.clicked.connect(self.region_request.emit)
        self.btn_toggle = QPushButton("Start ▶")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.clicked.connect(self.on_toggle)
        btn_layout.addWidget(self.btn_region)
        btn_layout.addWidget(self.btn_toggle)
        layout.addLayout(btn_layout)

        self.lbl_status = QLabel("Status: Stopped ●")
        self.lbl_status.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        layout.addLayout(self.create_slider("FPS", 1, 30, 15, "fps"))
        layout.addLayout(self.create_slider("Extension %", 20, 300, 100, "ext"))
        layout.addLayout(self.create_slider("Smoothing", 1, 10, 3, "alpha"))
        layout.addLayout(self.create_slider("Canny", 10, 255, 50, "canny"))

        util_layout = QHBoxLayout()
        self.btn_color = QPushButton("Color")
        self.btn_color.clicked.connect(self.pick_color)
        self.btn_save = QPushButton("Save PNG")
        self.btn_save.clicked.connect(self.save_requested.emit)
        util_layout.addWidget(self.btn_color)
        util_layout.addWidget(self.btn_save)
        layout.addLayout(util_layout)

        self.lbl_cpu = QLabel("CPU: 0%")
        layout.addWidget(self.lbl_cpu)
        self.setLayout(layout)

    def create_slider(self, label, min_v, max_v, default_v, key):
        v_layout = QVBoxLayout()
        lbl = QLabel(f"{label}: {default_v if key != 'alpha' else default_v/10.0}")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(default_v)
        slider.valueChanged.connect(lambda v: self.on_slider_change(lbl, label, v, key))
        v_layout.addWidget(lbl)
        v_layout.addWidget(slider)
        return v_layout

    def on_slider_change(self, lbl, prefix, val, key):
        display_val = val / 10.0 if key == "alpha" else val
        lbl.setText(f"{prefix}: {display_val}")
        self.params_changed.emit({key: display_val})

    def on_toggle(self):
        if self.btn_toggle.isChecked():
            self.btn_toggle.setText("Stop ■")
            self.start_requested.emit()
        else:
            self.btn_toggle.setText("Start ▶")
            self.stop_requested.emit()

    def set_status(self, status):
        if status == "detecting":
            self.lbl_status.setText("Status: Detecting ●")
            self.lbl_status.setStyleSheet("color: #00FF88; font-weight: bold;")
        elif status == "failed":
            self.lbl_status.setText("Status: Failed ●")
            self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.lbl_status.setText("Status: Stopped ●")
            self.lbl_status.setStyleSheet("color: gray; font-weight: bold;")

    def update_cpu(self):
        self.lbl_cpu.setText(f"CPU: {psutil.cpu_percent()}%")

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid(): self.params_changed.emit({"color": color})
