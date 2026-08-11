from maix import app, uart, pinmap, time
import sys

device = "/dev/ttyS0"
serial0 = uart.UART(device, 115200)

try:
    while True:
        serial0.write("hello world\r\n".encode())
        print("Maix 已发送 hello world")
        data = serial0.read(timeout = 1000)
        if data:
            print("Received, type: {}, len: {}, data: {}".format(type(data), len(data), data))
        time.sleep_ms(3000)
except Exception as e:
    print("程序异常退出，错误信息：", e)