from maix import image, camera, display, app
import cv2
import numpy as np

# 定义形态学操作核
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

def extend_line(line, width, height):
    """延长直线到图像边界"""
    if line is None:
        return None
        
    x1, y1, x2, y2 = line
    
    # 计算直线方向向量
    dx = x2 - x1
    dy = y2 - y1
    
    # 如果线段长度太短，使用中点作为参考
    if dx == 0 and dy == 0:
        return line
    
    # 计算延长参数
    t_values = []
    
    # 与左边界相交 (x=0)
    if dx != 0:
        t = (0 - x1) / dx
        y = y1 + t * dy
        if 0 <= y <= height:
            t_values.append(t)
    
    # 与右边界相交 (x=width)
    if dx != 0:
        t = (width - x1) / dx
        y = y1 + t * dy
        if 0 <= y <= height:
            t_values.append(t)
    
    # 与上边界相交 (y=0)
    if dy != 0:
        t = (0 - y1) / dy
        x = x1 + t * dx
        if 0 <= x <= width:
            t_values.append(t)
    
    # 与下边界相交 (y=height)
    if dy != 0:
        t = (height - y1) / dy
        x = x1 + t * dx
        if 0 <= x <= width:
            t_values.append(t)
    
    # 如果没有找到交点，返回原始线段
    if not t_values:
        return line
    
    # 找到最小和最大t值
    t_min = min(t_values)
    t_max = max(t_values)
    
    # 计算延长后的端点
    x1_ext = x1 + t_min * dx
    y1_ext = y1 + t_min * dy
    x2_ext = x1 + t_max * dx
    y2_ext = y1 + t_max * dy
    
    return (int(x1_ext), int(y1_ext), int(x2_ext), int(y2_ext))

def line_intersection(line1, line2):
    """计算两条直线的交点"""
    if line1 is None or line2 is None:
        return None
        
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    
    # 计算分母
    den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    
    # 如果分母为0，说明两线平行
    if den == 0:
        return None
    
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
    
    # 计算交点
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    
    return (int(x), int(y))

