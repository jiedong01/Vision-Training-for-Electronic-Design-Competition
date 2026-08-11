from maix import image, camera, display
import math

cam = camera.Camera()
disp = display.Display()

families = image.ApriltagFamilies.TAG36H11
x_scale = cam.width() / 160
y_scale = cam.height() / 120

FONT_SCALE = 1.2          # 字号适中，可根据屏幕调整
LINE_HEIGHT = int(22 * FONT_SCALE)

while 1:
    img = cam.read()
    new_img = img.resize(160, 120)
    apriltags = new_img.find_apriltags(families=families)

    for a in apriltags:
        # ---- 映射坐标 ----
        corners = a.corners()
        for i in range(4):
            corners[i][0] = int(corners[i][0] * x_scale)
            corners[i][1] = int(corners[i][1] * y_scale)
        x = int(a.x() * x_scale)
        y = int(a.y() * y_scale)
        w = int(a.w() * x_scale)
        h = int(a.h() * y_scale)

        # ---- 画框 ----
        for i in range(4):
            img.draw_line(corners[i][0], corners[i][1],
                          corners[(i + 1) % 4][0], corners[(i + 1) % 4][1],
                          image.COLOR_RED)

        # ---- 屏幕显示（Euler 分三行，Z 单独一行） ----
        text_x = x + w + 10
        text_y = y

        # ID
        img.draw_string(text_x, text_y, f"ID: {a.id()}", image.COLOR_RED, scale=FONT_SCALE)
        text_y += LINE_HEIGHT

        # 坐标
        img.draw_string(text_x, text_y, f"Pos: ({x}, {y})", image.COLOR_RED, scale=FONT_SCALE)
        text_y += LINE_HEIGHT

        # 欧拉角：三个轴分别单独一行
        euler_x = math.degrees(a.x_rotation())
        euler_y = math.degrees(a.y_rotation())
        euler_z = math.degrees(a.z_rotation())
        img.draw_string(text_x, text_y, f"Ex: {euler_x:.1f} deg", image.COLOR_RED, scale=FONT_SCALE)
        text_y += LINE_HEIGHT
        img.draw_string(text_x, text_y, f"Ey: {euler_y:.1f} deg", image.COLOR_RED, scale=FONT_SCALE)
        text_y += LINE_HEIGHT
        img.draw_string(text_x, text_y, f"Ez: {euler_z:.1f} deg", image.COLOR_RED, scale=FONT_SCALE)
        text_y += LINE_HEIGHT

        # Z 平移（深度）
        img.draw_string(text_x, text_y, f"Z: {a.z_translation():.3f}", image.COLOR_RED, scale=FONT_SCALE)

        # ---- 终端输出 ----
        deg_rot = math.degrees(a.rotation())
        print("=" * 40)
        print(f"ID: {a.id()}")
        print(f"坐标 (左上角): x={x}, y={y}, w={w}, h={h}")
        print(f"中心点 (浮点): cx={a.cxf()}, cy={a.cyf()}")
        print(f"旋转角度 (弧度): {a.rotation()}  (度: {deg_rot:.2f}°)")
        print("--- 3D 姿态 (相机坐标系) ---")
        print(f"平移: x={a.x_translation():.3f}, y={a.y_translation():.3f}, z={a.z_translation():.3f}")
        print(f"旋转 (欧拉角): x={a.x_rotation():.3f}, y={a.y_rotation():.3f}, z={a.z_rotation():.3f}")
        print("=" * 40)

    disp.show(img)