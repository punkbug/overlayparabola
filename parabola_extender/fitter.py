import numpy as np

class ParabolaFitter:
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.prev_coeffs = None
        self.fail_count = 0
        self.mode = "detect" 

    def set_mode(self, mode):
        self.mode = mode
        self.prev_coeffs = None

    def fit(self, data):
        if data is None:
            self.fail_count += 1
            return self.prev_coeffs if self.fail_count <= 10 else None
            
        ball = data.get("ball")
        hoop = data.get("hoop")
        dots = data.get("dots", [])
        
        if self.mode == "fixed":
            if ball is not None and hoop is not None:
                p1, p2 = np.array(hoop), np.array(ball)
                mid_x = (p1[0] + p2[0]) / 2
                # 높이를 한 번 더 2/3로 낮춤 (0.4 -> 0.26)
                peak_y = min(p1[1], p2[1]) - abs(p1[0] - p2[0]) * 0.26
                
                x = np.array([p1[0], mid_x, p2[0]])
                y = np.array([p1[1], peak_y, p2[1]])
                try:
                    coeffs = np.polyfit(x, y, 2)
                    self.prev_coeffs = coeffs
                    return coeffs
                except: return self.prev_coeffs
            return self.prev_coeffs

        all_pts, weights = [], []
        if ball is not None:
            all_pts.append(ball); weights.append(500.0)
        if len(dots) > 0:
            for p in dots: all_pts.append(p); weights.append(1.0)

        if len(all_pts) < 3:
            self.fail_count += 1
            return self.prev_coeffs if self.fail_count <= 5 else None
            
        self.fail_count = 0
        all_pts = np.array(all_pts)
        try:
            coeffs = np.polyfit(all_pts[:, 0], all_pts[:, 1], 2, w=weights)
            if self.prev_coeffs is None: self.prev_coeffs = coeffs; return coeffs
            smoothed = self.alpha * coeffs + (1 - self.alpha) * self.prev_coeffs
            self.prev_coeffs = smoothed
            return smoothed
        except: return self.prev_coeffs

    def set_alpha(self, alpha):
        self.alpha = alpha
