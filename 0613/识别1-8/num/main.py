from maix import camera, display, image, nn, app
import os

model_path = os.path.join(os.path.dirname(__file__), "model_127448.mud")
detector = nn.YOLOv5(model=model_path, dual_buff=True)

cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
disp = display.Display()

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
    
    for obj in objs:
        # 在屏幕上画框和标签（保持不变）
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
        label = detector.labels[obj.class_id]
        msg = f'{label}: {obj.score:.2f}'
        img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

        # 终端输出识别到的对象信息 
        print(f"检测到: {label}, 置信度: {obj.score:.2f}, 位置: ({obj.x}, {obj.y}, {obj.w}, {obj.h})")
    
    disp.show(img)