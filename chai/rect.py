from maix import image, camera, display, app
import cv2

#开运算：一般要识别的图形周围有噪点采用。
#先对图像进行腐蚀，然后再膨胀，把噪点腐掉，同时要识别的图形会变得瘦小，所以需要膨胀操作恢复
#闭运算：开开运算的对应操作，要识别的图像內部噪点时采用。
#先膨胀再腐蚀，膨胀可以把内部的噪点去除，如果图像有断断续续的部分也能将其连接上
#由于膨胀操作把目标图形扩大了，所以需要进行一次腐蚀操作恢复到原来的图形

#找边缘（边缘操作）/二值化：把主要目标对象的边缘或者轮廓突出
# 闭运算卷积核


kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))

def rect_reg(img, disp):  # 修改1：增加disp参数
    img_raw = image.image2cv(img, copy=False)
    # 转灰度
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY) 
    # 双边滤波  # 两重高斯滤波
    img_filtered = cv2.bilateralFilter(img_gray, 9, 150, 200)
    # 闭运算
    img_closed = cv2.morphologyEx(img_filtered, cv2.MORPH_CLOSE, kernel) 
    # canny边缘检测  canny算子效果最好
    edged = cv2.Canny(img_closed, 100, 200) 
    
    # 查找轮廓 
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours: 
        # 计算参数，多边形逼近
        epsilon = 0.01 * cv2.arcLength(contour, True)
        #epsilon设定的常规方式一般会和要识别的轮廓的周长结合起来 这个函数就是算周长的
        approx = cv2.approxPolyDP(contour, epsilon, True) 
        #contour：要近似逼近的轮廓 epsilon：从原始轮廓到近似轮廓的最大距离（反应逼近准确程度的阈值）
        #closed：设定弧线是否闭合
        if ((len(approx) >= 3) & (len(approx) <=4)):
            # 画轮廓 
            cv2.drawContours(img_raw, [approx], 0, (0, 255, 0), 2) 
            for point in approx:
                # 画各个角点  
                x, y = point.ravel()
                cv2.circle(img_raw, (x, y), 5, (255,0,0), 1) 
                print([point.ravel()])
    
    # 显示处理后的图像
    img_show = image.cv2image(img_raw, copy=False) 
    disp.show(img_show)

def main():
    cam = camera.Camera(240, 240) 
    disp = display.Display()  # 创建显示对象
    
    while not app.need_exit():
        img = cam.read()
        rect_reg(img, disp)  # 修改2：传入disp对象

if __name__ == '__main__':
    main()