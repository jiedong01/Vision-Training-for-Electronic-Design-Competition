from maix import image, camera, display, app, touchscreen
import cv2
import time
import math
import numpy as np
import json
import os

# ========================= GUI组件 =========================
class GUI:
    def __init__(self) -> None:
        self.background = None
        self.buttons = list()     # 存储按钮组件
        self.sliders = list()     # 存储滑动条组件
        self.button_callbacks = list()  # 按钮回调函数
        self.slider_callbacks = list()  # 滑动条回调函数

        self.touch_x = 0
        self.touch_y = 0
        self.dragging_slider = None  # 当前拖动的滑动条ID

        image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf")
        image.set_default_font("sourcehansans")

        self._ts = touchscreen.TouchScreen()
        self._disp = display.Display()
        self._last_pressed = 0

    def _is_in_button(self, button_id: int, x: int, y: int) -> bool:
        '''
        判断坐标是否在按钮所在区域之内
        '''
        if button_id >= len(self.buttons) or self.background is None:
            return False
        
        button = self.buttons[button_id]
        button_disp_pos = image.resize_map_pos(
            self.background.width(), self.background.height(),
            self._disp.width(), self._disp.height(),
            image.Fit.FIT_CONTAIN,
            button['x'], button['y'], button['width'], button['height']
        )
        
        return (x > button_disp_pos[0] and x < (button_disp_pos[0]+button_disp_pos[2])) and \
               (y > button_disp_pos[1] and y < (button_disp_pos[1]+button_disp_pos[3]))

    def _is_in_slider(self, slider_id: int, x: int, y: int) -> bool:
        '''
        判断坐标是否在滑块所在区域之内
        '''
        if slider_id >= len(self.sliders) or self.background is None:
            return False
        
        slider = self.sliders[slider_id]
        slider_disp_pos = image.resize_map_pos(
            self.background.width(), self.background.height(),
            self._disp.width(), self._disp.height(),
            image.Fit.FIT_CONTAIN,
            slider['x'], slider['y'], slider['width'], slider['height']
        )
        
        # 扩展10像素区域,使得在触摸两端的时候能够方便达到极值位置
        if slider['vertical']:
            return (x >= slider_disp_pos[0] and x <= (slider_disp_pos[0]+slider_disp_pos[2])) and \
                   (y >= slider_disp_pos[1]-10 and y <= (slider_disp_pos[1]+slider_disp_pos[3]+10))
        else:
            return (x >= slider_disp_pos[0]-10 and x <= (slider_disp_pos[0]+slider_disp_pos[2]+10)) and \
                   (y >= slider_disp_pos[1] and y <= (slider_disp_pos[1]+slider_disp_pos[3]))

    def createButton(self, x: int, y: int, width: int, height: int, label: str = '', bkground_color = image.COLOR_YELLOW, text_color = image.COLOR_WHITE) -> int:
        '''
        创建按钮
        '''
        button_id = len(self.buttons)
        self.buttons.append({
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'label': label,
            'bkground_color': bkground_color,
            'text_color': text_color
        })
        self.button_callbacks.append(None)
        return button_id

    def createSlider(self, x: int, y: int, width: int, height: int, min_val: int=0, max_val: int=100, vertical=False, label: str = '', track_color = image.COLOR_YELLOW, slider_color = image.COLOR_WHITE) -> int:
        '''
        创建滑块
        '''
        slider_id = len(self.sliders)
        self.sliders.append({
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'min': min_val,
            'max': max_val,
            'value': min_val,
            'slider_size': 20,
            'label': label,
            'vertical': vertical,
            'track_color': track_color,
            'slider_color': slider_color
        })
        self.slider_callbacks.append(None)
        return slider_id

    def setButtonCallback(self, button_id: int, cb) -> None:
        '''
        设置按钮的回调函数
        '''
        if button_id >= len(self.buttons):
            return
        self.button_callbacks[button_id] = cb

    def setSliderCallback(self, slider_id: int, cb) -> None:
        '''
        设置滑块的回调函数
        '''
        if slider_id >= len(self.sliders):
            return
        self.slider_callbacks[slider_id] = cb

    def getTouch(self) -> tuple:
        '''
        获取当前触摸的位置坐标
        '''
        if self.background is None:
            return (0, 0)
            
        x, y = image.resize_map_pos_reverse(
            self.background.width(), self.background.height(),
            self._disp.width(), self._disp.height(),
            image.Fit.FIT_CONTAIN,
            self.touch_x, self.touch_y
        )
        x = x if x >= 0 else 0
        y = y if y >= 0 else 0
        return (x, y)
    
    def setButtonLabel(self, button_id: int, label: str):
        '''
        设置按钮所显示文字
        '''
        if button_id >= len(self.buttons):
            return False
        
        self.buttons[button_id]['label'] = label
        return True
    
    def setSliderLabel(self, slider_id: int, label: str):
        '''
        设置滑块所显示文字
        '''
        if slider_id >= len(self.sliders):
            return False
        
        self.sliders[slider_id]['label'] = label
        return True
    
    def setSliderValue(self, slider_id: int , value:int):
        '''
        设置滑块当前位置
        '''
        if slider_id >= len(self.sliders) or value < 0 or value > 100:
            return False
        
        self.sliders[slider_id]['value'] = value
        return True

    def run(self, background: image.Image) -> None:
        self.background = background
        self.touch_x, self.touch_y, pressed = self._ts.read()

        # 处理按钮触摸事件
        if self._last_pressed != pressed:
            self._last_pressed = pressed
            for button_id in range(len(self.buttons)):
                if self._is_in_button(button_id, self.touch_x, self.touch_y):
                    if self.button_callbacks[button_id] is not None:
                        self.button_callbacks[button_id](button_id, pressed)
                    break

        # 处理滑动条触摸事件
        for slider_id in range(len(self.sliders)):
            if pressed:
                if self._is_in_slider(slider_id, self.touch_x, self.touch_y):
                    slider = self.sliders[slider_id]
                    disp_pos = image.resize_map_pos(
                        self.background.width(), self.background.height(),
                        self._disp.width(), self._disp.height(),
                        image.Fit.FIT_CONTAIN,
                        slider['x'], slider['y'], slider['width'], slider['height']
                    )

                    # 计算相对坐标
                    if slider['vertical']:
                        # 垂直方向：Y轴坐标决定值
                        ty = self.touch_y - disp_pos[1]
                        total_length = disp_pos[3]  # 轨道长度（height参数）
                        new_value = int(slider['max'] - (ty / total_length) * (slider['max'] - slider['min']))
                    else:
                        # 水平方向：X轴坐标决定值
                        tx = self.touch_x - disp_pos[0]
                        total_length = disp_pos[2]  # 轨道长度（width参数）
                        new_value = int(slider['min'] + (tx / total_length) * (slider['max'] - slider['min']))
                    new_value = max(slider['min'], min(new_value, slider['max']))
                    if slider['value'] != new_value:
                        slider['value'] = new_value
                        if self.slider_callbacks[slider_id] is not None:
                            self.slider_callbacks[slider_id](slider_id, new_value)
                    self.dragging_slider = slider_id
            elif self.dragging_slider == slider_id:
                self.dragging_slider = None

        # 绘制按钮
        for button_id in range(len(self.buttons)):
            label_size = image.string_size(self.buttons[button_id]['label'])
            label_x = (self.buttons[button_id]['x'] + (self.buttons[button_id]['width'] - label_size.width())//2) if self.buttons[button_id]['width'] > label_size.width() else self.buttons[button_id]['x']
            label_y = (self.buttons[button_id]['y'] + (self.buttons[button_id]['height'] - label_size.height())//2) if self.buttons[button_id]['height'] > label_size.height() else self.buttons[button_id]['y']

            self.background.draw_rect(self.buttons[button_id]['x'], self.buttons[button_id]['y'], self.buttons[button_id]['width'], self.buttons[button_id]['height'],  self.buttons[button_id]['bkground_color'], 2)
            if self.buttons[button_id]['label']:
                self.background.draw_string(label_x, label_y, self.buttons[button_id]['label'], self.buttons[button_id]['text_color'])

        # 绘制滑动条
        for slider_id in range(len(self.sliders)):
            slider = self.sliders[slider_id]
            # 绘制轨道
            self.background.draw_rect(
                slider['x'], 
                slider['y'], 
                slider['width'], 
                slider['height'], 
                slider['track_color'], 
                thickness=2  # 填充
            )
            
            if slider['vertical']:
                # 计算滑块位置
                slider_pos = (( slider['max'] - slider['value']) / (slider['max'] - slider['min'])) * (slider['height'] - slider['slider_size'])
                slider_pos = max(0, min(slider_pos, slider['height'] - slider['slider_size']))
                # 绘制滑块
                self.background.draw_rect(
                    slider['x'],
                    int(slider['y'] + slider_pos),
                    slider['width'],
                    slider['slider_size'],
                    slider['slider_color'],
                    -1
                )
                if len(slider['label']) > 0:
                    label_size = image.string_size(slider['label'])
                    self.background.draw_string(slider['x']+slider['width'], slider['y']+slider['height']-label_size.height(), slider['label'], slider['slider_color'] )
            else:
                # 计算滑块位置
                slider_pos = ((slider['value'] - slider['min']) / (slider['max'] - slider['min'])) * (slider['width'] - slider['slider_size'])
                slider_pos = max(0, min(slider_pos, slider['width'] - slider['slider_size']))
                # 绘制滑块
                self.background.draw_rect(
                    int(slider['x'] + slider_pos),
                    slider['y'],
                    slider['slider_size'],
                    slider['height'],
                    slider['slider_color'],
                    -1
                )
                if len(slider['label']) > 0:
                    label_size = image.string_size(slider['label'])
                    self.background.draw_string(slider['x'], slider['y']-label_size.height(), slider['label'], slider['slider_color'] )

        self._disp.show(self.background)

# ========================= 颜色空间定义 =========================
class ColorMode:
    HSV = 0
    LAB = 1

class ValueMode:
    Min = 0
    Max = 1

# ========================= 激光点识别模块 =========================
# 定义全局常量
CAMERA_WIDTH = 240
CAMERA_HEIGHT = 240
HISTORY_SIZE = 3
COLOR_BLUE = image.COLOR_BLUE
COLOR_BLUE_PRED = image.Color(100, 100, 200)
COLOR_WHITE = image.COLOR_WHITE

# 默认颜色阈值配置（HSV空间）
BLUE_H_THRESH_LOW = 100
BLUE_H_THRESH_HIGH = 140
BLUE_MIN_SAT = 40
BLUE_MIN_VAL = 50
BLUE_MIN_CIRCULARITY = 0.5

def rgb_to_hsv(r, g, b):
    bgr_pixel = np.uint8([[[b, g, r]]])
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)
    h, s, v = hsv_pixel[0][0]
    return h, s, v

def rgb_to_lab(r, g, b):
    bgr_pixel = np.uint8([[[b, g, r]]])
    lab_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2LAB)
    l, a, b_val = lab_pixel[0][0]
    l = int(l * (100 / 255))
    a = a - 128
    b_val = b_val - 128
    return l, a, b_val

