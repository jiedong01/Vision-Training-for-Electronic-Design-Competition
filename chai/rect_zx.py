from maix import image, camera, display, app
import cv2
import numpy as np

# 定义不同框的颜色
INNER_COLOR = (0, 255, 0)    # 绿色 - 内框
OUTER_COLOR = (0, 0, 255)      # 红色 - 外框
MIDDLE_COLOR = (255, 0, 0)     # 蓝色 - 中间框
POINT_COLOR = (255, 255, 0)    # 青色 - 点
LABEL_COLOR = (255, 0, 255)    # 紫色 - 标签

# 闭运算卷积核
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

def order_points(pts):
    """对点进行排序：左上，右上，右下，左下"""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # 左上点
    rect[2] = pts[np.argmax(s)]  # 右下点
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # 右上点
    rect[3] = pts[np.argmax(diff)]  # 左下点
    return rect

def rect_reg(img, disp):
    img_raw = image.image2cv(img, copy=False)
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    img_filtered = cv2.bilateralFilter(img_gray, 9, 150, 200)
    img_closed = cv2.morphologyEx(img_filtered, cv2.MORPH_CLOSE, kernel)
    edged = cv2.Canny(img_closed, 100, 200)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # 存储找到的四边形
    quads = []
    
    for contour in contours:
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 只处理四边形
        if len(approx) == 4:
            # 转换为numpy数组并展平
            approx_flat = approx.reshape(4, 2)
            quads.append(approx_flat)
    
    # 需要至少两个四边形才能计算中间框
    if len(quads) < 2:
        # 如果没有足够四边形，直接显示原始图像
        img_show = image.cv2image(img_raw, copy=False)
        disp.show(img_show)
        return
    
    # 根据面积排序，面积大的为外框，小的为内框
    quads.sort(key=lambda x: cv2.contourArea(x))
    inner_quad = quads[0]  # 内框（面积小）
    outer_quad = quads[-1]  # 外框（面积大）
    
    # 对点进行排序（左上，右上，右下，左下）
    inner_quad = order_points(inner_quad)
    outer_quad = order_points(outer_quad)
    
    # 计算中间框的点（内框和外框对应点的平均值）
    middle_quad = []
    for i in range(4):
        x = int((inner_quad[i][0] + outer_quad[i][0]) / 2)
        y = int((inner_quad[i][1] + outer_quad[i][1]) / 2)
        middle_quad.append([x, y])
    middle_quad = np.array(middle_quad)
    
    # 绘制内框
    cv2.drawContours(img_raw, [inner_quad.astype("int")], -1, INNER_COLOR, 2)
    
    # 绘制外框
    cv2.drawContours(img_raw, [outer_quad.astype("int")], -1, OUTER_COLOR, 2)
    
    # 绘制中间框
    cv2.drawContours(img_raw, [middle_quad.astype("int")], -1, MIDDLE_COLOR, 2)
    
    # 绘制点
    for i, quad in enumerate([inner_quad, outer_quad, middle_quad]):
        for point in quad:
            x, y = int(point[0]), int(point[1])
            cv2.circle(img_raw, (x, y), 5, POINT_COLOR, -1)
    
    # 在中间框点上标注序号 P1, P2, P3, P4
    labels = ["P1", "P2", "P3", "P4"]
    for i, point in enumerate(middle_quad):
        x, y = int(point[0]), int(point[1])
        # 在点旁边添加标签
        cv2.putText(img_raw, labels[i], (x + 10, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, LABEL_COLOR, 2)
    
    # 创建并打印中间框点坐标数组
    middle_points_array = []
    for i, point in enumerate(middle_quad):
        x, y = int(point[0]), int(point[1])
        middle_points_array.append([x, y])
        # 打印每个点的坐标
        print(f"{labels[i]}: ({x}, {y})")
    
    # 打印整个数组
    print("\n中间框点坐标数组:")
    print(middle_points_array)
    img_show = image.cv2image(img_raw, copy=False)
    disp.show(img_show)
    return middle_points_array
    # # 显示处理后的图像
    # img_show = image.cv2image(img_raw, copy=False)
    # disp.show(img_show)

def main():
    cam = camera.Camera(240, 240)
    disp = display.Display()
    
    while not app.need_exit():
        img = cam.read()
        middle_points_array=rect_reg(img, disp)
        #print(f"1:{middle_points_array}")
if __name__ == '__main__':
    main()