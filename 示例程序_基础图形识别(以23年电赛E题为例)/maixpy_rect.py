from maix import camera, display, app, time, image

cam = camera.Camera(320, 240)
disp = display.Display()

# 过滤参数，根据实际目标大小调整
THRESHOLD = 60000   # 阈值越高，要求边缘越强，误检越少
MIN_W     = 50      # 矩形最小宽度（像素）
MIN_H     = 50      # 矩形最小高度（像素）
MIN_AREA  = 4000    # 矩形最小面积（像素²）

while not app.need_exit():
    img = cam.read()

    # 双边滤波：平滑噪点，同时保留边缘，减少 find_rects 误检
    img.bilateral(3)

    rects = img.find_rects(threshold=THRESHOLD)

    for rect in rects:
        w, h = rect.w(), rect.h()

        # 过滤太小的伪矩形（噪点、细小纹理）
        if w < MIN_W or h < MIN_H or w * h < MIN_AREA:
            continue

        x, y = rect.x(), rect.y()

        # 绿色边框
        img.draw_rect(x, y, w, h, image.Color.from_rgb(0, 255, 0), 2)

        # 蓝色角点
        for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            img.draw_circle(cx, cy, 5, image.Color.from_rgb(0, 0, 255), -1)

    disp.show(img)

