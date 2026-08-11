from maix import image, camera, display, app
import cv2

cam  = camera.Camera(320, 240)
disp = display.Display()

# CLAHE：自适应对比度增强，专门用于低对比度场景（铅笔线/白底）
clahe   = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

while not app.need_exit():
    img     = cam.read()
    img_raw = image.image2cv(img, copy=False)

    # 转灰度
    gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)

    # CLAHE 增强局部对比度，铅笔细线会变得更明显
    enhanced = clahe.apply(gray)

    # 自适应二值化：铅笔（深色）→ 白色；白色背景 → 黑色
    # blockSize=21 适合线宽 1mm 的细线；C=3 容忍轻微噪点
    thresh = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,
        blockSize=21, C=1
    )

    # 膨胀：让 1px 细线变粗，同时闭合角点处的断口
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    # 只找最外层轮廓，避免内部噪点干扰
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_approx = None
    best_peri   = 0

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        if peri < 200:          # 过滤短小噪点轮廓
            continue
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        # 只要四边形，且取周长最大的那个（即目标正方形）
        if len(approx) == 4 and peri > best_peri:
            best_approx = approx
            best_peri   = peri

    if best_approx is not None:
        # 绿色边框
        cv2.drawContours(img_raw, [best_approx], 0, (0, 255, 0), 2)
        # 蓝色角点
        for point in best_approx:
            x, y = point.ravel()
            cv2.circle(img_raw, (x, y), 6, (255, 0, 0), -1)

    img_show = image.cv2image(img_raw, copy=False)
    disp.show(img_show)