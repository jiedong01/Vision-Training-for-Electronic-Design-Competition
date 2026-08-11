'''
V8 修复版激光点识别模块 (蓝紫色版本)
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
COLOR_BLUE = image.COLOR_BLUE  # 蓝色（用于绘制）
COLOR_PURPLE = image.Color(128, 0, 128)  # 紫色（用于绘制）
COLOR_BLUE_PRED = image.Color(100, 100, 200)  # 浅蓝色（预测位置）
COLOR_PURPLE_PRED = image.Color(180, 100, 180)  # 浅紫色（预测位置）
COLOR_WHITE = image.COLOR_WHITE  # 白色（备用）

# 颜色阈值配置（HSV空间）
# 蓝色在HSV空间中的范围 (H:100-140)
BLUE_H_THRESH_LOW = 100  # 蓝色色调下限
BLUE_H_THRESH_HIGH = 140  # 蓝色色调上限
# 紫色在HSV空间中的范围 (H:130-170)
PURPLE_H_THRESH_LOW = 130  # 紫色色调下限
PURPLE_H_THRESH_HIGH = 170  # 紫色色调上限

# 激光点参数（过滤条件）
BLUE_MIN_SAT = 40  # 蓝色最小饱和度
BLUE_MIN_VAL = 50  # 蓝色最小亮度+
BLUE_MIN_CIRCULARITY = 0.5  # 蓝色最小圆度
PURPLE_MIN_SAT = 30  # 紫色最小饱和度（紫色激光通常饱和度较低）
PURPLE_MIN_VAL = 40  # 紫色最小亮度
PURPLE_MIN_CIRCULARITY = 0.45  # 紫色最小圆度（要求稍低）

def detect_laser_points(img, state):
    """
    检测图像中的蓝色和紫色激光点
    
    核心原理：
    1. 帧间差分法：通过比较当前帧和上一帧的差异，检测移动的激光点
    2. 颜色过滤：在HSV色彩空间中识别蓝色和紫色区域
    3. 形状分析：通过圆度判断斑点形状是否符合激光点特征
    4. 历史轨迹平滑：使用移动平均平滑位置轨迹
    5. 位置预测：当激光点暂时消失时，使用历史位置进行预测
    
    参数:
        img: 当前帧图像 (MaixPy图像对象)
        state: 包含处理状态的字典（跨帧传递信息）
        
    返回:
        (blue_point, purple_point, updated_state): 
            检测到的蓝点和紫点坐标及更新后的状态
    """
    # 从状态字典中提取变量
    dynamic_threshold = state['dynamic_threshold']  # 动态二值化阈值
    min_contour_area = state['min_contour_area']  # 最小轮廓面积
    max_contour_area = state['max_contour_area']  # 最大轮廓面积
    frame_count = state['frame_count']  # 帧计数器
    start_time = state['start_time']  # 程序开始时间
    blue_history = state['blue_history']  # 蓝色点历史位置
    purple_history = state['purple_history']  # 紫色点历史位置
    last_blue_detected = state['last_blue_detected']  # 上一帧是否检测到蓝色
    last_purple_detected = state['last_purple_detected']  # 上一帧是否检测到紫色
    consecutive_blue_misses = state['consecutive_blue_misses']  # 连续未检测到蓝色的帧数
    consecutive_purple_misses = state['consecutive_purple_misses']  # 连续未检测到紫色的帧数
    last_img_cv_gray = state['last_img_cv_gray']  # 上一帧的灰度图像
    
    # 初始化点坐标（未检测到时为(-1, -1)）
    blue_point = (-1, -1)
    purple_point = (-1, -1)
    
    # 将MaixPy图像转换为OpenCV格式（RGB顺序）
    img_cv = image.image2cv(img, False, False)
    
    # 如果是第一帧，只保存灰度图（无法进行帧间差分）
    if last_img_cv_gray is None:
        img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        return (blue_point, purple_point), {
            'last_img_cv_gray': img_cv_gray,
            'dynamic_threshold': dynamic_threshold,
            'min_contour_area': min_contour_area,
            'max_contour_area': max_contour_area,
            'frame_count': frame_count + 1,
            'start_time': start_time,
            'blue_history': blue_history,
            'purple_history': purple_history,
            'last_blue_detected': last_blue_detected,
            'last_purple_detected': last_purple_detected,
            'consecutive_blue_misses': consecutive_blue_misses,
            'consecutive_purple_misses': consecutive_purple_misses
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
    blue_candidates = []  # 蓝色候选点列表 (x, y, weight)
    purple_candidates = []  # 紫色候选点列表 (x, y, weight)
    
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
        
        # === 蓝色激光点检测 ===
        blue_condition = BLUE_H_THRESH_LOW <= h_median <= BLUE_H_THRESH_HIGH
        
        if blue_condition:
            # 额外条件：饱和度、亮度和圆度
            if (s_median > BLUE_MIN_SAT and 
                v_median > BLUE_MIN_VAL and 
                circularity > BLUE_MIN_CIRCULARITY):
                # 计算权重（亮度越高、圆度越高，权重越大）
                weight = v_median * (1 + circularity)
                blue_candidates.append((point_x, point_y, weight))
        
        # === 紫色激光点检测 ===
        elif PURPLE_H_THRESH_LOW <= h_median <= PURPLE_H_THRESH_HIGH:
            if (s_median > PURPLE_MIN_SAT and 
                v_median > PURPLE_MIN_VAL and 
                circularity > PURPLE_MIN_CIRCULARITY):
                # 紫色点权重仅基于亮度
                weight = v_median
                purple_candidates.append((point_x, point_y, weight))
    
    # === 处理蓝色候选点 ===
    current_blue = (-1, -1)
    if blue_candidates:
        # 按权重降序排序（选择最可能是激光点的候选）
        blue_candidates.sort(key=lambda x: x[2], reverse=True)
        best_blue = blue_candidates[0]
        current_blue = (best_blue[0], best_blue[1])
        last_blue_detected = True
        consecutive_blue_misses = 0  # 重置连续未检测计数器
        
        # 更新历史记录（用于轨迹平滑）
        blue_history.append(current_blue)
        if len(blue_history) > HISTORY_SIZE:
            blue_history.pop(0)  # 保持历史记录大小
            
        # 计算平均位置（平滑轨迹）
        avg_x = sum(p[0] for p in blue_history) / len(blue_history)
        avg_y = sum(p[1] for p in blue_history) / len(blue_history)
        blue_point = (int(avg_x), int(avg_y))
    else:
        # 未检测到蓝色点
        consecutive_blue_misses += 1
        if consecutive_blue_misses > 2:  # 连续3帧未检测到
            last_blue_detected = False
    
    # === 处理紫色候选点 ===（逻辑同上）
    current_purple = (-1, -1)
    if purple_candidates:
        purple_candidates.sort(key=lambda x: x[2], reverse=True)
        best_purple = purple_candidates[0]
        current_purple = (best_purple[0], best_purple[1])
        last_purple_detected = True
        consecutive_purple_misses = 0
        
        purple_history.append(current_purple)
        if len(purple_history) > HISTORY_SIZE:
            purple_history.pop(0)
            
        avg_x = sum(p[0] for p in purple_history) / len(purple_history)
        avg_y = sum(p[1] for p in purple_history) / len(purple_history)
        purple_point = (int(avg_x), int(avg_y))
    else:
        consecutive_purple_misses += 1
        if consecutive_purple_misses > 2:
            last_purple_detected = False
    
    # === 位置预测机制 ===
    # 当激光点暂时消失时，使用历史位置预测
    if not last_blue_detected and blue_history:
        blue_point = blue_history[-1]  # 使用最后记录的位置
    
    if not last_purple_detected and purple_history:
        purple_point = purple_history[-1]
    
    # 返回检测结果和更新后的状态
    return (blue_point, purple_point), {
        'last_img_cv_gray': img_cv_gray,  # 保存当前帧灰度图用于下一帧
        'dynamic_threshold': dynamic_threshold,
        'min_contour_area': min_contour_area,
        'max_contour_area': max_contour_area,
        'frame_count': frame_count + 1,
        'start_time': start_time,
        'blue_history': blue_history,
        'purple_history': purple_history,
        'last_blue_detected': last_blue_detected,
        'last_purple_detected': last_purple_detected,
        'consecutive_blue_misses': consecutive_blue_misses,
        'consecutive_purple_misses': consecutive_purple_misses
    }

def print_coordinates(blue, purple):
    """在终端打印激光点坐标"""
    blue_str = f"({blue[0]}, {blue[1]})" if blue != (-1, -1) else "Not found"
    purple_str = f"({purple[0]}, {purple[1]})" if purple != (-1, -1) else "Not found"
    print(f"Blue: {blue_str}\tPurple: {purple_str}")

def draw_results(img, blue_point, purple_point, last_blue_detected, last_purple_detected):
    """在图像上绘制激光点位置和坐标"""
    # 绘制激光点位置
    if blue_point != (-1, -1):
        # 根据是否实际检测到选择颜色
        color = COLOR_BLUE if last_blue_detected else COLOR_BLUE_PRED
        label = "B" if last_blue_detected else "B?"  # 预测位置加问号
        # 绘制十字标记
        img.draw_cross(blue_point[0], blue_point[1], color, 5, 2)
        # 在标记旁绘制标签
        img.draw_string(blue_point[0] + 5, blue_point[1] - 10, label, color, scale=1.2)
    
    if purple_point != (-1, -1):
        color = COLOR_PURPLE if last_purple_detected else COLOR_PURPLE_PRED
        label = "P" if last_purple_detected else "P?"
        img.draw_cross(purple_point[0], purple_point[1], color, 5, 2)
        img.draw_string(purple_point[0] + 5, purple_point[1] - 10, label, color, scale=1.2)
    
    # 在图像底部显示坐标信息
    if blue_point != (-1, -1):
        img.draw_string(5, img.height() - 40, f"Blue: ({blue_point[0]}, {blue_point[1]})", 
                       COLOR_BLUE, scale=1.0)
    else:
        img.draw_string(5, img.height() - 40, "Blue: Not found", 
                       COLOR_BLUE, scale=1.0)
    
    if purple_point != (-1, -1):
        img.draw_string(5, img.height() - 20, f"Purple: ({purple_point[0]}, {purple_point[1]})", 
                       COLOR_PURPLE, scale=1.0)
    else:
        img.draw_string(5, img.height() - 20, "Purple: Not found", 
                       COLOR_PURPLE, scale=1.0)

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
        'blue_history': [],          # 蓝色点历史位置
        'purple_history': [],        # 紫色点历史位置
        'last_blue_detected': False, # 上一帧是否检测到蓝色
        'last_purple_detected': False, # 上一帧是否检测到紫色
        'consecutive_blue_misses': 0, # 连续未检测到蓝色的帧数
        'consecutive_purple_misses': 0 # 连续未检测到紫色的帧数
    }
    
    print("Starting laser point detection (Blue & Purple)...")
    print("Press Ctrl+C to exit")
    
    # 主循环
    while not app.need_exit():
        # 读取图像
        img = cam.read()
        
        # 检测激光点
        (blue_point, purple_point), state = detect_laser_points(img, state)
        
        # 在终端打印坐标（每5帧打印一次，避免过于频繁）
        if state['frame_count'] % 5 == 0:
            print_coordinates(blue_point, purple_point)
        
        # 在图像上绘制结果
        draw_results(
            img, 
            blue_point, 
            purple_point, 
            state['last_blue_detected'], 
            state['last_purple_detected']
        )
        
        # 显示图像
        disp.show(img)
        
        # 添加短暂延迟（降低CPU使用率）
        time.sleep(0.01)

if __name__ == "__main__":
    main()