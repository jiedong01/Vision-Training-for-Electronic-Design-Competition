from gui import GUI
from maix import camera, image, time, app
import math

#屏幕宽度和高度
_image_width  = 320
_image_height = 240
_btn_width  = _image_width//6
_btn_height = _image_height//6

_btn_id_pixel   = -1
_btn_id_binary  = -1
_to_show_binary = False
_to_get_pixel   = False

def rgb_to_lab(rgb):
    '''
    实现RGB值到LAB值的转换
    '''

    # RGB到XYZ的转换矩阵
    M = [
        [0.412453, 0.357580, 0.180423],
        [0.212671, 0.715160, 0.072169],
        [0.019334, 0.119193, 0.950227]
    ]
    
    # 归一化RGB值
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    
    # 线性化RGB值
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4
    
    # 计算XYZ值
    X = M[0][0] * r + M[0][1] * g + M[0][2] * b
    Y = M[1][0] * r + M[1][1] * g + M[1][2] * b
    Z = M[2][0] * r + M[2][1] * g + M[2][2] * b
    
    # XYZ到LAB的转换
    X /= 0.95047
    Y /= 1.0
    Z /= 1.08883
    
    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116
    
    L = 116 * f(Y) - 16
    a = 500 * (f(X) - f(Y))
    b = 200 * (f(Y) - f(Z))
    
    return [L, a, b]

def set_configured_threshold(threshold):
    '''
    阈值参数信息存入配置文件
    '''
    if len(threshold) < 6:
        return 

    app.set_app_config_kv('demo_find_line', 'lmin', str(threshold[0]), False)
    app.set_app_config_kv('demo_find_line', 'lmax', str(threshold[1]), False)
    app.set_app_config_kv('demo_find_line', 'amin', str(threshold[2]), False)
    app.set_app_config_kv('demo_find_line', 'amax', str(threshold[3]), False)
    app.set_app_config_kv('demo_find_line', 'bmin', str(threshold[4]), False)
    app.set_app_config_kv('demo_find_line', 'bmax', str(threshold[5]), True)

def get_configured_threshold():
    '''
    获取所存储配置文件中的阈值参数
    '''
    threshold = [0, 100, -128, 127, -128, 127] #默认阈值

    value_str = app.get_app_config_kv('demo_find_line', 'lmin','', False)
    if len(value_str) > 0:
        threshold[0] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'lmax','', False)
    if len(value_str) > 0:
        threshold[1] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amin','', False)
    if len(value_str) > 0:
        threshold[2] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amax','', False)
    if len(value_str) > 0:
        threshold[3] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmin','', False)
    if len(value_str) > 0:
        threshold[4] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmax','', False)
    if len(value_str) > 0:
        threshold[5] = int(value_str)
    return threshold


def btn_pressed(btn_id, state):
    '''
    界面上按键的装填改变回调函数
    '''
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel
    if state == 0: #只响应触摸抬起的动作
        return 

    if btn_id == _btn_id_binary:
        _to_show_binary = not _to_show_binary
        if _to_get_pixel:
            _to_get_pixel = False
    elif btn_id == _btn_id_pixel:
        _to_get_pixel = not _to_get_pixel


def main():
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel

    print(app.get_app_config_path())
    cam = camera.Camera(_image_width, _image_height) 
    gui = GUI()

    _btn_id_pixel = gui.createButton(0, _image_height-_btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_pixel, '取阈值')
    gui.setItemCallback(_btn_id_pixel, btn_pressed)

    _btn_id_binary = gui.createButton(_image_width-_btn_width, _image_height-_btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_binary, '二值化')
    gui.setItemCallback(_btn_id_binary, btn_pressed)

    last_x = -1
    last_y = -1
    threshold = get_configured_threshold()
    print(threshold)

    while not app.need_exit():
        # 1. 读取图像
        img = cam.read()
        if _to_show_binary:
            img = img.binary([threshold], False)
        
        # 2. 图像取阈值
        if _to_get_pixel:
            x,y = gui.get_touch()
            if last_x != x or last_y != y:
                last_x = x
                last_y = y

                rgb = img.get_pixel(x, y, True)
                lab = rgb_to_lab(rgb)
                if len(lab) >= 3:
                    threshold[0] = math.floor(lab[0]) - 30
                    threshold[0] = threshold[0] if threshold[0] >= 0 else 0

                    threshold[1] = math.ceil(lab[0]) + 30
                    threshold[1] = threshold[1] if threshold[1] <= 100 else 100
                    
                    threshold[2] = math.floor(lab[1]) - 10
                    threshold[2] = threshold[2] if threshold[2] >= -128 else -128

                    threshold[3] = math.ceil(lab[1]) + 10
                    threshold[3] = threshold[3] if threshold[1] <= 127 else 127

                    threshold[4] = math.floor(lab[2]) - 10
                    threshold[4] = threshold[4] if threshold[4] >= -128 else -128

                    threshold[5] = math.ceil(lab[2]) + 10
                    threshold[5] = threshold[5] if threshold[5] <= 127 else 127
                    print(threshold)
                    set_configured_threshold(threshold)
            img.draw_cross(x, y, image.COLOR_YELLOW, 8, 2)
        
        # 3. 线性回归寻迹画线
        area_threshold = 100
        lines = img.get_regression([threshold], area_threshold=area_threshold, pixels_threshold=area_threshold)
        for line in lines:
            img.draw_line(line.x1(), line.y1(), line.x2(), line.y2(), image.COLOR_GREEN, 2)
            img.draw_string(0,0, 'mag:{}  theta:{}  rho:{}'.format(line.magnitude(), line.theta(), line.rho()))

        # 4. 更新显示    
        gui.run(img)


if __name__ == '__main__':
    main()
