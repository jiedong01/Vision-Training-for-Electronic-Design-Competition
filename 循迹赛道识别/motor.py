# motor.py
# 电机控制模块 - 负责PWM输出和方向控制

from maix import pwm
import time

class Motor:
    def __init__(self, left_pwm_pin=0, right_pwm_pin=1, left_dir_pin=2, right_dir_pin=3):
        """
        初始化电机控制
        注意：实际引脚号需要根据你的电机驱动板连接方式修改
        """
        # 初始化PWM
        self.left_pwm = pwm.PWM(left_pwm_pin, freq=1000, duty=0)
        self.right_pwm = pwm.PWM(right_pwm_pin, freq=1000, duty=0)
        
        # 方向引脚（GPIO），用于控制正反转
        # 这里用简化的方式，实际你需要根据硬件配置GPIO
        self.left_dir_pin = left_dir_pin
        self.right_dir_pin = right_dir_pin
        
        # 速度范围 0-100
        self.max_speed = 80
        self.base_speed = 50
        
    def set_speed(self, left_speed, right_speed):
        """
        设置左右电机速度
        left_speed, right_speed: -100 ~ 100，负值表示反转
        """
        # 限幅
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))
        
        # 设置PWM占空比（这里简化处理，实际需要根据你的驱动调整）
        # 假设PWM占空比范围 0-100
        self.left_pwm.duty(abs(left_speed))
        self.right_pwm.duty(abs(right_speed))
        
        # 方向控制（简化：正转高电平，反转低电平）
        # 实际需要根据你的电机驱动芯片（如L298N、TB6612）调整
        # self.set_dir(self.left_dir_pin, left_speed >= 0)
        # self.set_dir(self.right_dir_pin, right_speed >= 0)
    
    def stop(self):
        """急停"""
        self.left_pwm.duty(0)
        self.right_pwm.duty(0)
    
    def control_by_error(self, error, kp=0.8, base_speed=None):
        """
        根据误差控制小车方向
        error: 偏差值，正表示偏右，负表示偏左
        kp: 比例系数
        base_speed: 基础速度，默认使用self.base_speed
        """
        if base_speed is None:
            base_speed = self.base_speed
        
        # 计算转向修正量
        correction = kp * error
        
        # 计算左右轮速度（差速转向）
        left_speed = base_speed + correction
        right_speed = base_speed - correction
        
        # 限幅
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))
        
        self.set_speed(left_speed, right_speed)
        return left_speed, right_speed