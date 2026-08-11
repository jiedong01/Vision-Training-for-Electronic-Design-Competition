from maix import camera, display, image

cam = camera.Camera(320, 240)
disp = display.Display()

area_threshold = 500
pixels_threshold = 500

# 黄色阈值
# 格式：[L_min, L_max, A_min, A_max, B_min, B_max]
# 你取到的黄色大概是 L=73, A=27, B=77
# 所以给它一个范围，不是直接写 73,27,77
thresholds = [[40, 100, 0, 60, 35, 120]]

while 1:
    img = cam.read()

    blobs = img.find_blobs(
        thresholds,
        area_threshold=area_threshold,
        pixels_threshold=pixels_threshold,
        merge=True
    )

    if blobs:
        # 只取面积最大的那个色块，避免小碎块干扰
        max_blob = blobs[0]
        for b in blobs:
            if b.area() > max_blob.area():
                max_blob = b

        b = max_blob

        # 画红色四边形，类似你视频里的效果
        corners = b.corners()
        for i in range(4):
            img.draw_line(
                corners[i][0],
                corners[i][1],
                corners[(i + 1) % 4][0],
                corners[(i + 1) % 4][1],
                image.COLOR_RED
            )

        # 画蓝色外接矩形
        blob_rect = b.rect()
        img.draw_rect(
            blob_rect[0],
            blob_rect[1],
            blob_rect[2],
            blob_rect[3],
            image.COLOR_BLUE
        )

        # 画中心点
        img.draw_cross(b.cx(), b.cy(), image.COLOR_GREEN)

    disp.show(img)