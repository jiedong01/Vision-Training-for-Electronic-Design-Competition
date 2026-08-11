# line_follower.py
# 核心寻线模块 - 边线提取、拐点检测、补线

import math

class LineFollower:
    def __init__(self, width=320, height=240):
        self.width = width
        self.height = height
        
        # 边线数组 [行] = 列坐标
        self.left_line = [0] * height
        self.right_line = [0] * height
        self.mid_line = [0] * height
        
        # 丢线统计
        self.left_lost_time = 0
        self.right_lost_time = 0
        self.both_lost_time = 0
        
        # 搜索截止行（前瞻距离）
        self.search_stop_line = 0
        
        # 边界起始点
        self.boundry_start_left = 0
        self.boundry_start_right = 0
        
        # 拐点坐标（行号）
        self.left_up_find = 0
        self.right_up_find = 0
        self.left_down_find = 0
        self.right_down_find = 0
        
        # 标志位
        self.cross_flag = 0
        self.straight_flag = 0
        
        # 误差
        self.err = 0
        
        # 图像二值化数组（用于显示调试）
        self.binary_image = None
        
    def extract_lines(self, img, threshold=128):
        """
        从二值化图像中提取左右边线
        使用"最长白列法"从下往上搜索
        """
        h = self.height
        w = self.width
        
        # 重置
        self.left_line = [0] * h
        self.right_line = [0] * h
        self.mid_line = [0] * h
        self.left_lost_time = 0
        self.right_lost_time = 0
        self.both_lost_time = 0
        
        # 从底部往上逐行扫描
        for row in range(h - 1, -1, -1):
            # 获取该行像素（假设img是二值化数组，0为黑/赛道，1为白/背景）
            # 实际使用时，img可能是image.Image对象，需要适配
            row_data = self._get_row_data(img, row)
            
            # 从左往右找第一个黑点（左边界）
            left = -1
            for col in range(w):
                if row_data[col] == 0:  # 黑色=赛道
                    left = col
                    break
            
            # 从右往左找第一个黑点（右边界）
            right = -1
            for col in range(w - 1, -1, -1):
                if row_data[col] == 0:
                    right = col
                    break
            
            # 判断丢线
            if left == -1:
                self.left_lost_time += 1
                # 继承上一行的左边界
                if row < h - 1:
                    self.left_line[row] = self.left_line[row + 1]
                else:
                    self.left_line[row] = w // 2
            else:
                self.left_line[row] = left
            
            if right == -1:
                self.right_lost_time += 1
                if row < h - 1:
                    self.right_line[row] = self.right_line[row + 1]
                else:
                    self.right_line[row] = w // 2
            else:
                self.right_line[row] = right
            
            # 计算中线
            if left != -1 and right != -1:
                self.mid_line[row] = (left + right) // 2
            else:
                self.mid_line[row] = self.mid_line[row + 1] if row < h - 1 else w // 2
            
            # 如果左右都丢线，累计
            if left == -1 and right == -1:
                self.both_lost_time += 1
        
        # 计算搜索截止行（最长白列的长度）
        self.search_stop_line = self._calc_search_stop_line()
        
        # 计算边界起始点
        self.boundry_start_left = self._find_boundry_start(self.left_line)
        self.boundry_start_right = self._find_boundry_start(self.right_line)
        
        # 计算误差（中线偏移）
        self.err = self.mid_line[h - 1] - self.width // 2
        
        return True
    
    def _get_row_data(self, img, row):
        """获取图像某行数据 - 需要根据实际图像对象适配"""
        # 这里假设img是二维列表或可访问像素的对象
        # 实际使用MaixCAM时，可能需要用img.get_pixel()或直接访问buffer
        if hasattr(img, 'get_pixel'):
            return [img.get_pixel(col, row) for col in range(self.width)]
        elif isinstance(img, list):
            return img[row] if row < len(img) else [0] * self.width
        else:
            # 占位返回
            return [0] * self.width
    
    def _calc_search_stop_line(self):
        """计算搜索截止行（前瞻距离）"""
        # 简化：从底部往上找第一个左右边界都稳定的行
        h = self.height
        for row in range(h - 1, -1, -1):
            if self.left_line[row] > 0 and self.right_line[row] > 0:
                if self.left_line[row] < self.right_line[row]:
                    return h - row
        return h
    
    def _find_boundry_start(self, line):
        """找到第一个非丢线点（边界起始点）"""
        h = self.height
        for row in range(h - 1, -1, -1):
            if line[row] > 0 and line[row] < self.width - 1:
                return row
        return 0
    
    def detect_straight(self):
        """
        直道检测 - 参考CSDN博客思路
        条件：前瞻远 + 边界起始点靠下 + 误差小
        """
        self.straight_flag = 0
        
        if self.search_stop_line >= 65:  # 前瞻远
            if self.boundry_start_left >= 68 and self.boundry_start_right >= 65:
                if -5 <= self.err <= 5:
                    self.straight_flag = 1
        return self.straight_flag
    
    def find_corners(self):
        """
        找拐点（角点）- 使用"边界撕裂法"
        参考CSDN博客的Find_Up_Point和Find_Down_Point
        """
        # 重置拐点
        self.left_up_find = 0
        self.right_up_find = 0
        self.left_down_find = 0
        self.right_down_find = 0
        
        # 如果双边丢线太少，不可能是十字
        if self.both_lost_time < 10:
            return False
        
        # 找上拐点
        self._find_up_points()
        
        # 找下拐点
        if self.left_up_find != 0 and self.right_up_find != 0:
            down_start = max(self.left_up_find, self.right_up_find)
            self._find_down_points(down_start + 2)
        
        return (self.left_up_find != 0 or self.right_up_find != 0)
    
    def _find_up_points(self):
        """
        找上拐点（左上+右上）
        核心：边界撕裂 - 上面几行差距小，下面几行差距大
        """
        h = self.height
        margin = 5
        
        for row in range(h - 1 - margin, margin, -1):
            # 左上拐点
            if self.left_up_find == 0:
                # 上面几行差距小
                if (abs(self.left_line[row] - self.left_line[row - 1]) <= 5 and
                    abs(self.left_line[row - 1] - self.left_line[row - 2]) <= 5 and
                    abs(self.left_line[row - 2] - self.left_line[row - 3]) <= 5):
                    # 下面几行差距大（边界撕裂）
                    if (self.left_line[row] - self.left_line[row + 2] >= 8 and
                        self.left_line[row] - self.left_line[row + 3] >= 15 and
                        self.left_line[row] - self.left_line[row + 4] >= 15):
                        self.left_up_find = row
            
            # 右上拐点
            if self.right_up_find == 0:
                if (abs(self.right_line[row] - self.right_line[row - 1]) <= 5 and
                    abs(self.right_line[row - 1] - self.right_line[row - 2]) <= 5 and
                    abs(self.right_line[row - 2] - self.right_line[row - 3]) <= 5):
                    if (self.right_line[row] - self.right_line[row + 2] <= -8 and
                        self.right_line[row] - self.right_line[row + 3] <= -15 and
                        self.right_line[row] - self.right_line[row + 4] <= -15):
                        self.right_up_find = row
            
            # 都找到了就退出
            if self.left_up_find != 0 and self.right_up_find != 0:
                break
        
        # 防止误判：两个上拐点纵向差距过大
        if abs(self.right_up_find - self.left_up_find) >= 30:
            self.left_up_find = 0
            self.right_up_find = 0
    
    def _find_down_points(self, start_row):
        """
        找下拐点（左下+右下）
        """
        h = self.height
        margin = 5
        end_row = max(margin, h - self.search_stop_line)
        
        for row in range(start_row, end_row, -1):
            # 左下拐点
            if self.left_down_find == 0:
                if (abs(self.left_line[row] - self.left_line[row + 1]) <= 5 and
                    abs(self.left_line[row + 1] - self.left_line[row + 2]) <= 5 and
                    abs(self.left_line[row + 2] - self.left_line[row + 3]) <= 5):
                    if (self.left_line[row] - self.left_line[row - 2] >= 8 and
                        self.left_line[row] - self.left_line[row - 3] >= 15 and
                        self.left_line[row] - self.left_line[row - 4] >= 15):
                        self.left_down_find = row
            
            # 右下拐点
            if self.right_down_find == 0:
                if (abs(self.right_line[row] - self.right_line[row + 1]) <= 5 and
                    abs(self.right_line[row + 1] - self.right_line[row + 2]) <= 5 and
                    abs(self.right_line[row + 2] - self.right_line[row + 3]) <= 5):
                    if (self.right_line[row] - self.right_line[row - 2] <= -8 and
                        self.right_line[row] - self.right_line[row - 3] <= -15 and
                        self.right_line[row] - self.right_line[row - 4] <= -15):
                        self.right_down_find = row
            
            if self.left_down_find != 0 and self.right_down_find != 0:
                break
        
        # 下拐点不能比上拐点还靠上
        if self.left_down_find <= self.left_up_find:
            self.left_down_find = 0
        if self.right_down_find <= self.right_up_find:
            self.right_down_find = 0
    
    def detect_cross(self):
        """
        十字检测 - 参考CSDN博客思路
        核心：找到两个上拐点即认为进入十字
        """
        self.cross_flag = 0
        
        # 找拐点
        self.find_corners()
        
        # 找到两个上拐点就认为是十字
        if self.left_up_find != 0 and self.right_up_find != 0:
            self.cross_flag = 1
            self._fill_cross_lines()
        
        return self.cross_flag
    
    def _fill_cross_lines(self):
        """
        十字补线 - 根据拐点情况补线
        四种情况：
        1. 四个点都在 -> 直接连线
        2. 三个点 -> 一个斜率补线 + 一个直接连线
        3. 只有两个上点 -> 两个斜率补线
        """
        h = self.height
        
        if self.left_down_find != 0 and self.right_down_find != 0:
            # 四个点都在：直接连线
            self._add_line(
                self.left_line[self.left_up_find], self.left_up_find,
                self.left_line[self.left_down_find], self.left_down_find,
                'left'
            )
            self._add_line(
                self.right_line[self.right_up_find], self.right_up_find,
                self.right_line[self.right_down_find], self.right_down_find,
                'right'
            )
        elif self.left_down_find == 0 and self.right_down_find != 0:
            # 三个点：左斜率补线 + 右直接连线
            self._lengthen_boundry(self.left_up_find - 1, h - 1, 'left')
            self._add_line(
                self.right_line[self.right_up_find], self.right_up_find,
                self.right_line[self.right_down_find], self.right_down_find,
                'right'
            )
        elif self.left_down_find != 0 and self.right_down_find == 0:
            # 三个点：左直接连线 + 右斜率补线
            self._add_line(
                self.left_line[self.left_up_find], self.left_up_find,
                self.left_line[self.left_down_find], self.left_down_find,
                'left'
            )
            self._lengthen_boundry(self.right_up_find - 1, h - 1, 'right')
        else:
            # 只有两个上点：两个斜率补线
            self._lengthen_boundry(self.left_up_find - 1, h - 1, 'left')
            self._lengthen_boundry(self.right_up_find - 1, h - 1, 'right')
    
    def _add_line(self, x1, y1, x2, y2, side='left'):
        """
        两点连线补线
        参考CSDN博客的Left_Add_Line / Right_Add_Line
        """
        # 坐标校正
        x1 = max(0, min(self.width - 1, x1))
        x2 = max(0, min(self.width - 1, x2))
        y1 = max(0, min(self.height - 1, y1))
        y2 = max(0, min(self.height - 1, y2))
        
        # 确保y1 <= y2
        if y1 > y2:
            y1, y2 = y2, y1
            x1, x2 = x2, x1
        
        # 防止除零
        if y2 - y1 == 0:
            return
        
        line = self.left_line if side == 'left' else self.right_line
        
        for y in range(y1, y2 + 1):
            x = int((y - y1) * (x2 - x1) / (y2 - y1) + x1)
            x = max(0, min(self.width - 1, x))
            line[y] = x
    
    def _lengthen_boundry(self, start, end, side='left'):
        """
        斜率补线 - 只有一个点的时候，向上找点确定斜率然后向下延长
        参考CSDN博客的Lengthen_Left_Boundry / Lengthen_Right_Boundry
        """
        # 坐标校正
        start = max(0, min(self.height - 1, start))
        end = max(0, min(self.height - 1, end))
        
        line = self.left_line if side == 'left' else self.right_line
        
        # 如果起始点太靠上，无法向上取点，直接连线
        if start <= 5:
            self._add_line(line[start], start, line[end], end, side)
            return
        
        # 从起始点向上取点计算斜率
        # 使用start和start-4两个点计算斜率
        k = (line[start] - line[start - 4]) / 5.0  # 这里的k是1/斜率
        
        # 向下补线
        if start <= end:
            for y in range(start, end + 1):
                x = int((y - start) * k + line[start])
                x = max(0, min(self.width - 1, x))
                line[y] = x
        else:
            for y in range(end, start + 1):
                x = int((y - start) * k + line[start])
                x = max(0, min(self.width - 1, x))
                line[y] = x
    
    def get_error(self):
        """
        获取控制误差
        优先使用拐点信息修正误差
        """
        # 如果有十字标志，使用补线后的中线计算误差
        if self.cross_flag:
            # 使用补线后的边线重新计算中线
            h = self.height
            for row in range(h - 1, -1, -1):
                if self.left_line[row] > 0 and self.right_line[row] > 0:
                    if self.left_line[row] < self.right_line[row]:
                        self.mid_line[row] = (self.left_line[row] + self.right_line[row]) // 2
                    else:
                        self.mid_line[row] = self.mid_line[row + 1] if row < h - 1 else self.width // 2
                else:
                    self.mid_line[row] = self.mid_line[row + 1] if row < h - 1 else self.width // 2
            
            self.err = self.mid_line[h - 1] - self.width // 2
        
        return self.err
    
    def get_debug_info(self):
        """获取调试信息"""
        return {
            'search_stop': self.search_stop_line,
            'left_lost': self.left_lost_time,
            'right_lost': self.right_lost_time,
            'both_lost': self.both_lost_time,
            'err': self.err,
            'straight': self.straight_flag,
            'cross': self.cross_flag,
            'left_up': self.left_up_find,
            'right_up': self.right_up_find,
            'left_down': self.left_down_find,
            'right_down': self.right_down_find,
        }