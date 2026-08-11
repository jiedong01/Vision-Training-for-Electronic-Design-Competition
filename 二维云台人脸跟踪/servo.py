
'''
    180度3线航模伺服驱动
'''

from maix import pwm, pinmap

class Servo():
    SERVO_FREQ = 50        # 50Hz 20ms
    SERVO_MIN_DUTY = 2.5   # 2.5% -> 0.5ms
    SERVO_MAX_DUTY = 12.5  # 12.5% -> 2.5ms

    SERVO_MAX_ANGLE = 180

    def __init__(self, pwm_id:int, angle:int) -> None:

        angle = Servo.SERVO_MAX_ANGLE if angle > Servo.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle

        if pwm_id == 7:
            pinmap.set_pin_function("A19", "PWM7")
            self.pwm = pwm.PWM(pwm_id, freq=Servo.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)
        elif pwm_id == 6:
            pinmap.set_pin_function("A18", "PWM6")
            self.pwm = pwm.PWM(pwm_id, freq=Servo.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)
        elif pwm_id == 5:
            pinmap.set_pin_function("A17", "PWM5")
            self.pwm = pwm.PWM(pwm_id, freq=Servo.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)
        elif pwm_id == 4:
            pinmap.set_pin_function("A16", "PWM4")
            self.pwm = pwm.PWM(pwm_id, freq=Servo.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)

    def __del__(self) -> None:
        self.pwm.disable()

    def _angle_to_duty(self, angle:int) -> float:
        '''
        将角度转换为占空比
        '''
        return (Servo.SERVO_MAX_DUTY - Servo.SERVO_MIN_DUTY) / Servo.SERVO_MAX_ANGLE * angle  + Servo.SERVO_MIN_DUTY
    
    def angle(self, angle:int) -> None:
        '''
        设定角度
        '''
        angle = Servo.SERVO_MAX_ANGLE if angle > Servo.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle  

        duty = self._angle_to_duty(angle)
        self.pwm.duty(duty)