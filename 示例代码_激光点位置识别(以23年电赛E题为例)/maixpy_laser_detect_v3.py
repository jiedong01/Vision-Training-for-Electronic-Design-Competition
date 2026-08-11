'''
V3 帧差法 + HSV颜色掩膜双重过滤
核心思路：帧差找到"运动区域"后，还要验证该区域颜色是否为红色，两个条件同时满足才认定为激光点。
相比v2的改进：
  1. 双重过滤大幅减少干扰轮廓
  2. 面积过滤加了下限，排除单像素噪点
  3. 高斯模糊预处理，减少帧差噪声
  4. 修复了 M["m00"]==0 时的除零崩溃
'''

from maix import image, camera, display, app
import cv2
import numpy as np

cam = camera.Camera(320, 240)
disp = display.Display()

# ── 曝光调节 ──────────────────────────────────────────────
# 白色背景：激光功率小 → 适当加大曝光，让激光点更亮
# 黑色背景：激光功率大 → 减小曝光，避免背景反光干扰
# cam.exposure(5000)   # 取消注释并调整到合适值

# ── 红色激光点 HSV 范围 ───────────────────────────────────
# OpenCV HSV: H∈[0,180], S∈[0,255], V∈[0,255]
# 红色在色相轮上跨越0°两侧，需要两段范围
# 调参建议：先打印出激光点区域的 HSV 均值，再根据实际值微调
RED_HSV_LOW1  = np.array([  0, 120, 180])  # 红色低端 + 高饱和 + 高亮度
RED_HSV_HIGH1 = np.array([ 10, 255, 255])
RED_HSV_LOW2  = np.array([170, 120, 180])  # 红色高端
RED_HSV_HIGH2 = np.array([180, 255, 255])

# ── 形态学核 ─────────────────────────────────────────────
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

point_x, point_y = 0, 0
last_gray = None

while not app.need_exit():
    img = cam.read()
    img_cv = image.image2cv(img, False, False)  # RGB 格式

    # 高斯模糊降噪，再转灰度，减少帧差噪声
    img_blur = cv2.GaussianBlur(img_cv, (5, 5), 0)
    gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)

    if last_gray is None:
        last_gray = gray.copy()
        disp.show(img)
        continue

    # ── 帧差掩膜 ──────────────────────────────────────────
    diff = cv2.absdiff(gray, last_gray)
    _, mask_motion = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)  # 阈值适当调高
    mask_motion = cv2.dilate(mask_motion, kernel, iterations=2)

    # ── HSV 颜色掩膜（找红色高亮区域）────────────────────
    hsv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2HSV)
    mask_red = cv2.bitwise_or(
        cv2.inRange(hsv, RED_HSV_LOW1, RED_HSV_HIGH1),
        cv2.inRange(hsv, RED_HSV_LOW2, RED_HSV_HIGH2)
    )

    # ── 双重条件取交集 ────────────────────────────────────
    # 必须同时：① 相对上一帧有变化  ② 颜色是红色
    mask = cv2.bitwise_and(mask_motion, mask_red)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # ── 轮廓筛选 ──────────────────────────────────────────
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_contour = None
    best_area = 0
    for c in contours:
        area = cv2.contourArea(c)
        # 激光点面积范围：过滤单像素噪点(< 5)和大面积干扰物(> 400)
        if 5 < area < 400 and area > best_area:
            best_area = area
            best_contour = c

    if best_contour is not None:
        M = cv2.moments(best_contour)
        if M["m00"] != 0:  # 防止除零
            point_x = int(M["m10"] / M["m00"])
            point_y = int(M["m01"] / M["m00"])
            img.draw_cross(point_x, point_y, image.COLOR_BLUE, 8, 2)
            img.draw_string(point_x + 5, point_y, f'({point_x},{point_y})')

    last_gray = gray.copy()
    disp.show(img)
