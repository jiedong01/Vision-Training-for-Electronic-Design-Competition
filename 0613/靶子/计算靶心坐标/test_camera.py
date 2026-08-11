# ===== test_camera.py =====
# 防误报版本：多条件验证 + 连续帧确认
from maix import camera, display, image
import cv2
import numpy as np

cam = camera.Camera(280, 320, image.Format.FMT_BGR888)
disp = display.Display()

# 连续帧计数器
stable_counter = 0
MAX_STABLE = 3  # 连续3帧检测到才输出
last_valid_center = None  # 上一帧有效坐标（用于平滑，可选）

def find_red_center(image):
    """
    返回 (cx, cy, confidence) 或 (None, None, 0)
    confidence 为0~1，表示可信度
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    
    # ----- 1. 霍夫圆检测（优先） -----
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                               param1=50, param2=20, minRadius=2, maxRadius=25)
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        # 取第一个圆（通常是最显著的）
        x, y, r = circles[0]
        # 半径在合理范围（2~25像素）且圆度好（霍夫本身就有圆度约束）
        if 2 <= r <= 25:
            # 计算圆形区域的面积（用于补充验证）
            # 简单返回高可信度
            return (x, y, 0.9)
    
    # ----- 2. 颜色提取 + 轮廓分析（备选） -----
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
    mask = cv2.bitwise_or(mask1, mask2)
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return (None, None, 0)
    
    # 筛选候选：面积范围 5~300 像素，圆度 >0.4
    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 5 or area > 300:  # 排除太小或太大（线条通常很大）
            continue
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity > 0.4:  # 圆度要求
            candidates.append((cnt, area, circularity))
    
    if candidates:
        # 按面积从小到大，优先选小的（更可能是点）
        candidates.sort(key=lambda x: x[1])
        best_cnt = candidates[0][0]
        M = cv2.moments(best_cnt)
        if M["m00"] != 0:
            cx = int(M["m10"]/M["m00"])
            cy = int(M["m01"]/M["m00"])
            # 计算可信度：面积越小、圆度越高，可信度越高
            area = candidates[0][1]
            circularity = candidates[0][2]
            confidence = min(1.0, (circularity * 2) * (1.0 - area/300))
            return (cx, cy, confidence)
    
    # 没有候选
    return (None, None, 0)

# 主循环
while True:
    img = cam.read()
    img_cv = image.image2cv(img, ensure_bgr=False, copy=False)
    
    cx, cy, conf = find_red_center(img_cv)
    
    # 如果可信度 > 0.5 则认为检测到有效目标
    if conf > 0.5:
        stable_counter += 1
    else:
        stable_counter = 0  # 重置计数器
    
    # 只有当连续帧数达到阈值时才输出坐标
    if stable_counter >= MAX_STABLE:
        # 输出坐标（可以使用上一帧的坐标，但我们直接用当前帧）
        print(f"X={cx},Y={cy}")
        # 画标记
        cv2.circle(img_cv, (cx, cy), 8, (0, 255, 0), 2)
        cv2.drawMarker(img_cv, (cx, cy), (0,255,0), cv2.MARKER_CROSS, 10, 2)
        cv2.putText(img_cv, f"X={cx} Y={cy}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        last_valid_center = (cx, cy)
    else:
        # 未达到稳定帧数，不输出坐标（但可以显示上一次有效位置？）
        # 这里我们显示 None 标识
        cv2.putText(img_cv, "Searching...", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        # 可打印 None
        # print("None")  # 如果不想打印太多可注释掉
    
    # 显示画面
    disp.show(image.cv2image(img_cv, bgr=True, copy=False))