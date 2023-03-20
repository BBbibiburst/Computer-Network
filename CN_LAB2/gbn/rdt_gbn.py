# coding:gbk
import random
import socket
import time
import select


# 制作数据包
def make_pkt(seg, data, checksum):
    return bytes(str(seg), encoding='utf-8') + b'% %' + data + b'% %' + checksum


# hash函数
def ELFhash(strings):
    hashcode = 0
    x = 0
    str_len = len(strings)
    for i in range(str_len):

        hashcode = (hashcode << 4) + ord(strings[i])
        x = hashcode & 0xF000000000000000
        if x:
            hashcode ^= (x >> 56)
            hashcode &= ~x
    return hashcode


# 生成检验和
def make_checksum(data):
    return bytes(str(ELFhash(str(data, encoding='utf-8'))), encoding='utf-8')


# 解析数据包
def analyse_pkt(message):
    al = message.split(b'% %')
    return al


# 概率丢包
def loss_pkt():
    return random.randint(0, 9) == 1


# gbn协议
class rdt_gbn:
    def __init__(self, address):
        # 对面地址
        self.address_send = None
        # 本机地址
        self.ip = address[0]
        self.port = address[1]
        # socket设置
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(address)
        self.server_socket.settimeout(10)
        self.server_socket.setblocking(False)
        # 滑动窗口设置
        self.base = 0
        self.next_seq_num = 0
        self.window = 10
        self.expect = 0
        self.frag = 30

    # 发送数据包
    def __send(self, total, data, address):
        checksum = make_checksum(data)
        sndpkt = make_pkt(total, data, checksum)
        self.server_socket.sendto(sndpkt, address)

    # 设置对面地址
    def set_add_sen_to(self, address):
        self.address_send = address

    # 接受单个数据
    def rdt_recv(self, address):
        while True:
            try:
                message = self.server_socket.recvfrom(1024)
                # 丢包
                if loss_pkt():
                    return None
                # 解析
                [seg_last, data, checksum] = analyse_pkt(message[0])
                seg = bytes(str(self.expect), encoding='utf-8')
                cs = make_checksum(data)
                # 接收数据并发送ack
                if seg_last == seg and checksum == cs:
                    self.expect += 1
                    print('已接受到', str(seg_last, encoding='utf-8'), data)
                    self.__send(self.expect, b'ACK', address)
                    return data
                if seg_last < seg and checksum == cs:
                    self.__send(self.expect, b'ACK', address)
                self.__send(self.expect, b'ACK', address)
            except:
                pass

    # 发送数据
    def sendall(self, data):
        # 初始化
        data = bytes(data, encoding='utf-8')
        self.base = 0
        self.next_seq_num = 0
        self.expect = 0
        # 数据切片
        data_list = []
        while data != b'':
            data_list.append(data[:self.frag])
            data = data[self.frag:]
        # 发送数据
        while True:
            # 结束本次发送
            if self.base >= len(data_list):
                self.__send(self.base, b'#__END__#', self.address_send)
                break
            # 发送可以发送的数据包
            if self.base == self.next_seq_num:
                # 设置计时器
                start = time.time()
                # 发送数据
                for i in range(self.window):
                    self.__send(self.next_seq_num, data_list[self.next_seq_num], self.address_send)
                    self.next_seq_num += 1
                    # 限制范围
                    if self.next_seq_num >= len(data_list):
                        break
            # 检查超时
            if time.time() - start >= 1:
                self.next_seq_num = self.base
            # 接受ack
            try:
                message = self.server_socket.recvfrom(1024)
                # 模拟丢包
                if loss_pkt():
                    continue
                [seg_last, data, checksum] = analyse_pkt(message[0])
                seg = bytes(str(self.base + 1), encoding='utf-8')
                cs = make_checksum(data)
                # 记录收到的数据包
                if seg_last >= seg and checksum == cs:
                    # 更新base
                    self.base = int(seg_last)
                    print('已发送' + str(self.base - 1) + ' ', data_list[self.base - 1])
            except:
                pass

    # 接受数据
    def recv(self):
        self.base = 0
        self.next_seq_num = 0
        self.expect = 0
        recv_list = b''
        while True:
            data = None
            while data is None:
                data = self.rdt_recv(self.address_send)
            if data == b'#__END__#':
                break
            # 整合数据
            recv_list += data
        return recv_list
