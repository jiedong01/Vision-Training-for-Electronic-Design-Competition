from maix import image, camera, display, app, time
import cv2 

# 实例化摄像头和显示对象
cam  = camera.Camera(320, 240) 
disp = display.Display()

# 闭运算卷积核
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))

while not app.need_exit():
    img = cam.read()
    img_raw = image.image2cv(img, copy=False) 

    # 转灰度
    img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY) 

    # 高斯模糊去噪声
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # 膨胀处理
    img = cv2.dilate(img, kernel, iterations=1)

    # 腐蚀处理
    img = cv2.erode(img, kernel, iterations=1)

    # 边缘检测
    edged = cv2.Canny(img, 50, 150) 

    # img_show = image.cv2image(edged, copy=False) 
    # disp.show(img_show)

    # 找轮廓
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # 过滤掉面积较小的轮廓
    filtered_contours = [contour for contour in contours if cv2.contourArea(contour) > 1000]
    if len(filtered_contours) > 0:
        
        # 计算每个轮廓的面积
        areas = [cv2.contourArea(contour) for contour in filtered_contours]

        # 找到面积最大的轮廓
        max_area = max(areas)
        max_contour = contours[areas.index(max_area)]
        # 确保轮廓坐标按逆时针排列
        max_contour = max_contour[::-1] if cv2.contourArea(max_contour, oriented=True) > 0 else max_contour
        # 画轮廓
        cv2.drawContours(img_raw, max_contour, -1, (0, 255, 0), 2) 

        # 找到面积最小的轮廓
        min_area = min(areas)
        min_contour = contours[areas.index(min_area)]
        # 确保轮廓坐标按逆时针排列
        min_contour = min_contour[::-1] if cv2.contourArea(min_contour, oriented=True) > 0 else min_contour
        # 画轮廓
        cv2.drawContours(img_raw, min_contour, -1, (0, 255, 0), 2) 

        # img_show = image.cv2image(img_raw, copy=False) 
        # disp.show(img_show)

        # 逐点绘制最外围轮廓
        points = max_contour.reshape(-1, 2).ravel()
        for i in range(0, len(points), 2):
            x, y = points[i], points[i+1]
            # 届时把上边这个坐标发给主控去控制舵机运动，这里为了演示，加延时后逐点绘制
            cv2.circle(img_raw, (x, y), 2, (255,0,0), -1)
            img_show = image.cv2image(img_raw, copy=False) 
            disp.show(img_show)
            time.sleep_ms(10)

        # 逐点绘制最外围轮廓
        points = min_contour.reshape(-1, 2).ravel()
        for i in range(0, len(points), 2):
            x, y = points[i], points[i+1]
            # 届时把上边这个坐标发给主控去控制舵机运动，这里为了演示，加延时后逐点绘制
            cv2.circle(img_raw, (x, y), 2, (255,0,0), -1)
            img_show = image.cv2image(img_raw, copy=False) 
            disp.show(img_show)
            time.sleep_ms(10)     
    else:
        img_show = image.cv2image(img_raw, copy=False) 
        disp.show(img_show)