from maix import touchscreen, camera, display, image, time
from maix.image import Image
import math

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

    def run(self, background: Image) -> None:
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

if __name__ == '__main__':
    def btn_pressed(btn_id, state):
        print('Button {} state: {}'.format(btn_id, state))

    def slider_changed(slider_id, value):
        print('Slider {} value: {:.1f}'.format(slider_id, value))

    disp_width = 320
    disp_height = 240
    cam = camera.Camera(disp_width, disp_height)
    
    gui = GUI()
    # 创建按钮
    btn_id1 = gui.createButton(disp_width-60, disp_height-40, 60, 40, '按钮1')
    gui.setButtonCallback(btn_id1, btn_pressed)

    btn_id2 = gui.createButton(disp_width-60, 0, 60, 40, '按钮2')
    gui.setButtonCallback(btn_id2, btn_pressed)

    # 创建滑动条
    slider_id_h = gui.createSlider(100, 120, 200, 20, label='横向')
    gui.setSliderValue(slider_id_h, 50)
    gui.setSliderCallback(slider_id_h, slider_changed)

    slider_id_v = gui.createSlider(40, 20, 20, 200, vertical=True, label = 'vertical')
    gui.setSliderCallback(slider_id_v, slider_changed)

    while True:
        img = cam.read()
        gui.run(img)