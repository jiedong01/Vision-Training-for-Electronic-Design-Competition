
from maix import touchscreen, camera, display, image, time
from maix.image import Image
import math

class GUI:
    def __init__(self) -> None:
        self.background = None
        self.items      = list()
        self.callbacks  = list()
        self.labels     = list()

        self.touch_x = 0
        self.touch_y = 0

        image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf")
        #print("fonts:", image.fonts())
        image.set_default_font("sourcehansans")

        self._ts   = touchscreen.TouchScreen()
        self._disp = display.Display()
        self._last_pressed = 0

    def _is_in_item(self, item_id : int, x : int, y : int) -> bool:
        if item_id >= len(self.items) or self.background == None:
            return False
        
        item_pos = self.items[item_id]
        item_disp_pos = image.resize_map_pos(self.background.width(), self.background.height(), self._disp.width(), self._disp.height(), image.Fit.FIT_CONTAIN, item_pos[0], item_pos[1], item_pos[2], item_pos[3])
        
        if x > item_disp_pos[0] and x < (item_disp_pos[0]+item_disp_pos[2]) and y > item_disp_pos[1] and y < (item_disp_pos[1]+item_disp_pos[3]):
            return True
        else:
            return False

    def createButton(self, x : int, y:int, width : int, height : int) -> int:
        '''
        创建一个按钮组件，参数为按钮的位置坐标
        '''
        item_id = len(self.items)
        self.items.append([x, y, width, height])
        self.callbacks.append(None)
        self.labels.append(None)
        return item_id

    def setItemCallback(self, item_id : int, cb ) -> None:
        '''
        设置界面组件的回调函数，比如按钮按下时所自动调用的函数
        该回调函数原型如下:
        callback(item_id : int) -> None
        '''
        if item_id >= len(self.items):
            return
        self.callbacks[item_id] = cb

    def setItemLabel(self, item_id : int, label : str) -> None:
        '''
        设置界面组件中所显示信息
        '''
        if item_id >= len(self.items):
            return
        self.labels[item_id] = label

    def get_touch(self) -> tuple:
        '''
        返回最近时间触摸动作的位置
        '''
        if self.background == None:
            return (0,0)
            
        x, y = image.resize_map_pos_reverse(self.background.width(), self.background.height(), self._disp.width(), self._disp.height(), image.Fit.FIT_CONTAIN, self.touch_x, self.touch_y)
        x = x if x >= 0 else 0
        y = y if y >= 0 else 0
        return (x, y)

    def run(self, background : Image) -> None:
        self.background = background
        self.touch_x, self.touch_y, pressed = self._ts.read()
        # 检测按键输入
        if self._last_pressed != pressed:
            self._last_pressed = pressed

            for id in range(len(self.items)):
                if self._is_in_item(id, self.touch_x, self.touch_y):
                    if self.callbacks[id] != None:
                        self.callbacks[id](id, pressed)
                    break

        # 更新界面元素
        for id in range(len(self.items)):
            label_size = image.string_size(self.labels[id])
            label_x = (self.items[id][0] + (self.items[id][2] - label_size.width())//2) if self.items[id][2] > label_size.width() else self.items[id][0]
            label_y = (self.items[id][1] + (self.items[id][3] - label_size.height())//2) if self.items[id][3] > label_size.height() else self.items[id][1]

            self.background.draw_rect(self.items[id][0], self.items[id][1], self.items[id][2], self.items[id][3], image.COLOR_RED, 2)
            if self.labels[id] != None:
                self.background.draw_string(label_x, label_y, self.labels[id], image.COLOR_WHITE)

        self._disp.show(self.background)

if __name__ == '__main__':
    
    def btn_pressed(btn_id, state):
        print('item {} state: {}'.format(btn_id, state))

    disp_width  = 320
    disp_height = 240
    cam = camera.Camera(disp_width, disp_height)   # Manually set resolution, default is too large
    
    gui = GUI()
    btn_id1= gui.createButton(0,0,60,40)
    gui.setItemLabel(btn_id1, 'AA')
    gui.setItemCallback(btn_id1, btn_pressed)

    btn_id2= gui.createButton(0,disp_height-40,60,40)
    gui.setItemLabel(btn_id2, 'BB')
    gui.setItemCallback(btn_id2, btn_pressed)

    btn_id3= gui.createButton(disp_width-60,disp_height-40,60,40)
    gui.setItemLabel(btn_id3, 'CC')
    gui.setItemCallback(btn_id3, btn_pressed)

    btn_id4= gui.createButton(disp_width-60,0,60,40)
    gui.setItemLabel(btn_id4, 'DD')
    gui.setItemCallback(btn_id4, btn_pressed)

    while True:
        img = cam.read()
        gui.run(img)
    
