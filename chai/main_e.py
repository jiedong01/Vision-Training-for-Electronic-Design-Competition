from maix import image, camera, display, app,uart, pinmap
import cv2
import numpy as np
import time
import math
devices = uart.list_devices()
serial = uart.UART(devices[0], 115200, uart.BITS.BITS_8, uart.PARITY.PARITY_NONE, uart.STOP.STOP_1)
#做以下配置 波特率115200 数据位8 校验位NONE 停止位1



# 定义不同框的颜色
INNER_COLOR = (0, 255, 0)    # 绿色 - 内框
OUTER_COLOR = (0, 0, 255)      # 红色 - 外框
MIDDLE_COLOR = (255, 0, 0)     # 蓝色 - 中间框
POINT_COLOR = (255, 255, 0)    # 青色 - 点
LABEL_COLOR = (255, 0, 255)    # 紫色 - 标签


# 定义全局常量
CAMERA_WIDTH = 240
CAMERA_HEIGHT = 240
HISTORY_SIZE = 3
COLOR_RED = image.COLOR_RED
COLOR_GREEN = image.COLOR_GREEN
COLOR_RED_PRED = image.Color(200, 100, 100)  # 浅红色
COLOR_GREEN_PRED = image.Color(100, 200, 100)  # 浅绿色
COLOR_WHITE = image.COLOR_WHITE

# 颜色阈值配置
RED_H_THRESH_LOW = 0
RED_H_THRESH_HIGH = 40
RED_H_THRESH_LOW2 = 150
RED_H_THRESH_HIGH2 = 180
GREEN_H_THRESH_LOW = 40
GREEN_H_THRESH_HIGH = 90

# 激光点参数
RED_MIN_SAT = 10
RED_MIN_VAL = 40
RED_MIN_CIRCULARITY = 0.4
GREEN_MIN_SAT = 50
GREEN_MIN_VAL = 100
GREEN_MIN_CIRCULARITY = 0.6
#发送测试数据类
class TTest():
    def __init__(self) -> None:
        #发送标识位
        self.Tflag = 0
 
        #发送数据内容
        self.test_number0 = 0
        self.test_number1 = 0
        self.test_number2 = 0
        self.test_number3 = 0
        self.test_number4 = 0
        self.test_number5 = 0
        self.test_number6 = 0
        self.test_number7 = 0
        self.test_number8 = 0
        self.test_number9 = 0
      

TTest0 = TTest()
TTest0.Tflag = 1
TTest0.test_number0 = 0
TTest0.test_number1 = 0
TTest0.test_number2 = 0
TTest0.test_number3 = 0 
TTest0.test_number4 = 0
TTest0.test_number5 = 0
TTest0.test_number6 = 0
TTest0.test_number7 = 0
TTest0.test_number8 = 0 
TTest0.test_number9 = 0
#串口发送函数 十位
def DataTransimit(head, tail, TData, serial):
    data = ()
    if TData.Tflag == 1:
        data = bytes([
            head,
            TData.test_number0,
            TData.test_number1,
            TData.test_number2,
            TData.test_number3,
            TData.test_number4,
            TData.test_number5,
            TData.test_number6,
            TData.test_number7,
            TData.test_number8,
            TData.test_number9,                 
            tail
        ])
        
    elif TData.Tflag == 2:
        data = bytes([
            head,
            #想要发送的数据
            tail
        ])
 
    if data != ():
        #发送数据
        serial.write(data)
 
#接受测试数据类
class  RTest():
    def __init__(self) -> None:
        #接收标识位
        self.Rflag = 0
        #发送数据标识位        
        self.Tflag = 0
 
        #接收数据内容
        self.test_number0 = 0
        self.test_number1 = 0
        self.test_number2 = 0

     
 
 
RTest0 = RTest()
RTest0.Rflag = 1
RTest0.Tflag = 1
 
#串口接受函数 长度9位
def ReceiveData(head, tail, length, serial):
    BufData = serial.read(40)
    if BufData and len(BufData) >= length: #判断接收到的数据长度
        if BufData[0] == head and BufData[length-1] == tail: #判断帧头帧尾
            return BufData
        else:
            return None
 
#接收数据解析函数
def ParseData(RData, BufData):
    if BufData != None:
        if RData.Rflag == 1:
            RData.test_number0 = BufData[0]
            RData.test_number1 = BufData[1]
            RData.test_number2 = BufData[2]
   
            print(RData.test_number0,RData.test_number1,RData.test_number2)  #打印出结果 判断正误
        elif RData.Rflag == 2:
            #接收数据内容
            pass
 
 
class Timer():
    #定时器类   #count_flag为定时器完成计时的标志，每当count_flag == 1，我们将执行一次需要定时的程序。
    def __init__(self) -> None:
        #计时数
        self.count = 0
        #计时数上限
        self.count_max = 0
        #计时完成标识
        self.count_flag = 0
 
