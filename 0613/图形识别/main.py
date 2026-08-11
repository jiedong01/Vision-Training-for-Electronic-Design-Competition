from maix import camera, display, image, time
import cv2
import numpy as np

# ========== 颜色阈值（HSV） ==========
# 红色分为两个区间，合并判断
COLOR_RANGES = {
    "blue":  ([95, 43, 61], [125, 221, 153]),   # 
    "red1":  ([0, 100, 100], [10, 255, 255]),   # 红色区间1
    "red2":  ([163, 100, 100], [180, 255, 255]),# 红色区间2
    "black": ([0, 0, 0], [180, 249, 99]),
}

def get_color_from_contour(hsv_img, contour, sample_step=3):
    """
    从轮廓边界采样颜色，并计算中位数（更鲁棒）
    返回颜色名称或None
    """
    if len(contour) == 0:
        return None
    points = contour.reshape(-1, 2)
    sampled = points[::sample_step]
    if len(sampled) == 0:
        return None
    h_vals, s_vals, v_vals = [], [], []
    h, w = hsv_img.shape[:2]
    for (x, y) in sampled:
        if 0 <= x < w and 0 <= y < h:
            h_vals.append(hsv_img[y, x, 0])
            s_vals.append(hsv_img[y, x, 1])
            v_vals.append(hsv_img[y, x, 2])
    if not h_vals:
        return None
    # 使用中位数减少异常值影响
    h_med = np.median(h_vals)
    s_med = np.median(s_vals)
    v_med = np.median(v_vals)
    # 判断颜色：先检查红色两个区间（合并）
    # 红色1
    if (0 <= h_med <= 10 or 163 <= h_med <= 180) and s_med >= 100 and v_med >= 100:
        return "red"
    # 蓝色
    if 95 <= h_med <= 125 and s_med >= 43 and v_med >= 61:
        return "blue"
    # 黑色
    if s_med <= 249 and v_med <= 99:
        return "black"
    return None

# ========== 初始化 ==========
cam = camera.Camera(320, 240)
disp = display.Display()

while True:
    img = cam.read()
    if img is None:
        continue

    cv_img = image.image2cv(img, copy=True)
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # ---- 二值化 + 轮廓检测 ----
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 150:
            continue

        # 从轮廓边界提取颜色
        color_name = get_color_from_contour(hsv, cnt)
        if color_name is None:
            continue

        # 额外校验：如果是圆形且面积较小，检查内部颜色是否一致（防止空心圆误判）
        # 先计算圆形度
        peri = cv2.arcLength(cnt, True)
        if peri == 0:
            continue
        circularity = 4 * np.pi * area / (peri * peri)
        # 如果是圆形但内部大部分是背景色，可能误判，我们忽略（但可选项）
        # 这里不额外处理，因为边界采样已经足够

        # 形状判断
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        vertices = len(approx)

        shape_name = ""
        color_outline = (0, 255, 255)  # 黄色

        if vertices == 4:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h) if h > 0 else 1
            if 0.8 <= aspect_ratio <= 1.2 and area > 0.8 * w * h:
                shape_name = "Square"
            else:
                shape_name = "Rectangle"
            color_outline = (0, 255, 255)
        elif vertices >= 6:
            if circularity > 0.6:
                shape_name = "Circle"
                color_outline = (0, 165, 255)  # 橙色
            else:
                continue   # 不是圆形，跳过

        if shape_name:
            cv2.drawContours(cv_img, [cnt], -1, color_outline, 2)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(cv_img, (cx, cy), 5, (0, 0, 255), -1)
                x, y, w, h = cv2.boundingRect(cnt)
                label = f"{color_name} {shape_name}"
                cv2.putText(cv_img, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_outline, 1)
                print(f"形状: {label}, 中心: ({cx}, {cy})")

    # ---- 显示 ----
    img_show = image.cv2image(cv_img, copy=False)
    disp.show(img_show)
    time.sleep_ms(1)