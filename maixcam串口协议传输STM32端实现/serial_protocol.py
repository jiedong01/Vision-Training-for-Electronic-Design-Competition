import struct

'''
协议数据格式：
帧头(0xAA) + 数据域长度 + 数据域 + 长度及数据域数据和校验 + 帧尾(0x55)
'''

class SerialProtocol():
    HEAD = 0xAA
    TAIL = 0x55

    def __init__(self) -> None:
        pass

    def _checksum(self, data:bytes)-> int:
        '''
        计算和校验
        '''
        check_sum = 0
        for a in data:
            check_sum = (check_sum + a) & 0xFF
        return check_sum

    def is_valid(self, raw_data:bytes) -> tuple:
        '''
        判断数据是否有效
        返回值: -1 -- 参数错误 -2 -- 数据长度不够 -3 -- 数据格式错误
        '''
        if len(raw_data) == 0:
            return (-1, 0)

        bytes_redundant = 0
        index = 0
        for a in raw_data:
            if a != SerialProtocol.HEAD:
                index += 1
            else:
                break
        bytes_redundant = index

        if len(raw_data[index:]) < 3:
            return (-2, bytes_redundant)

        payload_len = struct.unpack('<H', raw_data[index+1:index+3])[0]
        if len(raw_data)-bytes_redundant < payload_len+5:
            return (-2, bytes_redundant)
        
        if raw_data[index+3+payload_len+1] != SerialProtocol.TAIL or self._checksum(raw_data[index+1:index+3+payload_len]) != raw_data[index+3+payload_len]:
            return (-3, bytes_redundant)
        else:
            return (0, bytes_redundant)

    def length(self, raw_data:bytes) -> int:
        '''
        取得有效数据包的整体长度
        '''
        if len(raw_data) < 5 or raw_data[0] != SerialProtocol.HEAD:
            return -1

        payload_len = struct.unpack('<H', raw_data[1:3])[0]
        return (3+payload_len+2)      


    def encode(self, payload:bytes) -> bytes:
        '''
        编码数据负载部分，添加帧头帧尾校验等部分
        '''
        frame = bytearray()
        frame.append(SerialProtocol.HEAD)
        frame.extend(struct.pack('<H',len(payload)))
        frame.extend(payload)
        frame.append(self._checksum(frame[1:]))
        frame.append(SerialProtocol.TAIL)

        return bytes(frame)

    def decode(self, raw_data:bytes) -> bytes:
        '''
        解码出数据负载部分
        '''
        if len(raw_data) < 5 or raw_data[0] != SerialProtocol.HEAD:
            return bytes()
        
        payload_len = struct.unpack('<H', raw_data[1:3])[0]
        return raw_data[3:3+payload_len]

if __name__ == '__main__':
    payload = 'hello'
    proto = SerialProtocol()

    encoded = proto.encode(payload.encode())
    print(encoded.hex())

    encoded = bytes([0x01,  0x02]) + encoded
    valid = proto.is_valid(encoded)
    print(valid)

    decoded = encoded[valid[1]:]
    decoded = proto.decode(decoded)
    print(decoded.decode())
   
