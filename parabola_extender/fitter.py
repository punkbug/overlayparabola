import numpy as np

class ParabolaFitter:
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.prev_coeffs = None
        self.fail_count = 0
        self.max_fail = 15 # 데이터가 안 보여도 15프레임(약 1초) 동안은 마지막 곡선 유지

    def fit(self, data):
        if data is None:
            self.fail_count += 1
            return self.prev_coeffs if self.fail_count <= self.max_fail else None
            
        anchors = data.get("anchors", np.array([]))
        dots = data.get("dots", np.array([]))
        
        all_pts = []
        weights = []
        
        # 1. 골대와 공 (절대적 기준점)
        if len(anchors) > 0:
            for p in anchors:
                all_pts.append(p)
                weights.append(100.0) # 가중치 100배 (반드시 지나야 함)
        
        # 2. 흰색 점선들 (곡선 흐름)
        if len(dots) > 0:
            for p in dots:
                all_pts.append(p)
                weights.append(1.0)

        # 회귀를 위한 최소 점 개수 확인
        if len(all_pts) < 3:
            self.fail_count += 1
            return self.prev_coeffs if self.fail_count <= self.max_fail else None
            
        self.fail_count = 0
        all_pts = np.array(all_pts)
        x = all_pts[:, 0]
        y = all_pts[:, 1]
        
        try:
            # 가중 회귀 (Weighted Polynomial Fit)
            coeffs = np.polyfit(x, y, 2, w=weights)
            
            if self.prev_coeffs is None:
                self.prev_coeffs = coeffs
                return coeffs
            
            # EMA (평활화)
            smoothed = self.alpha * coeffs + (1 - self.alpha) * self.prev_coeffs
            self.prev_coeffs = smoothed
            return smoothed
        except Exception:
            return self.prev_coeffs

    def set_alpha(self, alpha):
        self.alpha = alpha
