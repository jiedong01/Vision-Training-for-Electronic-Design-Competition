# main.py
# 主程序 - MaixCAM智能车巡线

from maix import camera, display, image, time
from motor import Motor
from line_follower import LineFollower

# ============ 配置 ============
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# LAB颜色阈值 - 需要根据实际赛道颜色调整
# 格式: [L_MIN, L_MAX, A_MIN, A_MAX, B_MIN, B_MAX]
# 以下为绿色赛道示例
THRESHOLDS = [[0, 80, -120, -10, 0, 30]]  # 绿色
# THRESHOLDS = [[0, 80, 40, 80, 10, 80]]   # 红色
# THRESHOLDS = [[0, 80, 30, 100, -120, -60]] # 蓝色

# PID参数
KP = 0.8
BASE_SPEED = 50

# ============ 初始化 ============
print("初始化摄像头...")
cam = camera.Camera(CAMERA_WIDTH, CAMERA_HEIGHT)
print("初始化屏幕...")
disp = display.Display()

print("初始化电机...")
motor = Motor()

print("初始化寻线模块...")
follower = LineFollower(CAMERA_WIDTH, CAMERA_HEIGHT)

print("初始化完成！开始巡线...")

# ============ 主循环 ============
while True:
    # 1. 读取图像
    img = cam.read()
    
    # 2. 寻找直线（用于获取theta和rho辅助控制）
    lines = img.get_regression(THRESHOLDS, area_threshold=100)
    
    # 3. 获取二值化图像用于边线提取
    # 注意：get_regression返回的是RGB图像，需要转换为二值化
    # 这里简化处理，实际使用时可能需要单独生成二值化图像
    binary_img = img.binary(THRESHOLDS)  # 生成二值化图像
    
    # 4. 提取边线
    follower.extract_lines(binary_img)
    
    # 5. 元素识别
    follower.detect_straight()
    follower.detect_cross()
    
    # 6. 获取控制误差
    error = follower.get_error()
    
    # 7. 显示调试信息
    debug_info = follower.get_debug_info()
    
    # 在图像上显示信息
    info_y = 0
    for key, value in debug_info.items():
        if key in ['left_up', 'right_up', 'left_down', 'right_down']:
            continue  # 拐点信息用图形显示
        img.draw_string(0, info_y, f"{key}: {value}", image.COLOR_RED, scale=1.5)
        info_y += 20
    
    # 显示拐点位置（红色圆圈）
    if debug_info['left_up'] > 0:
        x = follower.left_line[debug_info['left_up']]
        y = debug_info['left_up']
        img.draw_circle(x, y, 5, image.COLOR_RED, thickness=2)
    if debug_info['right_up'] > 0:
        x = follower.right_line[debug_info['right_up']]
        y = debug_info['right_up']
        img.draw_circle(x, y, 5, image.COLOR_RED, thickness=2)
    if debug_info['left_down'] > 0:
        x = follower.left_line[debug_info['left_down']]
        y = debug_info['left_down']
        img.draw_circle(x, y, 5, image.COLOR_GREEN, thickness=2)
    if debug_info['right_down'] > 0:
        x = follower.right_line[debug_info['right_down']]
        y = debug_info['right_down']
        img.draw_circle(x, y, 5, image.COLOR_GREEN, thickness=2)
    
    # 显示边线（在图像上画出左中右线）
    h = CAMERA_HEIGHT
    for row in range(h - 1, h - follower.search_stop_line - 1, -1):
        if follower.left_line[row] > 0:
            img.draw_point(follower.left_line[row], row, image.COLOR_RED)
        if follower.right_line[row] > 0:
            img.draw_point(follower.right_line[row], row, image.COLOR_BLUE)
        if follower.mid_line[row] > 0:
            img.draw_point(follower.mid_line[row], row, image.COLOR_GREEN)
    
    # 8. 控制电机
    motor.control_by_error(error, KP, BASE_SPEED)
    
    # 9. 显示图像
    disp.show(img)
    
    # 10. 小延时，控制帧率
    time.sleep_ms(10)