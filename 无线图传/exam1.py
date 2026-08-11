import socket
import math
import time

SERVER_IP = '192.168.3.194'   # 这里填你电脑的 IPv4
SERVER_PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.settimeout(10)

server_address = (SERVER_IP, SERVER_PORT)

print("正在连接 VOFA:", server_address)
client_socket.connect(server_address)
print("连接成功")

i = 0.0

while True:
    i += 0.1

    value = math.sin(i)

    # VOFA 文本波形数据
    data = 'I0:{}\n'.format(value)

    client_socket.sendall(data.encode('utf-8'))

    print("send:", data, end="")

    time.sleep(0.02)