import socket

HOST = "0.0.0.0"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("服务器已启动，等待 Maix 连接...")
print("监听端口:", PORT)

while True:
    conn, addr = server_socket.accept()
    print("Maix 已连接:", addr)

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print("连接断开")
                break

            print(data.decode("utf-8"), end="")

    except ConnectionResetError:
        print("Maix 强制断开连接")

    finally:
        conn.close()
        print("等待下一次连接...")