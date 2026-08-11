from maix import camera, display, app, time, image

cam = camera.Camera(320, 240)                         
disp = display.Display()        
                               
while not app.need_exit():
    img = cam.read() 
    # 双边滤波
    img.bilateral(1)  

    # 找线段
    lines = img.find_line_segments(merge_distance=10) 
    print('total line:', len(lines))
    for line in lines:
        img.draw_line(line.x1(), line.y1(), line.x2(), line.y2(), image.Color.from_rgb(0, 0, 255),3)                         
    disp.show(img)              
                                                      

