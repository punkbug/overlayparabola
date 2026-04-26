import cv2
import numpy as np

def detect_points(img_bgra, canny_thresh1=50, canny_thresh2=150):
    img_bgr = cv2.cvtColor(np.array(img_bgra), cv2.COLOR_BGRA2BGR)
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    ball, hoop, dots = None, None, []

    # 1. 빨간 골대 (림의 정중앙 탐지 강화)
    l_r1, u_r1 = np.array([0, 130, 80]), np.array([10, 255, 255])
    l_r2, u_r2 = np.array([170, 130, 80]), np.array([180, 255, 255])
    m_r = cv2.bitwise_or(cv2.inRange(hsv, l_r1, u_r1), cv2.inRange(hsv, l_r2, u_r2))
    
    cnts_r, _ = cv2.findContours(m_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts_r:
        # 원형도와 면적을 고려하여 '림'에 해당하는 부분 탐지
        best_hoop = None
        max_score = -1
        for cnt in cnts_r:
            area = cv2.contourArea(cnt)
            if area < 20: continue
            
            peri = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * (area / (peri * peri)) if peri > 0 else 0
            # 면적이 적당하고 원형도가 높을수록 골대 림일 확률이 높음
            score = area * circularity
            if score > max_score:
                max_score = score
                best_hoop = cnt
        
        if best_hoop is not None:
            M = cv2.moments(best_hoop)
            if M["m00"] > 0: hoop = [int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])]

    # 2. 갈색 공 (좌상단 무시 로직 유지)
    l_b, u_b = np.array([5, 80, 40]), np.array([25, 255, 200])
    m_b = cv2.inRange(hsv, l_b, u_b)
    cnts_b, _ = cv2.findContours(m_b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts_b:
        cnts_b = sorted(cnts_b, key=cv2.contourArea, reverse=True)
        for cnt in cnts_b:
            if cv2.contourArea(cnt) > 40:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                    if cx < (w * 0.15) and cy < (h * 0.15): continue
                    ball = [cx, cy]; break

    # 3. 흰색 점선
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    _, d_mask = cv2.threshold(tophat, max(10, 100 - canny_thresh1), 255, cv2.THRESH_BINARY)
    cnts_d, _ = cv2.findContours(d_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts_d:
        if 2 <= cv2.contourArea(cnt) <= 150:
            M = cv2.moments(cnt)
            if M["m00"] > 0: dots.append([int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])])

    return {"ball": ball, "hoop": hoop, "dots": np.array(dots)}