def detect_laser_point(img, state, blue_thresholds):
    """
    检测图像中的蓝色激光点
    """
    # 从状态字典中提取变量
    dynamic_threshold = state['dynamic_threshold']
    min_contour_area = state['min_contour_area']
    max_contour_area = state['max_contour_area']
    frame_count = state['frame_count']
    start_time = state['start_time']
    blue_history = state['blue_history']
    last_blue_detected = state['last_blue_detected']
    consecutive_blue_misses = state['consecutive_blue_misses']
    last_img_cv_gray = state['last_img_cv_gray']
    
    # 初始化点坐标
    blue_point = (-1, -1)
    
    # 从参数中获取阈值
    blue_h_low, blue_h_high, blue_s_min, blue_v_min = blue_thresholds
    
    # 将MaixPy图像转换为OpenCV格式
    img_cv = image.image2cv(img, False, False)
    
    # 如果是第一帧，只保存灰度图
    if last_img_cv_gray is None:
        img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
        return blue_point, {
            'last_img_cv_gray': img_cv_gray,
            'dynamic_threshold': dynamic_threshold,
            'min_contour_area': min_contour_area,
            'max_contour_area': max_contour_area,
            'frame_count': frame_count + 1,
            'start_time': start_time,
            'blue_history': blue_history,
            'last_blue_detected': last_blue_detected,
            'consecutive_blue_misses': consecutive_blue_misses
        }
    
    # 计算当前帧灰度图
    img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # 帧间差分法检测移动物体
    current_blur = cv2.GaussianBlur(img_cv_gray, (5, 5), 0)
    last_blur = cv2.GaussianBlur(last_img_cv_gray, (5, 5), 0)
    img_diff = cv2.absdiff(current_blur, last_blur)
    
    # 动态调整阈值
    if frame_count % 30 == 0:
        mean_brightness = cv2.mean(img_cv_gray)[0]
        if mean_brightness < 50:
            dynamic_threshold = 15
            min_contour_area = 2
        elif mean_brightness < 100:
            dynamic_threshold = 25
            min_contour_area = 4
        else:
            dynamic_threshold = 40
            min_contour_area = 6
            
        elapsed_time = time.time() - start_time
        if elapsed_time < 10:
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
    blue_candidates = []
    
    # 处理每个检测到的轮廓
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area < min_contour_area or contour_area > max_contour_area: 
            continue

        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
            
        point_x = int(M["m10"] / M["m00"])
        point_y = int(M["m01"] / M["m00"])
        
        x, y, w, h = cv2.boundingRect(contour)
        if y < 0 or x < 0 or y+h >= CAMERA_HEIGHT or x+w >= CAMERA_WIDTH:
            continue
            
        roi = img_cv[y:y+h, x:x+w]
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            circularity = 4 * math.pi * contour_area / (perimeter * perimeter)
        else:
            continue
        
        roi_hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
        h_median = np.median(roi_hsv[:,:,0])
        s_median = np.median(roi_hsv[:,:,1])
        v_median = np.median(roi_hsv[:,:,2])
        
        # 蓝色激光点检测
        blue_condition = blue_h_low <= h_median <= blue_h_high
        if blue_condition:
            if (s_median > blue_s_min and 
                v_median > blue_v_min and 
                circularity > BLUE_MIN_CIRCULARITY):
                weight = v_median * (1 + circularity)
                blue_candidates.append((point_x, point_y, weight))
    
    # 处理蓝色候选点
    current_blue = (-1, -1)
    if blue_candidates:
        blue_candidates.sort(key=lambda x: x[2], reverse=True)
        best_blue = blue_candidates[0]
        current_blue = (best_blue[0], best_blue[1])
        last_blue_detected = True
        consecutive_blue_misses = 0
        blue_history.append(current_blue)
        if len(blue_history) > HISTORY_SIZE:
            blue_history.pop(0)
        avg_x = sum(p[0] for p in blue_history) / len(blue_history)
        avg_y = sum(p[1] for p in blue_history) / len(blue_history)
        blue_point = (int(avg_x), int(avg_y))
    else:
        consecutive_blue_misses += 1
        if consecutive_blue_misses > 2:
            last_blue_detected = False
    
    # 位置预测机制
    if not last_blue_detected and blue_history:
        blue_point = blue_history[-1]
    
    # 返回检测结果
    return blue_point, {
        'last_img_cv_gray': img_cv_gray,
        'dynamic_threshold': dynamic_threshold,
        'min_contour_area': min_contour_area,
        'max_contour_area': max_contour_area,
        'frame_count': frame_count + 1,
        'start_time': start_time,
        'blue_history': blue_history,
        'last_blue_detected': last_blue_detected,
        'consecutive_blue_misses': consecutive_blue_misses
    }

