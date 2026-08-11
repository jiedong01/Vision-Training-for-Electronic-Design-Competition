from maix import camera, display, image
import math

W = 320
H = 240

cam = camera.Camera(W, H)
disp = display.Display()

thresholds = [[0, 41, -36, 28, -128, 96]]


# =========================
#  你的弯曲巡线，保留
# =========================
def track_smooth_lines(img, th):

    pts = []
    step = 8
    last_x = -1

    for y in range(0, H, step):

        roi = img.crop(0, y, W, step)

        blobs = roi.find_blobs(th, pixels_threshold=60, area_threshold=60)

        if blobs:

            b = max(blobs, key=lambda x: x.pixels())
            cx = b.cx()

            if last_x == -1:
                last_x = cx
            else:
                cx = int(last_x * 0.6 + cx * 0.4)
                last_x = cx

            pts.append((cx, y + b.cy()))

    return pts


# =========================
# 模拟 regression 的 theta / rho
# =========================
def calc_theta_rho(pts):

    if len(pts) < 2:
        return 0, 0

    # 用所有点做一个简单拟合：x = k * y + b
    n = len(pts)

    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_yy = 0

    for x, y in pts:
        sum_x += x
        sum_y += y
        sum_xy += x * y
        sum_yy += y * y

    den = n * sum_yy - sum_y * sum_y

    if den == 0:
        return 0, 0

    k = (n * sum_xy - sum_x * sum_y) / den

    # theta：相对竖直方向的偏转角
    theta = int(math.degrees(math.atan(k)))

    # rho：这里模拟成底部偏离中心的距离
    b = (sum_x - k * sum_y) / n
    bottom_x = int(k * (H - 1) + b)
    rho = bottom_x - W // 2

    return theta, rho


# =========================
# loop
# =========================
while True:

    img = cam.read().copy()

    pts = track_smooth_lines(img, thresholds)

    # 画弯曲轨迹
    for i in range(len(pts) - 1):

        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]

        img.draw_line(x1, y1, x2, y2, image.COLOR_GREEN, 2)

    #  注意：theta/rho 只在这里画一次，不放进 for 里面
    if len(pts) >= 2:
        theta, rho = calc_theta_rho(pts)
        img.draw_string(
            0,
            0,
            "theta: " + str(theta) + ", rho: " + str(rho),
            image.COLOR_BLUE
        )
    else:
        img.draw_string(
            0,
            0,
            "no line",
            image.COLOR_BLUE
        )

    disp.show(img)