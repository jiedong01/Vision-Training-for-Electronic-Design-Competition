from maix import camera, display, image

cam = camera.Camera(552,368)
cam.exposure(80)
# cam.awb_mode(1)
# cam.gain(100)

disp = display.Display()

filter_threshold = 10
color_thresholds = [[10, 93, 16, 112, -8, 72]] 

while True:
    img = cam.read()
    blobs = img.find_blobs(color_thresholds, pixels_threshold = filter_threshold)
    for b in blobs:
        cx = b.cx()
        cy = b.cy()
        img.draw_cross(cx, cy, image.COLOR_RED, 8, 2)
    disp.show(img)
