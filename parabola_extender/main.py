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
        self.controls.mode_toggled.connect(self.on_mode_toggled)
        
        self.controls.show()

    def on_mode_toggled(self, mode):
        if self.worker:
            self.worker.fitter.set_mode(mode)

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
        
        self.overlay.show()
        self.worker = CaptureWorker(self.region)
        # 초기 모드 설정
        initial_mode = "fixed" if self.controls.btn_mode.isChecked() else "detect"
        self.worker.fitter.set_mode(initial_mode)
        
        self.worker.result_ready.connect(self.on_result)
        self.worker.status_changed.connect(self.controls.set_status)
        self.worker.start()

    def stop_capture(self):
        if self.worker:
            self.worker.stop(); self.worker.wait(); self.worker = None
        self.overlay.update_data(None, None, None)
        self.overlay.hide(); self.controls.set_status("stopped")

    def update_parameters(self, params):
        if "ext" in params: self.overlay.update(); # overlay internally uses its own extend value but we sync it
        if "color" in params: self.overlay.line_color = params["color"]; self.overlay.update()
        if self.worker:
            self.worker.update_params(fps=params.get("fps"), alpha=params.get("alpha"), canny=params.get("canny"))

    def on_result(self, coeffs, data):
        self.overlay.update_data(coeffs, data, self.region)

    def save_screenshot(self):
        path = os.path.join(os.path.expanduser("~"), "Desktop", "parabola_export.png")
        QApplication.primaryScreen().grabWindow(0).save(path, "PNG")
        QMessageBox.information(self.controls, "Saved", f"Saved to Desktop")

    def run(self): sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = ParabolaApp(); app.run()