timer0 = Timer()
timer0.count_max = 100000
 
def TimerStart(Timer):
    if Timer.count < Timer.count_max:
        #计时开始，计时器标识位置0
        Timer.count_flag = 0
        Timer.count += 1
    
    else:
        #计时完成，计时器标识位置1
        Timer.count_flag = 1
        Timer.count = 0

def detect_laser_points(img, state):
    """
    检测图像中的红色和绿色激光点
    
    参数:
        img: 当前帧图像
        state: 包含处理状态的字典
        
    返回:
        (red_point, green_point, updated_state): 检测到的红点和绿点坐标及更新后的状态
    """
    # 从状态字典中提取变量
    dynamic_threshold = state['dynamic_threshold']
    min_contour_area = state['min_contour_area']
    max_contour_area = state['max_contour_area']
    frame_count = state['frame_count']
    start_time = state['start_time']
    red_history = state['red_history']
    green_history = state['green_history']
    last_red_detected = state['last_red_detected']
    last_green_detected = state['last_green_detected']
    consecutive_red_misses = state['consecutive_red_misses']
    consecutive_green_misses = state['consecutive_green_misses']
    last_img_cv_gray = state['last_img_cv_gray']
    
    # 初始化点坐标
    red_point = (-1, -1)
    green_point = (-1, -1)
    
    # 转换图像格式
    img_cv = image.image2cv(img, False, False)
    
    # 如果是第一帧，只保存灰度图
    if last_img_cv_gray is None:
        img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        return (red_point, green_point), {
            'last_img_cv_gray': img_cv_gray,
            'dynamic_threshold': dynamic_threshold,
            'min_contour_area': min_contour_area,
            'max_contour_area': max_contour_area,
            'frame_count': frame_count + 1,
            'start_time': start_time,
            'red_history': red_history,
            'green_history': green_history,
            'last_red_detected': last_red_detected,
            'last_green_detected': last_green_detected,
            'consecutive_red_misses': consecutive_red_misses,
            'consecutive_green_misses': consecutive_green_misses
        }
    
    # 计算当前帧灰度图
    img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # 修复高斯模糊语法错误
    # 计算差值 - 添加高斯模糊减少噪声
    current_blur = cv2.GaussianBlur(img_cv_gray, (5, 5), 0)
    last_blur = cv2.GaussianBlur(last_img_cv_gray, (5, 5), 0)
    img_diff = cv2.absdiff(current_blur, last_blur)
    
    # 动态调整阈值 - 每30帧根据环境亮度调整一次
    if frame_count % 30 == 0:
        mean_brightness = cv2.mean(img_cv_gray)[0]
        
        # 根据环境亮度调整阈值
        if mean_brightness < 50:   # 暗环境
            dynamic_threshold = 15
            min_contour_area = 2
        elif mean_brightness < 100: # 中等亮度
            dynamic_threshold = 25
            min_contour_area = 4
        else:                      # 明亮环境
            dynamic_threshold = 40
            min_contour_area = 6
            
        # 根据运行时间微调
        elapsed_time = time.time() - start_time
        if elapsed_time < 10:  # 前10秒
            dynamic_threshold = max(10, dynamic_threshold - 5)
    
    # 二值化处理
    _, img_binary = cv2.threshold(img_diff, dynamic_threshold, 255, cv2.THRESH_BINARY)
    
    # 形态学操作
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img_binary = cv2.dilate(img_binary, kernel, iterations=1)
    img_binary = cv2.erode(img_binary, None, iterations=1)
    
    # 查找轮廓
    contours, _ = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 存储候选激光点
    red_candidates = []
    green_candidates = []
    
    # 处理每个轮廓
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < min_contour_area or contour_area > max_contour_area: 
            continue

        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
            
        point_x = int(M["m10"] / M["m00"])
        point_y = int(M["m01"] / M["m00"])
        
        # 确保ROI在图像范围内
        x, y, w, h = cv2.boundingRect(contour)
        if y < 0 or x < 0 or y+h >= CAMERA_HEIGHT or x+w >= CAMERA_WIDTH:
            continue
            
        roi = img_cv[y:y+h, x:x+w]
        
        # 计算轮廓圆度
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            circularity = 4 * math.pi * contour_area / (perimeter * perimeter)
        else:
            continue
        
        # 转换为HSV并计算中值
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        h_median = np.median(roi_hsv[:,:,0])
        s_median = np.median(roi_hsv[:,:,1])
        v_median = np.median(roi_hsv[:,:,2])
        
        # 红色激光点检测
        red_condition = (
            (RED_H_THRESH_LOW <= h_median <= RED_H_THRESH_HIGH) or 
            (RED_H_THRESH_LOW2 <= h_median <= RED_H_THRESH_HIGH2)
        )
        
        if red_condition:
            if (s_median > RED_MIN_SAT and 
                v_median > RED_MIN_VAL and 
                circularity > RED_MIN_CIRCULARITY):
                weight = v_median * (1 + circularity)
                red_candidates.append((point_x, point_y, weight))
        
        # 绿色激光点检测
        elif GREEN_H_THRESH_LOW <= h_median <= GREEN_H_THRESH_HIGH:
            if (s_median > GREEN_MIN_SAT and 
                v_median > GREEN_MIN_VAL and 
                circularity > GREEN_MIN_CIRCULARITY):
                weight = v_median
                green_candidates.append((point_x, point_y, weight))
    
    # 处理红色候选点
    current_red = (-1, -1)
    if red_candidates:
        red_candidates.sort(key=lambda x: x[2], reverse=True)
        best_red = red_candidates[0]
        current_red = (best_red[0], best_red[1])
        last_red_detected = True
        consecutive_red_misses = 0
        
        # 更新历史记录
        red_history.append(current_red)
        if len(red_history) > HISTORY_SIZE:
            red_history.pop(0)
            
        # 计算平均位置
        avg_x = sum(p[0] for p in red_history) / len(red_history)
        avg_y = sum(p[1] for p in red_history) / len(red_history)
        red_point = (int(avg_x), int(avg_y))
    else:
        consecutive_red_misses += 1
        if consecutive_red_misses > 2:
            last_red_detected = False
    
    # 处理绿色候选点
    current_green = (-1, -1)
    if green_candidates:
        green_candidates.sort(key=lambda x: x[2], reverse=True)
        best_green = green_candidates[0]
        current_green = (best_green[0], best_green[1])
        last_green_detected = True
        consecutive_green_misses = 0
        
        # 更新历史记录
        green_history.append(current_green)
        if len(green_history) > HISTORY_SIZE:
            green_history.pop(0)
            
        # 计算平均位置
        avg_x = sum(p[0] for p in green_history) / len(green_history)
        avg_y = sum(p[1] for p in green_history) / len(green_history)
        green_point = (int(avg_x), int(avg_y))
    else:
        consecutive_green_misses += 1
        if consecutive_green_misses > 2:
            last_green_detected = False
    
    # 使用历史位置预测
    if not last_red_detected and red_history:
        red_point = red_history[-1]
    
    if not last_green_detected and green_history:
        green_point = green_history[-1]
    
    # 返回检测结果和更新后的状态
    return (red_point, green_point), {
        'last_img_cv_gray': img_cv_gray,
        'dynamic_threshold': dynamic_threshold,
        'min_contour_area': min_contour_area,
        'max_contour_area': max_contour_area,
        'frame_count': frame_count + 1,
        'start_time': start_time,
        'red_history': red_history,
        'green_history': green_history,
        'last_red_detected': last_red_detected,
        'last_green_detected': last_green_detected,
        'consecutive_red_misses': consecutive_red_misses,
        'consecutive_green_misses': consecutive_green_misses
    }

