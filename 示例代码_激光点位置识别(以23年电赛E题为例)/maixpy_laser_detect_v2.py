'''
V2 红绿激光点的区分，颜色获取转换到HSV色域，取目标区域的H色相的平均值，区分度相比LAB色域更好一些
'''

from maix import image, camera, display, app
import cv2

cam  = camera.Camera(320, 240) 
disp = display.Display()

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))

# 初始化激光点坐标位置变量
point_x = 0
point_y = 0

last_img_cv_gray = None
while not app.need_exit():
    img = cam.read()
    img_cv = image.image2cv(img, False, False)
    img_cv_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    if last_img_cv_gray is None:
        last_img_cv_gray = img_cv_gray.copy()

    # 计算差值
    img_diff = cv2.absdiff(img_cv_gray, last_img_cv_gray)

    # 二值化处理
    _, img_binary = cv2.threshold(img_diff, 25, 255, cv2.THRESH_BINARY)
    
    # 膨胀处理填充激光点空洞
    img_binary = cv2.dilate(img_binary, kernel, iterations=2)

    # check point 放开注释,应能黑色背景下激光点二值化后的白点
    # img_show = image.cv2image(img_binary, False, False) 
    # disp.show(img_show)
    
    # 查找轮廓
    contours, _ = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        # 计算轮廓面积
        contour_area = cv2.contourArea(contour)

        # 激光点不大，过滤掉大范围的轮廓
        if contour_area < 200: 
            # 计算轮廓质心作为激光点位置坐标
            M = cv2.moments(contour)
            point_x = int(M["m10"] / M["m00"])
            point_y = int(M["m01"] / M["m00"])

            # 获取激光点轮廓的外接矩形 
            x, y, w, h = cv2.boundingRect(contour)
            roi = img_cv[y:y+h, x:x+w]
    
            # 转换为 Lab 并计算均值
            roi_lab = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
            value = cv2.mean(roi_lab)[:3]  # 取前三个通道 (H, S, V)

            '''
            红绿激光点的区分有两种思路，一种是根据直方图统计值，比如查看激光点轮廓内的颜色的均值/中位数/众数等，哪个区别度大选哪个
            另一种可以首先调节激光点器，使其红色和绿色的光斑大小不同，这样就可以根据该轮廓面积来区分
            下面打印出这两种值，你可以实际测验哪种更方便和准确
            '''
            print('value = {} and contour area = {}'.format(value, contour_area))
            img.draw_cross(point_x, point_y, image.COLOR_BLUE, 5, 2)
            img.draw_string(point_x, point_y, 'value:{:.2f}'.format(value[0]))

    last_img_cv_gray = img_cv_gray.copy()
    disp.show(img)
