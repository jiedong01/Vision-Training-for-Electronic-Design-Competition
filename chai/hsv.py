'''
V8 修复版激光点识别模块
详细注释版
'''

# 导入必要的库
from maix import image, camera, display, app  # MaixPy硬件操作库
import cv2  # OpenCV计算机视觉库
import time  # 时间操作
import math  # 数学计算
import numpy as np  # 数值计算库

# 定义全局常量
CAMERA_WIDTH = 240  # 摄像头采集图像宽度
CAMERA_HEIGHT = 240  # 摄像头采集图像高度
HISTORY_SIZE = 3  # 历史位置记录的大小（平滑轨迹用）
COLOR_RED = image.COLOR_RED  # 红色（用于绘制）
COLOR_GREEN = image.COLOR_GREEN  # 绿色（用于绘制）
COLOR_RED_PRED = image.Color(200, 100, 100)  # 浅红色（预测位置）
COLOR_GREEN_PRED = image.Color(100, 200, 100)  # 浅绿色（预测位置）
COLOR_WHITE = image.COLOR_WHITE  # 白色（备用）

# 颜色阈值配置（HSV空间）
RED_H_THRESH_LOW = 0  # 红色色调下限1
RED_H_THRESH_HIGH = 40  # 红色色调上限1
RED_H_THRESH_LOW2 = 150  # 红色色调下限2（红色在HSV色环上跨越0°和180°）
RED_H_THRESH_HIGH2 = 180  # 红色色调上限2
GREEN_H_THRESH_LOW = 40  # 绿色色调下限
GREEN_H_THRESH_HIGH = 90  # 绿色色调上限

# 激光点参数（过滤条件）
RED_MIN_SAT = 10  # 红色最小饱和度
RED_MIN_VAL = 40  # 红色最小亮度
RED_MIN_CIRCULARITY = 0.4  # 红色最小圆度（轮廓接近圆形的程度）
GREEN_MIN_SAT = 50  # 绿色最小饱和度
GREEN_MIN_VAL = 100  # 绿色最小亮度（绿色激光通常更亮）
GREEN_MIN_CIRCULARITY = 0.6  # 绿色最小圆度（要求更严格）

