# Installation: pip install -r requirements.txt
# Execution: python main.py

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from controls import ControlPanel, RegionSelector
from capture import CaptureWorker
from overlay import OverlayWindow

class ParabolaApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        self.region = None
        self.controls = ControlPanel()
        self.overlay = OverlayWindow()
        self.worker = None
        
        # Connect Signals
        self.controls.region_request.connect(self.start_region_selection)
        self.controls.start_requested.connect(self.start_capture)
        self.controls.stop_requested.connect(self.stop_capture)
        self.controls.params_changed.connect(self.update_parameters)
        self.controls.save_requested.connect(self.save_screenshot)
        
        self.controls.show()

    def start_region_selection(self):
        self.stop_capture()
        self.selector = RegionSelector()
        self.selector.region_selected.connect(self.on_region_selected)
        self.selector.show()
        self.selector.raise_()

    def on_region_selected(self, region):
        self.region = region
        self.controls.activateWindow()
        self.controls.raise_()

    def start_capture(self):
        if not self.region:
            QMessageBox.warning(self.controls, "Warning", "Please select a capture region first.")
            self.controls.btn_toggle.setChecked(False)
            self.controls.btn_toggle.setText("Start ▶")
            return
        
        # 오버레이 표시 (ToolTip 플래그가 있어 클릭을 가로채지 않고 위에 뜸)
        self.overlay.show()
        
        self.worker = CaptureWorker(self.region)
        self.worker.result_ready.connect(self.on_result)
        self.worker.status_changed.connect(self.controls.set_status)
        self.worker.start()

    def stop_capture(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
        
        self.overlay.update_data(None, None, None)
        self.overlay.hide()
        self.controls.set_status("stopped")

    def update_parameters(self, params):
        if "ext" in params:
            self.overlay.extend_percent = params["ext"] / 100.0
            self.overlay.update()
        if "color" in params:
            self.overlay.line_color = params["color"]
            self.overlay.update()
        
        if self.worker:
            fps = params.get("fps")
            alpha = params.get("alpha")
            canny_val = params.get("canny")
            canny = (canny_val, canny_val * 3) if canny_val else None
            self.worker.update_params(fps=fps, alpha=alpha, canny=canny)

    def on_result(self, coeffs, points):
        self.overlay.update_data(coeffs, points, self.region)
        # 감지 중일 때 오버레이가 항상 최상위인지 주기적으로 확인 (선택 사항)
        # self.overlay.raise_() 

    def save_screenshot(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "parabola_export.png")
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        pixmap.save(path, "PNG")
        QMessageBox.information(self.controls, "Saved", f"Screenshot saved to Desktop:\n{path}")

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = ParabolaApp()
    app.run()
