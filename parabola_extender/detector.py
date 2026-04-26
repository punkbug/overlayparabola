import cv2
import numpy as np

def detect_points(img_bgra, canny_thresh1=50, canny_thresh2=150):
    img_bgr = cv2.cvtColor(np.array(img_bgra), cv2.COLOR_BGRA2BGR)
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    ball_point = None
    dot_points = []

    # --- [1] 갈색 공 탐지 (우측 끝점) ---
    lower_brown = np.array([5, 80, 40])
    upper_brown = np.array([25, 255, 200])
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
    cnts_b, _ = cv2.findContours(mask_brown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts_b:
        best = max(cnts_b, key=cv2.contourArea)
        if cv2.contourArea(best) > 50:
            M = cv2.moments(best)
            if M["m00"] > 0:
                ball_point = [int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])]

    # --- [2] 검정 테두리가 있는 흰색 점 탐지 ---
    # 1. 탑햇 변환으로 주변보다 밝은 작은 점들 강조
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    
    # 2. 이진화
    _, dot_mask = cv2.threshold(tophat, 40, 255, cv2.THRESH_BINARY)
    
    # 3. 윤곽선 분석 (원형도 체크)
    cnts_d, _ = cv2.findContours(dot_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts_d:
        area = cv2.contourArea(cnt)
        if 5 <= area <= 300:
            peri = cv2.arcLength(cnt, True)
            if peri == 0: continue
            circularity = 4 * np.pi * (area / (peri * peri))
            
            if circularity > 0.6:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                    
                    # 주변에 검정색 테두리가 있는지 확인
                    y_start, y_end = max(0, cy-5), min(h, cy+5)
                    x_start, x_end = max(0, cx-5), min(w, cx+5)
                    roi = gray[y_start:y_end, x_start:x_end]
                    if roi.size > 0 and np.min(roi) < 100:
                        dot_points.append([cx, cy])

    if not dot_points and not ball_point:
        return None
        
    return {"ball": ball_point, "dots": np.array(dot_points)}