def print_coordinates(red, green):
    """在终端打印激光点坐标"""
    red_str = f"({red[0]}, {red[1]})" if red != (-1, -1) else "Not found"
    green_str = f"({green[0]}, {green[1]})" if green != (-1, -1) else "Not found"
    print(f"Red: {red_str}\tGreen: {green_str}")

def draw_results(img, red_point, green_point, last_red_detected, last_green_detected):
    """在图像上绘制激光点位置和坐标"""
    # 绘制激光点位置
    if red_point != (-1, -1):
        color = COLOR_RED if last_red_detected else COLOR_RED_PRED
        label = "R" if last_red_detected else "R?"
        img.draw_cross(red_point[0], red_point[1], color, 5, 2)
        img.draw_string(red_point[0] + 5, red_point[1] - 10, label, color, scale=1.2)
    
    if green_point != (-1, -1):
        color = COLOR_GREEN if last_green_detected else COLOR_GREEN_PRED
        label = "G" if last_green_detected else "G?"
        img.draw_cross(green_point[0], green_point[1], color, 5, 2)
        img.draw_string(green_point[0] + 5, green_point[1] - 10, label, color, scale=1.2)
    
    # 在图像底部显示坐标
    if red_point != (-1, -1):
        img.draw_string(5, img.height() - 40, f"Red: ({red_point[0]}, {red_point[1]})", 
                       COLOR_RED, scale=1.0)
    else:
        img.draw_string(5, img.height() - 40, "Red: Not found", 
                       COLOR_RED, scale=1.0)
    
    if green_point != (-1, -1):
        img.draw_string(5, img.height() - 20, f"Green: ({green_point[0]}, {green_point[1]})", 
                       COLOR_GREEN, scale=1.0)
    else:
        img.draw_string(5, img.height() - 20, "Green: Not found", 
                       COLOR_GREEN, scale=1.0)

 # 定义形态学操作核
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