def draw_laser_result(img, blue_point, last_blue_detected, target_position=None):
    """在图像上绘制激光点位置和坐标"""
    if blue_point != (-1, -1):
        color = COLOR_BLUE if last_blue_detected else COLOR_BLUE_PRED
        label = "定位点" if last_blue_detected else "定位点?"
        
        # 增强十字标记
        img.draw_line(blue_point[0]-8, blue_point[1], blue_point[0]+8, blue_point[1], color, 2)
        img.draw_line(blue_point[0], blue_point[1]-8, blue_point[0], blue_point[1]+8, color, 2)
        
        img.draw_string(blue_point[0] + 5, blue_point[1] - 10, label, color, scale=1.2)
    
    # 绘制目标位置（如果存在）
    if target_position and target_position != (-1, -1):
        img.draw_circle(target_position[0], target_position[1], 5, image.COLOR_RED, thickness=-1)
        img.draw_string(target_position[0] + 10, target_position[1] - 20, "目标", image.COLOR_RED, scale=1.0)
        
        # 如果检测到定位点，绘制连接线
        if blue_point != (-1, -1):
            img.draw_line(blue_point[0], blue_point[1], target_position[0], target_position[1], image.COLOR_GREEN, 1)
            
            # 计算距离和角度
            dx = target_position[0] - blue_point[0]
            dy = target_position[1] - blue_point[1]
            distance = int(math.sqrt(dx*dx + dy*dy))
            angle = int(math.degrees(math.atan2(dy, dx)))
            
            img.draw_string(5, img.height() - 40, f"距离: {distance}px", image.COLOR_GREEN, scale=1.0)
            img.draw_string(5, img.height() - 20, f"角度: {angle}°", image.COLOR_GREEN, scale=1.0)
    
    # 显示定位点坐标
    if blue_point != (-1, -1):
        img.draw_string(5, 5, f"定位点: ({blue_point[0]}, {blue_point[1]})", color, scale=1.0)
    else:
        img.draw_string(5, 5, "定位点: 未检测到", image.COLOR_BLUE, scale=1.0)

