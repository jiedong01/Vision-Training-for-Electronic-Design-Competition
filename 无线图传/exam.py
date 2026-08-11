from maix import camera, display
import socket, struct

SERVER_IP   = '192.168.3.194'
SERVER_PORT = 5000

IMAGE_WIDTH  = 512
IMAGE_HEIGHT = 320

client_socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (SERVER_IP, SERVER_PORT)
client_socket.connect(server_address)

cam = camera.Camera(IMAGE_WIDTH, IMAGE_HEIGHT) 
disp = display.Display()
frame_head = [0, 0, IMAGE_WIDTH, IMAGE_HEIGHT, 13, 0x7F800000, 0x7F800000]

while True:
    img  = cam.read()
    disp.show(img)

    image_bytes   = img.to_bytes()
    frame_head[1] = len(image_bytes)
    
    buffer = b''
    for item in frame_head:
        buffer += struct.pack('<i', item)
    client_socket.sendall(buffer)

    block = int(len(image_bytes)/2048)
    for i in range(block):
       client_socket.send(image_bytes[i*2048:(i+1)*2048])
    client_socket.sendall(image_bytes[block*2048:])