def extend_line(line, width, height):
    """延长直线到图像边界"""
    if line is None:
        return None
        
    x1, y1, x2, y2 = line
    
    # 计算直线方向向量
    dx = x2 - x1
    dy = y2 - y1
    
    # 如果线段长度太短，使用中点作为参考
    if dx == 0 and dy == 0:
        return line
    
    # 计算延长参数
    t_values = []
    
    # 与左边界相交 (x=0)
    if dx != 0:
        t = (0 - x1) / dx
        y = y1 + t * dy
        if 0 <= y <= height:
            t_values.append(t)
    
    # 与右边界相交 (x=width)
    if dx != 0:
        t = (width - x1) / dx
        y = y1 + t * dy
        if 0 <= y <= height:
            t_values.append(t)
    
    # 与上边界相交 (y=0)
    if dy != 0:
        t = (0 - y1) / dy
        x = x1 + t * dx
        if 0 <= x <= width:
            t_values.append(t)
    
    # 与下边界相交 (y=height)
    if dy != 0:
        t = (height - y1) / dy
        x = x1 + t * dx
        if 0 <= x <= width:
            t_values.append(t)
    
    # 如果没有找到交点，返回原始线段
    if not t_values:
        return line
    
    # 找到最小和最大t值
    t_min = min(t_values)
    t_max = max(t_values)
    
    # 计算延长后的端点
    x1_ext = x1 + t_min * dx
    y1_ext = y1 + t_min * dy
    x2_ext = x1 + t_max * dx
    y2_ext = y1 + t_max * dy
    
    return (int(x1_ext), int(y1_ext), int(x2_ext), int(y2_ext))

def line_intersection(line1, line2):
    """计算两条直线的交点"""
    if line1 is None or line2 is None:
        return None
        
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    
    # 计算分母
    den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    
    # 如果分母为0，说明两线平行
    if den == 0:
        return None
    
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
    
    # 计算交点
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    
    return (int(x), int(y))