# ========================= 主程序 =========================
# 全局上下文
_context = {
    'color_mode': ColorMode.HSV,
    'value_mode': ValueMode.Min,
    'current_ch': 1,
    'disp_binary': False,
    'mode': 0,  # 0:阈值调试模式, 1:定位模式
    'threshold_hsv': [BLUE_H_THRESH_LOW, BLUE_H_THRESH_HIGH, BLUE_MIN_SAT, BLUE_MIN_VAL],
    'laser_state': None,
    'target_position': None  # 目标物体位置
}

# 全局GUI实例
gui = GUI()
_btn_mode = -1
_btn_ch1 = -1
_btn_binary = -1
_btn_detect = -1
_btn_set_target = -1
_slider_id = -1

# 保存和加载阈值配置
def save_thresholds():
    with open('laser_thresholds.json', 'w') as f:
        json.dump(_context['threshold_hsv'], f)
    print("阈值已保存")

def load_thresholds():
    try:
        if os.path.exists('laser_thresholds.json'):
            with open('laser_thresholds.json', 'r') as f:
                _context['threshold_hsv'] = json.load(f)
            print("阈值已加载")
            return True
    except:
        pass
    return False

# 初始化激光点识别状态
def init_laser_state():
    return {
        'last_img_cv_gray': None,
        'dynamic_threshold': 20,
        'min_contour_area': 2,
        'max_contour_area': 400,
        'frame_count': 0,
        'start_time': time.time(),
        'blue_history': [],
        'last_blue_detected': False,
        'consecutive_blue_misses': 0
    }

