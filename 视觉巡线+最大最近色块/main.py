from maix import touchscreen, camera, display, image, time, app
from maix.image import Image
import math


class GUI:
    def __init__(self) -> None:
        self.background = None
        self.items = list()
        self.callbacks = list()
        self.labels = list()

        self.touch_x = 0
        self.touch_y = 0

        image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf")
        image.set_default_font("sourcehansans")

        self._ts = touchscreen.TouchScreen()
        self._disp = display.Display()
        self._last_pressed = 0

    def _is_in_item(self, item_id: int, x: int, y: int) -> bool:
        if item_id >= len(self.items) or self.background == None:
            return False

        item_pos = self.items[item_id]
        item_disp_pos = image.resize_map_pos(
            self.background.width(),
            self.background.height(),
            self._disp.width(),
            self._disp.height(),
            image.Fit.FIT_CONTAIN,
            item_pos[0], item_pos[1], item_pos[2], item_pos[3]
        )

        if x > item_disp_pos[0] and x < (item_disp_pos[0] + item_disp_pos[2]) and y > item_disp_pos[1] and y < (item_disp_pos[1] + item_disp_pos[3]):
            return True
        else:
            return False

    def createButton(self, x: int, y: int, width: int, height: int) -> int:
        item_id = len(self.items)
        self.items.append([x, y, width, height])
        self.callbacks.append(None)
        self.labels.append(None)
        return item_id

    def setItemCallback(self, item_id: int, cb) -> None:
        if item_id >= len(self.items):
            return
        self.callbacks[item_id] = cb

    def setItemLabel(self, item_id: int, label: str) -> None:
        if item_id >= len(self.items):
            return
        self.labels[item_id] = label

    def get_touch(self) -> tuple:
        if self.background == None:
            return (0, 0)

        x, y = image.resize_map_pos_reverse(
            self.background.width(),
            self.background.height(),
            self._disp.width(),
            self._disp.height(),
            image.Fit.FIT_CONTAIN,
            self.touch_x,
            self.touch_y
        )
        x = x if x >= 0 else 0
        y = y if y >= 0 else 0
        return (x, y)

    def run(self, background: Image) -> None:
        self.background = background
        self.touch_x, self.touch_y, pressed = self._ts.read()

        if self._last_pressed != pressed:
            self._last_pressed = pressed

            for id in range(len(self.items)):
                if self._is_in_item(id, self.touch_x, self.touch_y):
                    if self.callbacks[id] != None:
                        self.callbacks[id](id, pressed)
                    break

        for id in range(len(self.items)):
            label_size = image.string_size(self.labels[id])
            label_x = (self.items[id][0] + (self.items[id][2] - label_size.width()) // 2) if self.items[id][2] > label_size.width() else self.items[id][0]
            label_y = (self.items[id][1] + (self.items[id][3] - label_size.height()) // 2) if self.items[id][3] > label_size.height() else self.items[id][1]

            self.background.draw_rect(self.items[id][0], self.items[id][1], self.items[id][2], self.items[id][3], image.COLOR_RED, 2)
            if self.labels[id] != None:
                self.background.draw_string(label_x, label_y, self.labels[id], image.COLOR_WHITE)

        self._disp.show(self.background)


# =========================
# 全局参数
# =========================
_image_width = 320
_image_height = 240
_btn_width = _image_width // 6
_btn_height = _image_height // 6

_btn_id_pixel = -1
_btn_id_binary = -1

_to_show_binary = False
_to_get_pixel = False


def rgb_to_lab(rgb):
    """
    RGB 转 LAB
    """
    M = [
        [0.412453, 0.357580, 0.180423],
        [0.212671, 0.715160, 0.072169],
        [0.019334, 0.119193, 0.950227]
    ]

    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4

    X = M[0][0] * r + M[0][1] * g + M[0][2] * b
    Y = M[1][0] * r + M[1][1] * g + M[1][2] * b
    Z = M[2][0] * r + M[2][1] * g + M[2][2] * b

    X /= 0.95047
    Y /= 1.0
    Z /= 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    L = 116 * f(Y) - 16
    A = 500 * (f(X) - f(Y))
    B = 200 * (f(Y) - f(Z))

    return [L, A, B]


def clamp(v, vmin, vmax):
    if v < vmin:
        return vmin
    if v > vmax:
        return vmax
    return v


def set_configured_threshold(threshold):
    """
    保存阈值
    """
    if len(threshold) < 6:
        return

    app.set_app_config_kv('demo_find_circle', 'lmin', str(threshold[0]), False)
    app.set_app_config_kv('demo_find_circle', 'lmax', str(threshold[1]), False)
    app.set_app_config_kv('demo_find_circle', 'amin', str(threshold[2]), False)
    app.set_app_config_kv('demo_find_circle', 'amax', str(threshold[3]), False)
    app.set_app_config_kv('demo_find_circle', 'bmin', str(threshold[4]), False)
    app.set_app_config_kv('demo_find_circle', 'bmax', str(threshold[5]), True)


def get_configured_threshold():
    """
    获取阈值
    默认给一个黄色范围
    """
    threshold = [40, 100, 0, 70, 30, 127]

    value_str = app.get_app_config_kv('demo_find_circle', 'lmin', '', False)
    if len(value_str) > 0:
        threshold[0] = int(value_str)

    value_str = app.get_app_config_kv('demo_find_circle', 'lmax', '', False)
    if len(value_str) > 0:
        threshold[1] = int(value_str)

    value_str = app.get_app_config_kv('demo_find_circle', 'amin', '', False)
    if len(value_str) > 0:
        threshold[2] = int(value_str)

    value_str = app.get_app_config_kv('demo_find_circle', 'amax', '', False)
    if len(value_str) > 0:
        threshold[3] = int(value_str)

    value_str = app.get_app_config_kv('demo_find_circle', 'bmin', '', False)
    if len(value_str) > 0:
        threshold[4] = int(value_str)

    value_str = app.get_app_config_kv('demo_find_circle', 'bmax', '', False)
    if len(value_str) > 0:
        threshold[5] = int(value_str)

    return threshold


def btn_pressed(btn_id, state):
    """
    按钮回调
    """
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel

    if state == 0:
        return

    if btn_id == _btn_id_binary:
        _to_show_binary = not _to_show_binary
        if _to_get_pixel:
            _to_get_pixel = False

    elif btn_id == _btn_id_pixel:
        _to_get_pixel = not _to_get_pixel
        if _to_show_binary:
            _to_show_binary = False


def blob_to_circle_info(blob):
    """
    判断一个 blob 是否像圆，并提取圆信息
    """
    rect = blob.rect()
    x = rect[0]
    y = rect[1]
    w = rect[2]
    h = rect[3]

    if w < 8 or h < 8:
        return None

    # 长宽比，越接近 1 越像圆
    ratio = min(w, h) / max(w, h)

    # 填充率：圆在外接矩形中的面积占比大约是 pi/4 = 0.785
    fill_ratio = blob.pixels() / float(w * h)

    # 条件可以按实际调
    if ratio < 0.72:
        return None

    if fill_ratio < 0.45 or fill_ratio > 0.95:
        return None

    r = min(w, h) // 2
    cx = x + w // 2
    cy = y + h // 2

    return {
        "blob": blob,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "cx": cx,
        "cy": cy,
        "r": r,
        "pixels": blob.pixels(),
        "ratio": ratio,
        "fill_ratio": fill_ratio
    }


def find_nearest_biggest_circle(blobs):
    """
    在所有 blob 中找：
    1. 像圆的
    2. 其中最大的那个
    这里“最近”用“半径最大”近似
    """
    circle_list = []

    for b in blobs:
        info = blob_to_circle_info(b)
        if info is not None:
            circle_list.append(info)

    if len(circle_list) == 0:
        return None, []

    best = circle_list[0]

    for c in circle_list:
        # 优先选半径更大的
        if c["r"] > best["r"]:
            best = c
        elif c["r"] == best["r"]:
            # 半径一样就选像素更多的
            if c["pixels"] > best["pixels"]:
                best = c

    return best, circle_list


def main():
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel

    cam = camera.Camera(_image_width, _image_height)
    gui = GUI()

    _btn_id_pixel = gui.createButton(0, _image_height - _btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_pixel, '取阈值')
    gui.setItemCallback(_btn_id_pixel, btn_pressed)

    _btn_id_binary = gui.createButton(_image_width - _btn_width, _image_height - _btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_binary, '二值化')
    gui.setItemCallback(_btn_id_binary, btn_pressed)

    last_x = -1
    last_y = -1

    threshold = get_configured_threshold()
    print("当前阈值:", threshold)

    area_threshold = 200
    pixels_threshold = 200

    while not app.need_exit():
        raw_img = cam.read()

        # =========================
        # 1. 取阈值
        # =========================
        if _to_get_pixel:
            x, y = gui.get_touch()

            if last_x != x or last_y != y:
                last_x = x
                last_y = y

                rgb = raw_img.get_pixel(x, y, True)
                lab = rgb_to_lab(rgb)

                if len(lab) >= 3:
                    L = lab[0]
                    A = lab[1]
                    B = lab[2]

                    threshold[0] = clamp(math.floor(L) - 35, 0, 100)
                    threshold[1] = clamp(math.ceil(L) + 35, 0, 100)

                    threshold[2] = clamp(math.floor(A) - 25, -128, 127)
                    threshold[3] = clamp(math.ceil(A) + 25, -128, 127)

                    threshold[4] = clamp(math.floor(B) - 25, -128, 127)
                    threshold[5] = clamp(math.ceil(B) + 25, -128, 127)

                    print("LAB:", int(L), int(A), int(B))
                    print("threshold:", threshold)

                    set_configured_threshold(threshold)

            raw_img.draw_cross(x, y, image.COLOR_YELLOW, 8, 2)

        # =========================
        # 2. 找色块
        # =========================
        blobs = raw_img.find_blobs(
            [threshold],
            area_threshold=area_threshold,
            pixels_threshold=pixels_threshold
        )

        # =========================
        # 3. 准备显示图
        # =========================
        if _to_show_binary:
            img = raw_img.binary([threshold], False)
        else:
            img = raw_img

        # =========================
        # 4. 找所有圆，并选最近最大的圆
        # =========================
        best_circle, circle_list = find_nearest_biggest_circle(blobs)

        # 先把所有候选圆画成绿色
        for c in circle_list:
            img.draw_rect(c["x"], c["y"], c["w"], c["h"], image.COLOR_GREEN)
            img.draw_circle(c["cx"], c["cy"], c["r"], image.COLOR_GREEN)

        # 再把最终目标圆高亮
        if best_circle is not None:
            img.draw_rect(best_circle["x"], best_circle["y"], best_circle["w"], best_circle["h"], image.COLOR_RED)
            img.draw_circle(best_circle["cx"], best_circle["cy"], best_circle["r"], image.COLOR_BLUE)
            img.draw_cross(best_circle["cx"], best_circle["cy"], image.COLOR_BLUE)

            img.draw_string(
                0, 0,
                "TARGET cx:{} cy:{} r:{}".format(best_circle["cx"], best_circle["cy"], best_circle["r"]),
                image.COLOR_BLUE
            )

            img.draw_string(
                0, 20,
                "count:{}".format(len(circle_list)),
                image.COLOR_GREEN
            )
        else:
            img.draw_string(0, 0, "No circle", image.COLOR_RED)

        # =========================
        # 5. 显示
        # =========================
        gui.run(img)


if __name__ == '__main__':
    main()