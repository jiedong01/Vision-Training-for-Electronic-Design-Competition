from maix import camera, display, image


def find_closed_blob(blobs):
    # 找 pixels 最大的色块
    max_blob = blobs[0]
    for b in blobs:
        if b.pixels() > max_blob.pixels():
            max_blob = b
    return max_blob


cam = camera.Camera(320, 240)
disp = display.Display()

area_threshold = 500
pixels_threshold = 500

# 黄色阈值
# 格式：[L_min, L_max, A_min, A_max, B_min, B_max]
# 你取色得到的是 L=73, A=27, B=77
# 所以阈值要写成范围，不是直接写 73,27,77
thresholds = [[40, 100, 0, 60, 35, 120]]

while 1:
    img = cam.read()

    blobs = img.find_blobs(
        thresholds,
        area_threshold=area_threshold,
        pixels_threshold=pixels_threshold
    )

    if len(blobs) > 0:
        # 只找最大的那个黄色色块
        max_blob = find_closed_blob(blobs)

        # 画红色旋转四边形
        corners = max_blob.corners()
        for i in range(4):
            img.draw_line(
                corners[i][0],
                corners[i][1],
                corners[(i + 1) % 4][0],
                corners[(i + 1) % 4][1],
                image.COLOR_RED
            )

        # 画蓝色外接矩形
        blob_rect = max_blob.rect()
        img.draw_rect(
            blob_rect[0],
            blob_rect[1],
            blob_rect[2],
            blob_rect[3],
            image.COLOR_BLUE
        )

        # 画中心点
        img.draw_cross(
            max_blob.cx(),
            max_blob.cy(),
            image.COLOR_GREEN
        )

    disp.show(img)