# 按钮回调函数
def btn_pressed(btn_id, state):
    global _context
    if state == 1:
        return

    if btn_id == _btn_mode:
        if _context['color_mode'] == ColorMode.LAB:
            text = 'HSV'
            _context['color_mode'] = ColorMode.HSV
            gui.setButtonLabel(_btn_ch1, 'H Min')
            gui.setSliderLabel(_slider_id, 'H Min')
        else:
            text = 'LAB'
            _context['color_mode'] = ColorMode.LAB
            gui.setButtonLabel(_btn_ch1, 'L Min')
            gui.setSliderLabel(_slider_id, 'L Min')
        gui.setButtonLabel(btn_id, text)
        _context['current_ch'] = 1
        _context['value_mode'] = ValueMode.Min
    elif btn_id == _btn_ch1:
        if _context['value_mode'] == ValueMode.Min:
            _context['value_mode'] = ValueMode.Max
            if _context['color_mode'] == ColorMode.LAB:
                text = 'L Max'
                slider_value = _context['threshold_hsv'][1] 
            else:
                text = 'H Max'
                slider_value = int(_context['threshold_hsv'][1]/180*100)
        else:
            _context['value_mode'] = ValueMode.Min
            if _context['color_mode'] == ColorMode.LAB:
                text = 'L Min'
                slider_value = _context['threshold_hsv'][0]
            else:
                text = 'H Min'
                slider_value = int(_context['threshold_hsv'][0]/180*100 )
        gui.setButtonLabel(btn_id, text)
        gui.setSliderLabel(_slider_id, text)
        gui.setSliderValue(_slider_id, slider_value)
        _context['current_ch'] = 1
    elif btn_id == _btn_binary:
        _context['disp_binary'] = not _context['disp_binary']     
    elif btn_id == _btn_detect:
        # 切换模式：阈值调试/定位模式
        _context['mode'] = 1 - _context['mode']
        if _context['mode'] == 0:
            gui.setButtonLabel(btn_id, "定位模式")
            _context['laser_state'] = None  # 重置识别状态
        else:
            gui.setButtonLabel(btn_id, "调试模式")
            save_thresholds()  # 保存当前阈值
    elif btn_id == _btn_set_target:
        # 设置目标位置为当前触摸位置
        if _context['mode'] == 1:  # 仅在定位模式下设置目标
            touch_x, touch_y = gui.getTouch()
            _context['target_position'] = (int(touch_x), int(touch_y))
            print(f"目标位置设置为: ({touch_x}, {touch_y})")