def rect_reg(img, disp):
    img_raw = image.image2cv(img, copy=False)
    height, width = img_raw.shape[:2]
    center_x, center_y = width // 2, height // 2
    
    # 1. 转灰度
    img_gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY) 
    
    # 2. 高斯模糊降噪
    img_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    
    # 3. 自适应阈值处理 - 更适合铅笔线
    binary_img = cv2.adaptiveThreshold(
        img_blur, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        11, 
        2
    )
    
    # 4. 形态学操作 - 闭运算连接断线
    img_closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # 5. Canny边缘检测
    edged = cv2.Canny(img_closed, 50, 150)

    # 6. 霍夫线变换检测直线
    lines = cv2.HoughLinesP(edged, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=20)
    
    # 7. 绘制检测到的直线并分类
    horizontal_lines = []
    vertical_lines = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # 计算直线角度
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # 分类水平线和垂直线
            if angle < 30 or angle > 150:  # 水平线
                horizontal_lines.append(line[0])
                # 绘制原始检测到的水平线 (绿色)
                cv2.line(img_raw, (x1, y1), (x2, y2), (0, 255, 0), 1)
            elif 60 < angle < 120:  # 垂直线
                vertical_lines.append(line[0])
                # 绘制原始检测到的垂直线 (蓝色)
                cv2.line(img_raw, (x1, y1), (x2, y2), (255, 0, 0), 1)
    
    # 8. 选择最靠近图像中心的四条线（最里面的矩形）
    top_line = None
    bottom_line = None
    left_line = None
    right_line = None
    
    # 选择最靠近图像中心的水平线作为顶部和底部
    if len(horizontal_lines) > 0:
        # 按中点y坐标排序
        horizontal_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
        
        # 选择最靠近中心的线作为参考
        closest_line = horizontal_lines[0]
        closest_y = (closest_line[1] + closest_line[3]) / 2
        
        # 区分上方和下方的线
        top_lines = [line for line in horizontal_lines if (line[1] + line[3]) / 2 < center_y]
        bottom_lines = [line for line in horizontal_lines if (line[1] + line[3]) / 2 > center_y]
        
        # 选择最靠近中心的上方线（顶部）
        if top_lines:
            top_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
            top_line = top_lines[0]
        
        # 选择最靠近中心的下方线（底部）
        if bottom_lines:
            bottom_lines.sort(key=lambda l: abs((l[1] + l[3]) / 2 - center_y))
            bottom_line = bottom_lines[0]
    
    # 选择最靠近图像中心的垂直线作为左侧和右侧
    if len(vertical_lines) > 0:
        # 按中点x坐标排序
        vertical_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
        
        # 选择最靠近中心的线作为参考
        closest_line = vertical_lines[0]
        closest_x = (closest_line[0] + closest_line[2]) / 2
        
        # 区分左侧和右侧的线
        left_lines = [line for line in vertical_lines if (line[0] + line[2]) / 2 < center_x]
        right_lines = [line for line in vertical_lines if (line[0] + line[2]) / 2 > center_x]
        
        # 选择最靠近中心的左侧线（左边）
        if left_lines:
            left_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
            left_line = left_lines[0]
        
        # 选择最靠近中心的右侧线（右边）
        if right_lines:
            right_lines.sort(key=lambda l: abs((l[0] + l[2]) / 2 - center_x))
            right_line = right_lines[0]
    
    # 延长选中的线
    if top_line is not None:
        top_line_ext = extend_line(top_line, width, height)
        cv2.line(img_raw, (top_line_ext[0], top_line_ext[1]), 
                 (top_line_ext[2], top_line_ext[3]), (0, 200, 0), 2)
    
    if bottom_line is not None:
        bottom_line_ext = extend_line(bottom_line, width, height)
        cv2.line(img_raw, (bottom_line_ext[0], bottom_line_ext[1]), 
                 (bottom_line_ext[2], bottom_line_ext[3]), (0, 200, 0), 2)
    
    if left_line is not None:
        left_line_ext = extend_line(left_line, width, height)
        cv2.line(img_raw, (left_line_ext[0], left_line_ext[1]), 
                 (left_line_ext[2], left_line_ext[3]), (200, 0, 0), 2)
    
    if right_line is not None:
        right_line_ext = extend_line(right_line, width, height)
        cv2.line(img_raw, (right_line_ext[0], right_line_ext[1]), 
                 (right_line_ext[2], right_line_ext[3]), (200, 0, 0), 2)
    
    # 9. 计算交点
    corners = []
    
    # 计算四个交点
    if top_line is not None and left_line is not None:
        top_ext = extend_line(top_line, width, height)
        left_ext = extend_line(left_line, width, height)
        corner = line_intersection(top_ext, left_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)  # 红色点标记交点
    
    if top_line is not None and right_line is not None:
        top_ext = extend_line(top_line, width, height)
        right_ext = extend_line(right_line, width, height)
        corner = line_intersection(top_ext, right_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    if bottom_line is not None and left_line is not None:
        bottom_ext = extend_line(bottom_line, width, height)
        left_ext = extend_line(left_line, width, height)
        corner = line_intersection(bottom_ext, left_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    if bottom_line is not None and right_line is not None:
        bottom_ext = extend_line(bottom_line, width, height)
        right_ext = extend_line(right_line, width, height)
        corner = line_intersection(bottom_ext, right_ext)
        if corner is not None:
            corners.append(corner)
            cv2.circle(img_raw, corner, 5, (0, 0, 255), -1)
    
    # 10. 检查矩形高度并绘制矩形框
    if len(corners) == 4:
        # 按左上、右上、右下、左下排序
        # 计算中心点
        center_x = int(round(sum(c[0] for c in corners) / 4))
        center_y = int(round(sum(c[1] for c in corners) / 4))
        
        # 按角度排序
        def angle_from_center(corner):
            return np.arctan2(corner[1] - center_y, corner[0] - center_x)
        
        corners_sorted = sorted(corners, key=angle_from_center)
        
        # 提取四个点
        p1 = corners_sorted[0]  # 左上
        p2 = corners_sorted[1]  # 右上
        p3 = corners_sorted[2]  # 右下
        p4 = corners_sorted[3]  # 左下
        
        # 计算左右两侧的高度
        height_left = abs(p4[1] - p1[1])  # 左侧高度（P1和P4的Y坐标差）
        height_right = abs(p3[1] - p2[1])  # 右侧高度（P2和P3的Y坐标差）
        
        # 设置最小高度阈值
        min_height_threshold = 100
        
        # 检查高度是否满足要求
        if height_left > min_height_threshold and height_right > min_height_threshold:
            # 绘制矩形框
            cv2.polylines(img_raw, [np.array(corners_sorted)], True, (0, 0, 255), 2)
            
            # 标记角点
            for i, (x, y) in enumerate(corners_sorted):
                cv2.circle(img_raw, (x, y), 8, (0, 255, 255), -1)
                cv2.putText(img_raw, f"P{i+1}", (x+10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.circle(img_raw, (center_x, center_y), 8, (0, 255, 255), -1)     
            #打印坐标到控制台
            # print("检测到的矩形角点坐标:")
            # print(f"P1 (左上): ({p1[0]}, {p1[1]})")
            # print(f"P2 (右上): ({p2[0]}, {p2[1]})")
            # print(f"P3 (右下): ({p3[0]}, {p3[1]})")
            # print(f"P4 (左下): ({p4[0]}, {p4[1]})")
            # print(f"矩形中心点的坐标: ({center_x,center_y})")
            # print(f"左侧高度: {height_left}, 右侧高度: {height_right}")
            # print("-" * 40)
            # return([p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p4[0],p4[1],center_x,center_y])

            # 在图像上显示坐标和高度信息
            cv2.putText(img_raw, f"P1:({p1[0]},{p1[1]})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P2:({p2[0]},{p2[1]})", 
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P3:({p3[0]},{p3[1]})", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"P4:({p4[0]},{p4[1]})", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"center({center_x,center_y})", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(img_raw, f"Height: {height_left}", 
                       (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                # 11. 显示结果
            img_show = image.cv2image(img_raw, copy=False) 
            disp.show(img_show)
            return([p1[0],p1[1],p2[0],p2[1],p3[0],p3[1],p4[0],p4[1],center_x,center_y])
        else:
            #高度不足，显示提示信息
            cv2.putText(img_raw, f"Height too small: {min(height_left, height_right)} < {min_height_threshold}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            print(f"矩形高度不足: 左侧高度 {height_left}, 右侧高度 {height_right} < {min_height_threshold}")
    
    elif len(corners) > 0:
        # 显示找到的角点数量
        cv2.putText(img_raw, f"Corners: {len(corners)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # 11. 显示结果
    img_show = image.cv2image(img_raw, copy=False) 
    disp.show(img_show)

def main():
    cam = camera.Camera(240, 240) 
    disp = display.Display()
    
    while not app.need_exit():
        img = cam.read()
        rectdata=rect_reg(img, disp)
        print(rectdata)
if __name__ == '__main__':
    main()