def detect_laser_points(img, state):
    """
    检测图像中的红色和绿色激光点
    
    核心原理：
    1. 帧间差分法：通过比较当前帧和上一帧的差异，检测移动的激光点
    2. 颜色过滤：在HSV色彩空间中识别红色和绿色区域
    3. 形状分析：通过圆度判断斑点形状是否符合激光点特征
    4. 历史轨迹平滑：使用移动平均平滑位置轨迹
    5. 位置预测：当激光点暂时消失时，使用历史位置进行预测
    
    参数:
        img: 当前帧图像 (MaixPy图像对象)
        state: 包含处理状态的字典（跨帧传递信息）
        
    返回:
        (red_point, green_point, updated_state): 
            检测到的红点和绿点坐标及更新后的状态
    """
    # 从状态字典中提取变量
    dynamic_threshold = state['dynamic_threshold']  # 动态二值化阈值
    min_contour_area = state['min_contour_area']  # 最小轮廓面积
    max_contour_area = state['max_contour_area']  # 最大轮廓面积
    frame_count = state['frame_count']  # 帧计数器
    start_time = state['start_time']  # 程序开始时间
    red_history = state['red_history']  # 红色点历史位置
    green_history = state['green_history']  # 绿色点历史位置
    last_red_detected = state['last_red_detected']  # 上一帧是否检测到红色
    last_green_detected = state['last_green_detected']  # 上一帧是否检测到绿色
    consecutive_red_misses = state['consecutive_red_misses']  # 连续未检测到红色的帧数
    consecutive_green_misses = state['consecutive_green_misses']  # 连续未检测到绿色的帧数
    last_img_cv_gray = state['last_img_cv_gray']  # 上一帧的灰度图像
    
    # 初始化点坐标（未检测到时为(-1, -1)）
    red_point = (-1, -1)
    green_point = (-1, -1)
    
    # 将MaixPy图像转换为OpenCV格式（RGB顺序）
    img_cv = image.image2cv(img, False, False)
    
    # 如果是第一帧，只保存灰度图（无法进行帧间差分）
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
    
    # 计算当前帧灰度图（用于下一帧的差分计算）
    img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # === 帧间差分法检测移动物体 ===
    # 对当前帧和上一帧应用高斯模糊（5x5核），减少噪声影响
    current_blur = cv2.GaussianBlur(img_cv_gray, (5, 5), 0)
    last_blur = cv2.GaussianBlur(last_img_cv_gray, (5, 5), 0)
    
    # 计算两帧之间的绝对差异（突出显示移动物体）
    img_diff = cv2.absdiff(current_blur, last_blur)
    
    # === 动态调整阈值 ===
    # 每30帧根据环境亮度调整一次阈值（适应不同光照条件）
    if frame_count % 30 == 0:
        # 计算当前帧的平均亮度
        mean_brightness = cv2.mean(img_cv_gray)[0]
        
        # 根据环境亮度调整阈值和最小轮廓面积
        if mean_brightness < 50:   # 暗环境（如夜晚）
            dynamic_threshold = 15  # 较低阈值（更敏感）
            min_contour_area = 2   # 较小的最小面积
        elif mean_brightness < 100: # 中等亮度（如室内）
            dynamic_threshold = 25
            min_contour_area = 4
        else:                      # 明亮环境（如室外）
            dynamic_threshold = 40  # 较高阈值（减少噪声）
            min_contour_area = 6
            
        # 根据运行时间微调（程序启动初期更敏感）
        elapsed_time = time.time() - start_time
        if elapsed_time < 10:  # 前10秒
            dynamic_threshold = max(10, dynamic_threshold - 5)
    
    # 二值化处理：将差异图像转换为二值图像
    _, img_binary = cv2.threshold(img_diff, dynamic_threshold, 255, cv2.THRESH_BINARY)
    
    # 形态学操作：优化二值图像
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    img_binary = cv2.dilate(img_binary, kernel, iterations=1)  # 膨胀（连接邻近区域）
    img_binary = cv2.erode(img_binary, None, iterations=1)    # 腐蚀（消除小噪点）
    
    # 查找轮廓：在二值图像中寻找连续区域
    contours, _ = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 存储候选激光点
    red_candidates = []  # 红色候选点列表 (x, y, weight)
    green_candidates = []  # 绿色候选点列表 (x, y, weight)
    
    # 处理每个检测到的轮廓
    for contour in contours:
        # 计算轮廓面积
        contour_area = cv2.contourArea(contour)
        
        # 面积过滤：排除过大或过小的轮廓
        if contour_area < min_contour_area or contour_area > max_contour_area: 
            continue

        # 计算轮廓矩（用于求中心点）
        M = cv2.moments(contour)
        if M["m00"] == 0:  # 避免除以零错误
            continue
            
        # 计算轮廓中心点坐标
        point_x = int(M["m10"] / M["m00"])
        point_y = int(M["m01"] / M["m00"])
        
        # 获取轮廓的边界矩形
        x, y, w, h = cv2.boundingRect(contour)
        
        # 确保ROI在图像范围内（防止数组越界）
        if y < 0 or x < 0 or y+h >= CAMERA_HEIGHT or x+w >= CAMERA_WIDTH:
            continue
            
        # 提取感兴趣区域(ROI) - 轮廓所在的矩形区域
        roi = img_cv[y:y+h, x:x+w]
        
        # 计算轮廓圆度（衡量轮廓接近圆形的程度）
        perimeter = cv2.arcLength(contour, True)  # 轮廓周长
        if perimeter > 0:
            # 圆度公式: 4*π*面积/周长² (完美的圆=1)
            circularity = 4 * math.pi * contour_area / (perimeter * perimeter)
        else:
            continue  # 周长为零跳过
        
        # 将ROI转换为HSV颜色空间（更适合颜色分析）
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        
        # 计算HSV通道的中值（减少噪声影响）
        h_median = np.median(roi_hsv[:,:,0])  # 色调（Hue）
        s_median = np.median(roi_hsv[:,:,1])  # 饱和度（Saturation）
        v_median = np.median(roi_hsv[:,:,2])  # 亮度（Value）
        
        # === 红色激光点检测 ===
        # 红色在HSV色环上跨越0°和180°（两个范围）
        red_condition = (
            (RED_H_THRESH_LOW <= h_median <= RED_H_THRESH_HIGH) or 
            (RED_H_THRESH_LOW2 <= h_median <= RED_H_THRESH_HIGH2)
        )
        
        if red_condition:
            # 额外条件：饱和度、亮度和圆度
            if (s_median > RED_MIN_SAT and 
                v_median > RED_MIN_VAL and 
                circularity > RED_MIN_CIRCULARITY):
                # 计算权重（亮度越高、圆度越高，权重越大）
                weight = v_median * (1 + circularity)
                red_candidates.append((point_x, point_y, weight))
        
        # === 绿色激光点检测 ===
        elif GREEN_H_THRESH_LOW <= h_median <= GREEN_H_THRESH_HIGH:
            if (s_median > GREEN_MIN_SAT and 
                v_median > GREEN_MIN_VAL and 
                circularity > GREEN_MIN_CIRCULARITY):
                # 绿色点权重仅基于亮度
                weight = v_median
                green_candidates.append((point_x, point_y, weight))
    
    # === 处理红色候选点 ===
    current_red = (-1, -1)
    if red_candidates:
        # 按权重降序排序（选择最可能是激光点的候选）
        red_candidates.sort(key=lambda x: x[2], reverse=True)
        best_red = red_candidates[0]
        current_red = (best_red[0], best_red[1])
        last_red_detected = True
        consecutive_red_misses = 0  # 重置连续未检测计数器
        
        # 更新历史记录（用于轨迹平滑）
        red_history.append(current_red)
        if len(red_history) > HISTORY_SIZE:
            red_history.pop(0)  # 保持历史记录大小
            
        # 计算平均位置（平滑轨迹）
        avg_x = sum(p[0] for p in red_history) / len(red_history)
        avg_y = sum(p[1] for p in red_history) / len(red_history)
        red_point = (int(avg_x), int(avg_y))
    else:
        # 未检测到红色点
        consecutive_red_misses += 1
        if consecutive_red_misses > 2:  # 连续3帧未检测到
            last_red_detected = False
    
    # === 处理绿色候选点 ===（逻辑同上）
    current_green = (-1, -1)
    if green_candidates:
        green_candidates.sort(key=lambda x: x[2], reverse=True)
        best_green = green_candidates[0]
        current_green = (best_green[0], best_green[1])
        last_green_detected = True
        consecutive_green_misses = 0
        
        green_history.append(current_green)
        if len(green_history) > HISTORY_SIZE:
            green_history.pop(0)
            
        avg_x = sum(p[0] for p in green_history) / len(green_history)
        avg_y = sum(p[1] for p in green_history) / len(green_history)
        green_point = (int(avg_x), int(avg_y))
    else:
        consecutive_green_misses += 1
        if consecutive_green_misses > 2:
            last_green_detected = False
    
    # === 位置预测机制 ===
    # 当激光点暂时消失时，使用历史位置预测
    if not last_red_detected and red_history:
        red_point = red_history[-1]  # 使用最后记录的位置
    
    if not last_green_detected and green_history:
        green_point = green_history[-1]
    
    # 返回检测结果和更新后的状态
    return (red_point, green_point), {
        'last_img_cv_gray': img_cv_gray,  # 保存当前帧灰度图用于下一帧
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
        # 根据是否实际检测到选择颜色
        color = COLOR_RED if last_red_detected else COLOR_RED_PRED
        label = "R" if last_red_detected else "R?"  # 预测位置加问号
        # 绘制十字标记
        img.draw_cross(red_point[0], red_point[1], color, 5, 2)
        # 在标记旁绘制标签
        img.draw_string(red_point[0] + 5, red_point[1] - 10, label, color, scale=1.2)
    
    if green_point != (-1, -1):
        color = COLOR_GREEN if last_green_detected else COLOR_GREEN_PRED
        label = "G" if last_green_detected else "G?"
        img.draw_cross(green_point[0], green_point[1], color, 5, 2)
        img.draw_string(green_point[0] + 5, green_point[1] - 10, label, color, scale=1.2)
    
    # 在图像底部显示坐标信息
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

def main():
    """主函数"""
    # 初始化摄像头和显示屏
    cam = camera.Camera(CAMERA_WIDTH, CAMERA_HEIGHT) 
    disp = display.Display()
    
    # 初始化状态字典
    state = {
        'last_img_cv_gray': None,  # 上一帧灰度图像
        'dynamic_threshold': 20,   # 初始动态阈值
        'min_contour_area': 2,     # 初始最小轮廓面积
        'max_contour_area': 400,   # 最大轮廓面积
        'frame_count': 0,           # 帧计数器
        'start_time': time.time(),  # 程序开始时间
        'red_history': [],          # 红色点历史位置
        'green_history': [],        # 绿色点历史位置
        'last_red_detected': False, # 上一帧是否检测到红色
        'last_green_detected': False, # 上一帧是否检测到绿色
        'consecutive_red_misses': 0, # 连续未检测到红色的帧数
        'consecutive_green_misses': 0 # 连续未检测到绿色的帧数
    }
    
    print("Starting laser point detection...")
    print("Press Ctrl+C to exit")
    
    # 主循环
    while not app.need_exit():
        # 读取图像
        img = cam.read()
        
        # 检测激光点
        (red_point, green_point), state = detect_laser_points(img, state)
        
        # 在终端打印坐标（每5帧打印一次，避免过于频繁）
        if state['frame_count'] % 5 == 0:
            print_coordinates(red_point, green_point)
        
        # 在图像上绘制结果
        draw_results(
            img, 
            red_point, 
            green_point, 
            state['last_red_detected'], 
            state['last_green_detected']
        )
        
        # 显示图像
        disp.show(img)
        
        # 添加短暂延迟（降低CPU使用率）
        time.sleep(0.01)

if __name__ == "__main__":
    main()