# 滑块回调函数
def slider_changed(slider_id, value):
    global _context
    if _context['color_mode'] == ColorMode.LAB:
        if _context['value_mode'] == ValueMode.Min:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][0] = value
        else:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][1] = value
    else:
        if _context['value_mode'] == ValueMode.Min:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][0] = int(value/100*180)
        else:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][1] = int(value/100*180)

def main():
    global _btn_mode, _btn_ch1, _btn_binary, _btn_detect, _btn_set_target, _slider_id

    # 初始化摄像头
    disp_width  = 320
    disp_height = 240
    cam = camera.Camera(disp_width, disp_height)

    # 加载阈值配置
    load_thresholds()

    # 创建按钮
    button_height = disp_height//6
    button_width  = 60
    _btn_mode = gui.createButton(0, 0, button_width, button_height, 'HSV')
    gui.setButtonCallback(_btn_mode, btn_pressed)

    _btn_ch1 = gui.createButton(0, button_height, button_width, button_height, 'H Min')
    gui.setButtonCallback(_btn_ch1, btn_pressed)

    _btn_binary = gui.createButton(0, 2*button_height, button_width, button_height, '二值化')
    gui.setButtonCallback(_btn_binary, btn_pressed)

    _btn_detect = gui.createButton(0, 3*button_height, button_width, button_height, '定位模式')
    gui.setButtonCallback(_btn_detect, btn_pressed)
    
    _btn_set_target = gui.createButton(0, 4*button_height, button_width, button_height, '设置目标')
    gui.setButtonCallback(_btn_set_target, btn_pressed)

    # 创建滑动条
    _slider_id = gui.createSlider(80, 200, 220, 20, label='H Min')
    gui.setSliderCallback(_slider_id, slider_changed)
    gui.setSliderValue(_slider_id, int(_context['threshold_hsv'][0]/180*100))

    # 修复：确保在进入定位模式前初始化 laser_state
    _context['laser_state'] = init_laser_state()

    while True:
        img = cam.read()
            
        # 阈值调试模式
        if _context['mode'] == 0:
            frame = image.image2cv(img, ensure_bgr=False, copy=False)
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            
            # 使用当前阈值生成掩膜
            blue_lower = np.array([
                _context['threshold_hsv'][0],  # H_min
                _context['threshold_hsv'][2],  # S_min
                _context['threshold_hsv'][3]   # V_min
            ])
            blue_upper = np.array([
                _context['threshold_hsv'][1],  # H_max
                255,  # S上限
                255   # V上限
            ])
            
            mask = cv2.inRange(hsv, blue_lower, blue_upper)
                
            if _context['disp_binary']:
                img = image.cv2image(mask, bgr=False, copy=False)
            else:
                # 在原图上标记检测区域
                contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
                if len(contours) > 0:
                    for c in contours:
                        if cv2.contourArea(c) > 50:  # 过滤小噪点
                            x, y, w, h = cv2.boundingRect(c)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            
                            # 添加十字标记
                            M = cv2.moments(c)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                cv2.drawMarker(frame, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 10, 2)
                img = image.cv2image(frame, bgr=False, copy=False)
        
        # 定位模式
        else:  
            # 修复：确保状态已初始化
            if _context['laser_state'] is None:
                _context['laser_state'] = init_laser_state()
            
            # 准备阈值参数
            blue_thresholds = (
                _context['threshold_hsv'][0],  # H low
                _context['threshold_hsv'][1],  # H high
                _context['threshold_hsv'][2],  # S min
                _context['threshold_hsv'][3]   # V min
            )
            
            # 检测激光点
            blue_point, _context['laser_state'] = detect_laser_point(
                img, 
                _context['laser_state'], 
                blue_thresholds
            )
            
            # 绘制结果
            draw_laser_result(
                img,
                blue_point,
                _context['laser_state']['last_blue_detected'],
                _context['target_position']  # 传递目标位置
            )
        
        # 显示当前模式
        mode_text = "调试模式" if _context['mode'] == 0 else "定位模式"
        img.draw_string(disp_width - 100, 5, mode_text, image.COLOR_GREEN)
        
        # 运行GUI
        gui.run(img)

if __name__ == '__main__':
    main()