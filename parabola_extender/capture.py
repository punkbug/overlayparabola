import time
import mss
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from detector import detect_points
from fitter import ParabolaFitter

class CaptureWorker(QThread):
    # coeffs, debug_data(dict)
    result_ready = pyqtSignal(object, object)  
    status_changed = pyqtSignal(str)

    def __init__(self, region, fps=15):
        super().__init__()
        self.region = region
        self.fps = fps
        self.running = False
        self.fitter = ParabolaFitter()
        self.canny_params = (50, 150)

    def update_params(self, fps=None, alpha=None, canny=None):
        if fps: self.fps = fps
        if alpha: self.fitter.set_alpha(alpha)
        if canny: self.canny_params = canny

    def run(self):
        self.running = True
        with mss.mss() as sct:
            while self.running:
                start_time = time.time()
                
                img = sct.grab(self.region)
                
                # data = {"anchors": ..., "dots": ...}
                data = detect_points(img, *self.canny_params)
                
                coeffs = self.fitter.fit(data)
                
                if coeffs is not None:
                    # overlay.py에서 모든 점을 그릴 수 있게 data 통째로 전달
                    self.result_ready.emit(coeffs, data)
                    self.status_changed.emit("detecting")
                else:
                    self.result_ready.emit(None, None)
                    self.status_changed.emit("failed")
                
                elapsed = time.time() - start_time
                wait = max(0, (1 / self.fps) - elapsed)
                time.sleep(wait)
        
        self.status_changed.emit("stopped")

    def stop(self):
        self.running = False
