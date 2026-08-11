from maix import camera, image
from gui import GUI
import cv2
import numpy as np

class ColorMode:
    HSV = 0
    LAB = 1
class ValueMode:
    Min = 0
    Max = 1

_btn_mode = -1
_btn_ch1 = -1
_btn_ch2 = -1
_btn_ch3 = -1
_btn_binary = -1
_slider_id = -1

_context = {
    'color_mode': ColorMode.LAB,
    'value_mode': ValueMode.Min,
    'current_ch': 1,

    'disp_binary': False,

    'threshold_lab': [0, 100, -128, 127, -128, 127],
    'threshold_hsv': [0, 180, 0, 255, 0, 255]
}

gui = GUI()

def rgb_to_hsv(r, g, b):
    # OpenCV 默认使用 BGR 顺序，需将 RGB 转换为 BGR
    bgr_pixel = np.uint8([[[b, g, r]]])  # 输入顺序：B, G, R
    hsv_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2HSV)
    h, s, v = hsv_pixel[0][0]
    return h, s, v

def rgb_to_lab(r, g, b):
    # 将 RGB 转换为 BGR 格式（OpenCV 默认顺序）
    bgr_pixel = np.uint8([[[b, g, r]]])
    
    # 转换为 Lab（输入需为 BGR 且范围 [0, 255]）
    lab_pixel = cv2.cvtColor(bgr_pixel, cv2.COLOR_BGR2LAB)
    l, a, b = lab_pixel[0][0]
    
    # OpenCV 的 Lab 范围：
    # L: [0, 100] → 映射到 [0, 255]，需转换回 [0, 100]
    # a: [42, 226] → 对应 [-128, 127]
    # b: [20, 223] → 对应 [-128, 127]
    l = int(l * (100 / 255))
    a = a - 128
    b = b - 128
    return l, a, b

def btn_pressed(btn_id, state):
    '''
    按键回调函数，按键按下的时候会自动调用
    '''
    global _btn_mode, _btn_ch1, _btn_ch2, _btn_ch3, _btn_binary, _slider_id, _context
    if state == 1:
        return

    text = ''
    if btn_id == _btn_mode:
        if _context['color_mode'] == ColorMode.LAB:
            text = 'HSV'
            _context['color_mode'] = ColorMode.HSV
            gui.setButtonLabel(_btn_ch1, 'H Min')
            gui.setButtonLabel(_btn_ch2, 'S Min')
            gui.setButtonLabel(_btn_ch3, 'V Min')
            gui.setSliderLabel(_slider_id, 'H Min')
        else:
            text = 'LAB'
            _context['color_mode'] = ColorMode.LAB
            gui.setButtonLabel(_btn_ch1, 'L Min')
            gui.setButtonLabel(_btn_ch2, 'A Min')
            gui.setButtonLabel(_btn_ch3, 'B Min')
            gui.setSliderLabel(_slider_id, 'L Min')
        gui.setButtonLabel(btn_id, text)
        _context['current_ch'] = 1
        _context['value_mode'] = ValueMode.Min
    elif btn_id == _btn_ch1:
        if _context['value_mode'] == ValueMode.Min:
            _context['value_mode'] = ValueMode.Max
            if _context['color_mode'] == ColorMode.LAB:
                text = 'L Max'
                slider_value = _context['threshold_lab'][1] 
            else:
                text = 'H Max'
                slider_value = int(_context['threshold_hsv'][1]/180*100)
        else:
            _context['value_mode'] = ValueMode.Min
            if _context['color_mode'] == ColorMode.LAB:
                text = 'L Min'
                slider_value = _context['threshold_lab'][0]
            else:
                text = 'H Min'
                slider_value = int(_context['threshold_hsv'][0]/180*100 )
        gui.setButtonLabel(btn_id, text)
        gui.setSliderLabel(_slider_id, text)
        gui.setSliderValue(_slider_id, slider_value)
        _context['current_ch'] = 1
    elif btn_id == _btn_ch2:
        if _context['value_mode'] == ValueMode.Min:
            _context['value_mode'] = ValueMode.Max
            if _context['color_mode'] == ColorMode.LAB:
                text = 'A Max'
                slider_value = int((_context['threshold_lab'][3] + 128)/255*100)
            else:
                text = 'S Max'
                slider_value = int(_context['threshold_hsv'][3]/255*100)
        else:
            _context['value_mode'] = ValueMode.Min
            if _context['color_mode'] == ColorMode.LAB:
                text = 'A Min'
                slider_value = int((_context['threshold_lab'][2] + 128)/255*100) 
            else:
                text = 'S Min'
                slider_value = int(_context['threshold_hsv'][2]/255*100)
        gui.setButtonLabel(btn_id, text)
        gui.setSliderLabel(_slider_id, text)
        gui.setSliderValue(_slider_id, slider_value)
        _context['current_ch'] = 2 
    elif btn_id == _btn_ch3:
        if _context['value_mode'] == ValueMode.Min:
            _context['value_mode'] = ValueMode.Max
            if _context['color_mode'] == ColorMode.LAB:
                text = 'B Max'
                slider_value = int((_context['threshold_lab'][5] + 128)/255*100) 
            else:
                text = 'V Max'
                slider_value = int(_context['threshold_hsv'][5]/255*100)
        else:
            _context['value_mode'] = ValueMode.Min
            if _context['color_mode'] == ColorMode.LAB:
                text = 'B Min'
                slider_value = int((_context['threshold_lab'][4] + 128)/255*100) 
            else:
                text = 'V Min'
                slider_value = int(_context['threshold_hsv'][4]/255*100)
        gui.setButtonLabel(btn_id, text)  
        gui.setSliderLabel(_slider_id, text)
        gui.setSliderValue(_slider_id, slider_value)
        _context['current_ch'] = 3
    elif btn_id == _btn_binary:
        _context['disp_binary'] = not _context['disp_binary']     

