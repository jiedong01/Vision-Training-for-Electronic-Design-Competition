from maix import camera, display, image, nn, app, uart, time
import struct
import serial_protocol

detector = nn.Retinaface(model="/root/models/retinaface.mud")

cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()

comm_proto = serial_protocol.SerialProtocol()
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th = 0.4, iou_th = 0.45)
    for obj in objs:
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color = image.COLOR_RED)
        #print(obj.x, obj.y, obj.w, obj.h)
        payload = struct.pack('<iiii',obj.x,obj.y,obj.w,obj.h)
        
        encoded = comm_proto.encode(payload)
        serial.write(encoded)
        print(encoded.hex(' '))
    #time.sleep_ms(50)

    dis.show(img)