def penrect_reg(img, disp):
    img_raw = image.image2cv(img, copy=False)
    height, width = img_raw.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    # 1. 转灰度
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY) 
    
    # 2. 高斯模糊降噪
    img_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    
    # 3. 自适应阈值处理 - 更适合铅笔线
    binary_img = cv2.adaptiveThreshold(
        img_blur, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        11, 
        2
    )
    
    # 4. 形态学操作 - 闭运算连接断线
    img_closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # 5. Canny边缘检测
    edged = cv2.Canny(img_closed, 50, 150)

    # 6. 霍夫线变换检测直线
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=20)
    
    # 7. 绘制检测到的直线并分类
    horizontal_lines = []
    vertical_lines = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 计算直线角度
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 分类水平线和垂直线
            if angle < 30 or angle > 150:  # 水平线
                horizontal_lines.append(line[0])
                # 绘制原始检测到的水平线 (绿色)
                cv2.line(img_raw, (x1, y1), (x2, y2), (0, 255, 0), 1)
            elif 60 < angle < 120:  # 垂直线
                vertical_lines.append(line[0])
                # 绘制原始检测到的垂直线 (蓝色)
                cv2.line(img_raw, (x1, y1), (x2, y2), (255, 0, 0), 1)
    
    # 8. 选择最靠近图像中心的四条线（最里面的矩形）
    top_line = None
    bottom_line = None
    left_line = None
    right_line = None
    
    # 选择最靠近图像中心的水平线作为顶部和底部
    if len(horizontal_lines) > 0:
        # 按中点y坐标排序
        horizontal_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
        
        # 选择最靠近中心的线作为参考
        closest_line = horizontal_lines[0]
        closest_y = (closest_line[1] + closest_line[3]) / 2
        
        # 区分上方和下方的线
        top_lines = [line for line in horizontal_lines if (line[1] + line[3]) / 2 < center_y]
        bottom_lines = [line for line in horizontal_lines if (line[1] + line[3]) / 2 > center_y]
        
        # 选择最靠近中心的上方线（顶部）
        if top_lines:
            top_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
            top_line = top_lines[0]
        
        # 选择最靠近中心的下方线（底部）
        if bottom_lines:
            bottom_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
            bottom_line = bottom_lines[0]
    
    # 选择最靠近图像中心的垂直线作为左侧和右侧
    if len(vertical_lines) > 0:
        # 按中点x坐标排序
        vertical_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
        
        # 选择最靠近中心的线作为参考
        closest_line = vertical_lines[0]
        closest_x = (closest_line[0] + closest_line[2]) / 2
        
        # 区分左侧和右侧的线
        left_lines = [line for line in vertical_lines if (line[0] + line[2]) / 2 < center_x]
        right_lines = [line for line in vertical_lines if (line[0] + line[2]) / 2 > center_x]
        
        # 选择最靠近中心的左侧线（左边）
        if left_lines:
            left_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
            left_line = left_lines[0]
        
        # 选择最靠近中心的右侧线（右边）
        if right_lines:
            right_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
            right_line = right_lines[0]
    
    # 延长选中的线
    if top_line is not None:
        top_line_ext = extend_line(top_line, width, height)
        cv2.line(img_raw, (top_line_ext[0], top_line_ext[1]), 
                 (top_line_ext[2], top_line_ext[3]), (0, 200, 0), 2)
    
    if bottom_line is not None:
        bottom_line_ext = extend_line(bottom_line, width, height)
        cv2.line(img_raw, (bottom_line_ext[0], bottom_line_ext[1]), 
                 (bottom_line_ext[2], bottom_line_ext[3]), (0, 200, 0), 2)
    
    if left_line is not None:
        left_line_ext = extend_line(left_line, width, height)
        cv2.line(img_raw, (left_line_ext[0], left_line_ext[1]), 
                 (left_line_ext[2], left_line_ext[3]), (200, 0, 0), 2)
    
    if right_line is not None:
        right_line_ext = extend_line(right_line, width, height)
        cv2.line(img_raw, (right_line_ext[0], right_line_ext[1]), 
                 (right_line_ext[2], right_line_ext[3]), (200, 0, 0), 2)
    
    # 9. 计算交点
    corners = []
    
    # 计算四个交点
    if top_line is not None and left_line is not None:
        top_ext = extend_line(top_line, width, height)
        left_ext = extend_line(left_line, width, height)
        corner = line_intersection(top_ext, left_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)  # 红色点标记交点
    
    if top_line is not None and right_line is not None:
        top_ext = extend_line(top_line, width, height)
        right_ext = extend_line(right_line, width, height)
        corner = line_intersection(top_ext, right_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    if bottom_line is not None and left_line is not None:
        bottom_ext = extend_line(bottom_line, width, height)
        left_ext = extend_line(left_line, width, height)
        corner = line_intersection(bottom_ext, left_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    if bottom_line is not None and right_line is not None:
        bottom_ext = extend_line(bottom_line, width, height)
        right_ext = extend_line(right_line, width, height)
        corner = line_intersection(bottom_ext, right_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    # 10. 检查矩形高度并绘制矩形框
    if len(corners) == 4:
        # 按左上、右上、右下、左下排序
        # 计算中心点
        center_x = int(round(sum(c[0] for c in corners) / 4))
        center_y = int(round(sum(c[1] for c in corners) / 4))
        
        # 按角度排序
        def angle_from_center(corner):
            return np.arctan2(corner[1] - center_y, corner[0] - center_x)
        
        corners_sorted = sorted(corners, key=angle_from_center)
        
        # 提取四个点
        p1 = corners_sorted[0]  # 左上
        p2 = corners_sorted[1]  # 右上
        p3 = corners_sorted[2]  # 右下
        p4 = corners_sorted[3]  # 左下
        
        # 计算左右两侧的高度
        height_left = abs(p4[1] - p1[1])  # 左侧高度（P1和P4的Y坐标差）
        height_right = abs(p3[1] - p2[1])  # 右侧高度（P2和P3的Y坐标差）
        
        # 设置最小高度阈值
        min_height_threshold = 85
        
        # 检查高度是否满足要求
        if height_left > min_height_threshold and height_right > min_height_threshold:
            # 绘制矩形框
            cv2.polylines(img_raw, [np.array(corners_sorted)], True, (0, 0, 255), 2)
            
            # 标记角点
            for i, (x, y) in enumerate(corners_sorted):
                cv2.circle(img_raw, (x, y), 8, (0, 255, 255), -1)
                cv2.putText(img_raw, f"P{i+1}", (x+10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.circle(img_raw, (center_x, center_y), 8, (0, 255, 255), -1)     
            #打印坐标到控制台
            # print("检测到的矩形角点坐标:")
            # print(f"P1 (左上): ({p1[0]}, {p1[1]})")
            # print(f"P2 (右上): ({p2[0]}, {p2[1]})")
            # print(f"P3 (右下): ({p3[0]}, {p3[1]})")
            # print(f"P4 (左下): ({p4[0]}, {p4[1]})")
            # print(f"矩形中心点的坐标: ({center_x,center_y})")
            # print(f"左侧高度: {height_left}, 右侧高度: {height_right}")
            # print("-" * 40)
            # return([p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p4[0],p4[1],center_x,center_y])

            # 在图像上显示坐标和高度信息
            cv2.putText(img_raw, f"P1:({p1[0]},{p1[1]})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P2:({p2[0]},{p2[1]})", 
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P3:({p3[0]},{p3[1]})", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P4:({p4[0]},{p4[1]})", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"center({center_x,center_y})", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"Height: {height_left}", 
                       (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                # 11. 显示结果
            img_show = image.cv2image(img_raw, copy=False) 
            disp.show(img_show)
            return([p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p4[0],p4[1],center_x,center_y])
        else:
            #高度不足，显示提示信息
            cv2.putText(img_raw, f"Height too small: {min(height_left, height_right)} < {min_height_threshold}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            print(f"矩形高度不足: 左侧高度 {height_left}, 右侧高度 {height_right} < {min_height_threshold}")
    
    elif len(corners) > 0:
        # 显示找到的角点数量
        cv2.putText(img_raw, f"Corners: {len(corners)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # 11. 显示结果
    img_show = image.cv2image(img_raw, copy=False) 
    disp.show(img_show)

def order_points(pts):
    """对点进行排序：左上，右上，右下，左下"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # 左上点
    rect[2] = pts[np.argmax(s)]  # 右下点
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 右上点
    rect[3] = pts[np.argmax(diff)]  # 左下点
    return rect

def rect_reg(img, disp):
    img_raw = image.image2cv(img, copy=False)
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    img_filtered = cv2.bilateralFilter(img_gray, 9, 150, 200)
    img_closed = cv2.morphologyEx(img_filtered, cv2.MORPH_CLOSE, kernel)
    edged = cv2.Canny(img_closed, 100, 200)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # 存储找到的四边形
    quads = []
    
    for contour in contours:
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 只处理四边形
        if len(approx) == 4:
            # 转换为numpy数组并展平
            approx_flat = approx.reshape(4, 2)
            quads.append(approx_flat)
    
    # 需要至少两个四边形才能计算中间框
    if len(quads) < 2:
        # 如果没有足够四边形，直接显示原始图像
        img_show = image.cv2image(img_raw, copy=False)
        disp.show(img_show)
        return
    
    # 根据面积排序，面积大的为外框，小的为内框
    quads.sort(key=lambda x: cv2.contourArea(x))
    inner_quad = quads[0]  # 内框（面积小）
    outer_quad = quads[-1]  # 外框（面积大）
    
    # 对点进行排序（左上，右上，右下，左下）
    inner_quad = order_points(inner_quad)
    outer_quad = order_points(outer_quad)
    
    # 计算中间框的点（内框和外框对应点的平均值）
    middle_quad = []
    for i in range(4):
        x = int((inner_quad[i][0] + outer_quad[i][0]) / 2)
        y = int((inner_quad[i][1] + outer_quad[i][1]) / 2)
        middle_quad.append([x, y])
    middle_quad = np.array(middle_quad)
    
    # 绘制内框
    cv2.drawContours(img_raw, [inner_quad.astype("int")], -1, INNER_COLOR, 2)
    
    # 绘制外框
    cv2.drawContours(img_raw, [outer_quad.astype("int")], -1, OUTER_COLOR, 2)
    
    # 绘制中间框
    cv2.drawContours(img_raw, [middle_quad.astype("int")], -1, MIDDLE_COLOR, 2)
    
    # 绘制点
    for i, quad in enumerate([inner_quad, outer_quad, middle_quad]):
        for point in quad:
            x, y = int(point[0]), int(point[1])
            cv2.circle(img_raw, (x, y), 5, POINT_COLOR, -1)
    
    # 在中间框点上标注序号 P1, P2, P3, P4
    labels = ["P1", "P2", "P3", "P4"]
    for i, point in enumerate(middle_quad):
        x, y = int(point[0]), int(point[1])
        # 在点旁边添加标签
        cv2.putText(img_raw, labels[i], (x + 10, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, LABEL_COLOR, 2)
    
    # 创建并打印中间框点坐标数组
    middle_points_array = []
    for i, point in enumerate(middle_quad):
        x, y = int(point[0]), int(point[1])
        middle_points_array.append([x, y])
        # 打印每个点的坐标
        print(f"{labels[i]}: ({x}, {y})")
    
    # 打印整个数组
    print("\n中间框点坐标数组:")
    print(middle_points_array)
    img_show = image.cv2image(img_raw, copy=False)
    disp.show(img_show)
    return middle_points_array
    # # 显示处理后的图像
    # img_show = image.cv2image(img_raw, copy=False)
    # disp.show(img_show)
    
# def main():  #串口主函数
#     while True:
#         TimerStart(timer0)
#         if (timer0.count_flag == 1 and RTest0.Rflag == 1):
#                 ParseData(RTest0, ReceiveData(0xA5, 0x5A, 3, serial))#接收数据的函数
#                 #RTest0.Rflag =0 #接收数据标志位
#         if (timer0.count_flag == 1 and TTest0.Tflag == 1):
#                  DataTransimit(0xA5, 0x5A, TTest0, serial) #发送数据的函数 TTest0为需要发送的值
# ... 前面的代码保持不变 ...

def main():
    # 初始化状态
    state = {
        'last_img_cv_gray': None,
        'dynamic_threshold': 20,
        'min_contour_area': 2,
        'max_contour_area': 400,
        'frame_count': 0,
        'start_time': time.time(),
        'red_history': [],
        'green_history': [],
        'last_red_detected': False,
        'last_green_detected': False,
        'consecutive_red_misses': 0,
        'consecutive_green_misses': 0
    }
    
    print("Starting laser point detection...")
    print("Press Ctrl+C to exit")

    cam = camera.Camera(240, 240) 
    disp = display.Display()
    current_mode = 0      # 当前工作模式
    process_stage = 0     # 处理阶段: 0-初始, 1-矩形框识别中, 2-激光点检测中
    rect_data = None      # 存储矩形框坐标数据
    last_red_point = (-1, -1)  # 上一次检测到的红点
    
    while not app.need_exit():
        TimerStart(timer0)
        img = cam.read()
        
        # 接收并处理串口数据
        BufData = ReceiveData(0xA5, 0x5A, 3, serial)
        if BufData is not None:
            ParseData(RTest0, BufData)
            # 更新模式，如果是模式5则重置处理阶段
            if RTest0.test_number1 == 5:
                current_mode = 5
                process_stage = 0
                rect_data = None
            else:
                # 如果模式改变，重置处理阶段
                if current_mode != RTest0.test_number1:
                    current_mode = RTest0.test_number1
                    process_stage = 0
                    rect_data = None
            print(f"Mode changed to: {current_mode}")
        
        # 模式5 - 停止所有处理，只显示原始图像
        if current_mode == 5:
            disp.show(img)
            continue
        
        # 模式1处理逻辑
        if current_mode == 1:
            # 阶段1: 铅笔框识别
            if process_stage == 0:
                rect_data = penrect_reg(img, disp)
                if rect_data is not None and len(rect_data) >= 10:
                    print("Pencil frame detected! Switching to laser detection.")
                    process_stage = 1  # 进入激光点检测阶段
            
            # 阶段2: 激光点检测
            elif process_stage == 1:
                # 检测激光点
                (red_point, green_point), state = detect_laser_points(img, state)
                
                # 绘制结果
                draw_results(
                    img, 
                    red_point, 
                    green_point, 
                    state['last_red_detected'], 
                    state['last_green_detected']
                )
                
                # 显示图像
                disp.show(img)
                
                # 如果检测到红点且位置发生变化，发送数据
                if red_point != (-1, -1) and red_point != last_red_point:
                    # 准备发送数据
                    TTest0 = TTest()
                    TTest0.Tflag = 1
                    # 铅笔框中心坐标 + 激光点坐标
                    TTest0.test_number0 = rect_data[8]  # 中心X
                    TTest0.test_number1 = rect_data[9]  # 中心Y
                    TTest0.test_number2 = red_point[0]  # 红点X
                    TTest0.test_number3 = red_point[1]  # 红点Y
                    
                    # 发送数据
                    DataTransimit(0xA5, 0x5A, TTest0, serial)
                    print(f"Sent: Center({rect_data[8]}, {rect_data[9]}), Laser({red_point[0]}, {red_point[1]})")
                    
                    # 更新最后检测到的红点
                    last_red_point = red_point
        
        # 模式2处理逻辑
        elif current_mode == 2:
            # 阶段1: 铅笔框识别
            if process_stage == 0:
                rect_data = penrect_reg(img, disp)
                if rect_data is not None and len(rect_data) >= 10:
                    print("Pencil frame detected! Switching to laser detection.")
                    process_stage = 1  # 进入激光点检测阶段
            
            # 阶段2: 激光点检测
            elif process_stage == 1:
                # 检测激光点
                (red_point, green_point), state = detect_laser_points(img, state)
                
                # 绘制结果
                draw_results(
                    img, 
                    red_point, 
                    green_point, 
                    state['last_red_detected'], 
                    state['last_green_detected']
                )
                
                # 显示图像
                disp.show(img)
                
                # 如果检测到红点且位置发生变化，发送数据
                if red_point != (-1, -1) and red_point != last_red_point:
                    # 准备发送数据
                    TTest0 = TTest()
                    TTest0.Tflag = 1
                    # 铅笔框四个角点 + 激光点坐标
                    TTest0.test_number0 = rect_data[0]  # P1x
                    TTest0.test_number1 = rect_data[1]  # P1y
                    TTest0.test_number2 = rect_data[2]  # P2x
                    TTest0.test_number3 = rect_data[3]  # P2y
                    TTest0.test_number4 = rect_data[4]  # P3x
                    TTest0.test_number5 = rect_data[5]  # P3y
                    TTest0.test_number6 = rect_data[6]  # P4x
                    TTest0.test_number7 = rect_data[7]  # P4y
                    TTest0.test_number8 = red_point[0]  # 红点X
                    TTest0.test_number9 = red_point[1]  # 红点Y
                    
                    # 发送数据
                    DataTransimit(0xA5, 0x5A, TTest0, serial)
                    print(f"Sent: Frame points and Laser({red_point[0]}, {red_point[1]})")
                    
                    # 更新最后检测到的红点
                    last_red_point = red_point
        
        # 模式3和4处理逻辑（共用）
        elif current_mode in [3, 4]:
            # 阶段1: 矩形框识别
            if process_stage == 0:
                rect_data = rect_reg(img, disp)
                if rect_data is not None and len(rect_data) == 4:
                    print("Rectangular frame detected! Switching to laser detection.")
                    process_stage = 1  # 进入激光点检测阶段
                    # 保存矩形框坐标
                    rect_points = rect_data
                else:
                    # 如果没有检测到矩形框，继续尝试
                    continue
            
            # 阶段2: 激光点检测
            elif process_stage == 1:
                # 检测激光点
                (red_point, green_point), state = detect_laser_points(img, state)
                
                # 绘制结果
                draw_results(
                    img, 
                    red_point, 
                    green_point, 
                    state['last_red_detected'], 
                    state['last_green_detected']
                )
                
                # 显示图像
                disp.show(img)
                
                # 如果检测到红点且位置发生变化，发送数据
                if red_point != (-1, -1) and red_point != last_red_point:
                    # 准备发送数据
                    TTest0 = TTest()
                    TTest0.Tflag = 1
                    # 矩形框四个角点 + 激光点坐标
                    # P1
                    TTest0.test_number0 = rect_points[0][0]  # P1x
                    TTest0.test_number1 = rect_points[0][1]  # P1y
                    # P2
                    TTest0.test_number2 = rect_points[1][0]  # P2x
                    TTest0.test_number3 = rect_points[1][1]  # P2y
                    # P3
                    TTest0.test_number4 = rect_points[2][0]  # P3x
                    TTest0.test_number5 = rect_points[2][1]  # P3y
                    # P4
                    TTest0.test_number6 = rect_points[3][0]  # P4x
                    TTest0.test_number7 = rect_points[3][1]  # P4y
                    # 激光点
                    TTest0.test_number8 = red_point[0]  # 红点X
                    TTest0.test_number9 = red_point[1]  # 红点Y
                    
                    # 发送数据
                    DataTransimit(0xA5, 0x5A, TTest0, serial)
                    print(f"Sent: Rect points and Laser({red_point[0]}, {red_point[1]})")
                    
                    # 更新最后检测到的红点
                    last_red_point = red_point
        
        # 短暂延迟
        time.sleep(0.01)
                
        # 显示图像
        disp.show(img)         

if __name__ == '__main__':
    main()

# def main():
#     """主函数"""
#     # 初始化摄像头和显示屏
#     cam = camera.Camera(CAMERA_WIDTH, CAMERA_HEIGHT) 
#     disp = display.Display()
    
#     # 初始化状态
#     state = {
#         'last_img_cv_gray': None,
#         'dynamic_threshold': 20,
#         'min_contour_area': 2,
#         'max_contour_area': 400,
#         'frame_count': 0,
#         'start_time': time.time(),
#         'red_history': [],
#         'green_history': [],
#         'last_red_detected': False,
#         'last_green_detected': False,
#         'consecutive_red_misses': 0,
#         'consecutive_green_misses': 0
#     }
    
#     print("Starting laser point detection...")
#     print("Press Ctrl+C to exit")
    
#     while not app.need_exit():
#         # 读取图像
#         img = cam.read()
        
#         # 检测激光点
#         (red_point, green_point), state = detect_laser_points(img, state)
        
#         # 在终端打印坐标
#         if state['frame_count'] % 5 == 0:  # 每5帧打印一次
#             print_coordinates(red_point, green_point)
        
#         # 在图像上绘制结果
#         draw_results(
#             img, 
#             red_point, 
#             green_point, 
#             state['last_red_detected'], 
#             state['last_green_detected']
#         )
        
#         # 显示图像
#         disp.show(img)
        
#         # 添加短暂延迟
#         time.sleep(0.01)

# def main():
#     cam = camera.Camera(240, 240)
#     disp = display.Display()
    
#     while not app.need_exit():
#         img = cam.read()
#         middle_points_array=rect_reg(img, disp)
#         #print(f"1:{middle_points_array}")

if __name__ == '__main__':
    main()