def slider_changed(slider_id, value):
    '''
    滑块值改变后的回调函数，会自动调用
    '''
    global _context

    if _context['color_mode'] == ColorMode.LAB:
        if _context['value_mode'] == ValueMode.Min:
            if _context['current_ch'] == 1:
                _context['threshold_lab'][0] = value
            elif _context['current_ch'] == 2:
                _context['threshold_lab'][2] = int(-128 + value*255/100)
            elif _context['current_ch'] == 3:
                _context['threshold_lab'][4] = int(-128 + value*255/100)
        else:
            if _context['current_ch'] == 1:
                _context['threshold_lab'][1] = value
            elif _context['current_ch'] == 2:
                _context['threshold_lab'][3] = int(-128 + value*255/100)
            elif _context['current_ch'] == 3:
                _context['threshold_lab'][5] = int(-128 + value*255/100)
    else:
        if _context['value_mode'] == ValueMode.Min:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][0] = int(value/100*180)
            elif _context['current_ch'] == 2:
                _context['threshold_hsv'][2] = int(value/100*255)
            elif _context['current_ch'] == 3:
                _context['threshold_hsv'][4] = int(value/100*255)
        else:
            if _context['current_ch'] == 1:
                _context['threshold_hsv'][1] = int(value/100*180)
            elif _context['current_ch'] == 2:
                _context['threshold_hsv'][3] = int(value/100*255)
            elif _context['current_ch'] == 3:
                _context['threshold_hsv'][5] = int(value/100*255)

