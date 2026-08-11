from maix import camera, display, image, nn, app
import servo

INIT_POS_X = 90
INIT_POS_Y = 100
FILTER_FACTOR = 0.15

detector = nn.Retinaface(model="/root/models/retinaface.mud")
cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()

servo_x = servo.Servo(6, INIT_POS_X)  # A18 / PWM6，左右
servo_y = servo.Servo(7, INIT_POS_Y)  # A19 / PWM7，上下

target_x_pos = INIT_POS_X
target_y_pos = INIT_POS_Y

last_err_x_pos = 0
last_err_y_pos = 0

image_width  = detector.input_width()
image_height = detector.input_height()

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=0.4, iou_th=0.45)

    if len(objs) == 0:
        dis.show(img)
        continue

    obj = objs[0]
    img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

    face_x = obj.x + obj.w / 2
    face_y = obj.y + obj.h / 2

    err_x_pos = image_width / 2 - face_x
    err_y_pos = image_height / 2 - face_y

    # 加死区，防止人脸框轻微抖动导致舵机一直抖
    if abs(err_x_pos) < 15:
        err_x_pos = 0
    if abs(err_y_pos) < 15:
        err_y_pos = 0

    # 一阶滤波
    err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
    err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

    # 降低增益，先别太猛
    delta_x_pos = 0.08 * (err_x_pos - last_err_x_pos) + 0.008 * err_x_pos
    delta_y_pos = 0.08 * (err_y_pos - last_err_y_pos) + 0.008 * err_y_pos

    last_err_x_pos = err_x_pos
    last_err_y_pos = err_y_pos

    # 这里先用负号，防止方向反了导致乱跑
    target_x_pos -= delta_x_pos
    target_y_pos -= delta_y_pos

    # 限制角度，防止积分越积越大
    if target_x_pos < 20:
        target_x_pos = 20
    if target_x_pos > 160:
        target_x_pos = 160

    if target_y_pos < 30:
        target_y_pos = 30
    if target_y_pos > 150:
        target_y_pos = 150

    servo_x.angle(target_x_pos)
    servo_y.angle(target_y_pos)

    dis.show(img)