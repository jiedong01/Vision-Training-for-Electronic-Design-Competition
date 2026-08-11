from maix import  uart, pinmap
 
devices = uart.list_devices()
serial = uart.UART(devices[0], 115200, uart.BITS.BITS_8, uart.PARITY.PARITY_NONE, uart.STOP.STOP_1)
#做以下配置 波特率115200 数据位8 校验位NONE 停止位1

#发送测试数据类
class TTest():
    def __init__(self) -> None:
        #发送标识位
        self.Tflag = 0
 
        #发送数据内容
        self.test_number0 = 0
        self.test_number1 = 0
        self.test_number2 = 0
        self.test_number3 = 0
        self.test_number4 = 0
        self.test_number5 = 0
        self.test_number6 = 0
        self.test_number7 = 0
        self.test_number8 = 0
        self.test_number9 = 0
      

TTest0 = TTest()
TTest0.Tflag = 1
TTest0.test_number0 = 0
TTest0.test_number1 = 1
TTest0.test_number2 = 2
TTest0.test_number3 = 3 
TTest0.test_number4 = 4
TTest0.test_number5 = 5
TTest0.test_number6 = 6
TTest0.test_number7 = 7
TTest0.test_number8 = 8 
TTest0.test_number9 = 9
#串口发送函数 十位
def DataTransimit(head, tail, TData, serial):
    data = ()
    if TData.Tflag == 1:
        data = bytes([
            head,
            TData.test_number0,
            TData.test_number1,
            TData.test_number2,
            TData.test_number3,
            TData.test_number4,
            TData.test_number5,
            TData.test_number6,
            TData.test_number7,
            TData.test_number8,
            TData.test_number9,                 
            tail
        ])
        
    elif TData.Tflag == 2:
        data = bytes([
            head,
            #想要发送的数据
            tail
        ])
 
    if data != ():
        #发送数据
        serial.write(data)
 
#接受测试数据类
class  RTest():
    def __init__(self) -> None:
        #接收标识位
        self.Rflag = 0
        #发送数据标识位        
        self.Tflag = 0
 
        #接收数据内容
        self.test_number0 = 0
        self.test_number1 = 0
        self.test_number2 = 0

     
 
 
RTest0 = RTest()
RTest0.Rflag = 1
RTest0.Tflag = 1
 
#串口接受函数 长度9位
def ReceiveData(head, tail, length, serial):
    BufData = serial.read(40)
    if BufData and len(BufData) >= length: #判断接收到的数据长度
        if BufData[0] == head and BufData[length-1] == tail: #判断帧头帧尾
            return BufData
        else:
            return None
 
#接收数据解析函数
def ParseData(RData, BufData):
    if BufData != None:
        if RData.Rflag == 1:
            RData.test_number0 = BufData[0]
            RData.test_number1 = BufData[1]
            RData.test_number2 = BufData[2]
   
            print(RData.test_number0,RData.test_number1,RData.test_number2)  #打印出结果 判断正误
        elif RData.Rflag == 2:
            #接收数据内容
            pass
 
 
class Timer():
    #定时器类   #count_flag为定时器完成计时的标志，每当count_flag == 1，我们将执行一次需要定时的程序。
    def __init__(self) -> None:
        #计时数
        self.count = 0
        #计时数上限
        self.count_max = 0
        #计时完成标识
        self.count_flag = 0
 
timer0 = Timer()
timer0.count_max = 100000
 
def TimerStart(Timer):
    if Timer.count < Timer.count_max:
        #计时开始，计时器标识位置0
        Timer.count_flag = 0
        Timer.count += 1
    
    else:
        #计时完成，计时器标识位置1
        Timer.count_flag = 1
        Timer.count = 0
 
def main():
    while True:
        TimerStart(timer0)
        if (timer0.count_flag == 1 and RTest0.Rflag == 1):
                ParseData(RTest0, ReceiveData(0xA5, 0x5A, 3, serial))#接收数据的函数
                #RTest0.Rflag =0 #接收数据标志位
        if (timer0.count_flag == 1 and TTest0.Tflag == 1):
                 DataTransimit(0xA5, 0x5A, TTest0, serial) #发送数据的函数 TTest0为需要发送的值



if __name__ == '__main__':
    main()