def main():
    global _btn_mode, _btn_ch1, _btn_ch2, _btn_ch3, _btn_binary, _slider_id

    # 摄像头初始化
    disp_width  = 320
    disp_height = 240
    cam = camera.Camera(disp_width, disp_height)

    # 创建按钮
    button_height = disp_height//5
    button_width  = 60
    _btn_mode = gui.createButton(0, 0, button_width, button_height, 'LAB')
    gui.setButtonCallback(_btn_mode, btn_pressed)

    _btn_ch1 = gui.createButton(0, button_height, button_width, button_height, 'L Min')
    gui.setButtonCallback(_btn_ch1, btn_pressed)

    _btn_ch2 = gui.createButton(0, 2*button_height, button_width, button_height, 'A Min')
    gui.setButtonCallback(_btn_ch2, btn_pressed)

    _btn_ch3 = gui.createButton(0, 3*button_height, button_width, button_height, 'B Min')
    gui.setButtonCallback(_btn_ch3, btn_pressed)

    _btn_binary = gui.createButton(0, 4*button_height, button_width, button_height, '二值化')
    gui.setButtonCallback(_btn_binary, btn_pressed)

    # 创建滑动条
    _slider_id = gui.createSlider(80, 200, 220, 20, label='L Min')
    gui.setSliderCallback(_slider_id, slider_changed)

    while True:
        # 1. 获取图像
        img = cam.read()

        # 2. 根据颜色模式，可进行阈值调整
        if _context['color_mode'] == ColorMode.LAB:
            blobs = img.find_blobs(thresholds = [_context['threshold_lab']], pixels_threshold=500)
            for blob in blobs:
                img.draw_rect(blob[0], blob[1], blob[2], blob[3], image.COLOR_BLUE)

            if _context['disp_binary']:
                img = img.binary([_context['threshold_lab']])

        else:
            frame = image.image2cv(img, ensure_bgr=False, copy=False)

            # 转换为HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            
            # 生成掩膜
            lower = np.array([_context['threshold_hsv'][0], _context['threshold_hsv'][2], _context['threshold_hsv'][4]])
            upper = np.array([_context['threshold_hsv'][1], _context['threshold_hsv'][3], _context['threshold_hsv'][5]])
            mask = cv2.inRange(hsv, lower, upper)
            
            # 检测轮廓
            contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            if len(contours) > 0:
                c = max(contours, key=cv2.contourArea)
                x,y,w,h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (255, 0, 0), 2)
            if _context['disp_binary']:
                img = image.cv2image(mask, bgr=False, copy=False)
            else:
                img = image.cv2image(frame, bgr=False, copy=False)
        
        if not _context['disp_binary']:
            # 3. 获取触摸点颜色值
            pixel_x = disp_width//2
            pixel_y = disp_height//2
            pixel = img.get_pixel(pixel_x, pixel_y, True)
            if _context['color_mode'] == ColorMode.LAB:
                value_l,value_a,value_b = rgb_to_lab(pixel[0], pixel[1], pixel[2])
                img.draw_string(65, 5, '颜色值:{:4d},{:4d},{:4d}'.format(value_l, value_a, value_b), image.COLOR_BLUE)    
            else:
                value_h,value_s,value_v = rgb_to_hsv(pixel[0], pixel[1], pixel[2])
                img.draw_string(65, 5, '颜色值:{:4d},{:4d},{:4d}'.format(value_h, value_s, value_v), image.COLOR_BLUE)
            img.draw_cross(pixel_x, pixel_y, image.COLOR_BLUE, 5)  


            # 4. 图像显示及GUI框架刷新
            if _context['color_mode'] == ColorMode.LAB:
                img.draw_string(65, 20, '阈值    :{:4d},{:4d},{:4d},{:4d},{:4d},{:4d}'
                                                .format(_context['threshold_lab'][0],
                                                _context['threshold_lab'][1],
                                                _context['threshold_lab'][2],
                                                _context['threshold_lab'][3],
                                                _context['threshold_lab'][4],
                                                _context['threshold_lab'][5]), image.COLOR_BLUE)
            else:
                img.draw_string(65, 20, '阈值    :{:4d},{:4d},{:4d},{:4d},{:4d},{:4d}'
                                                .format(_context['threshold_hsv'][0],
                                                _context['threshold_hsv'][1],
                                                _context['threshold_hsv'][2],
                                                _context['threshold_hsv'][3],
                                                _context['threshold_hsv'][4],
                                                _context['threshold_hsv'][5]), image.COLOR_BLUE)

                  
        gui.run(img)

if __name__ == '__main__':
    main()