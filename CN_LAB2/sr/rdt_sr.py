#coding:gbk
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
    return bytes(str(ELFhash(str(data,encoding='utf-8'))),encoding='utf-8')


# 解析数据包
def analyse_pkt(message):
    al = message.split(b'% %')
    return al


# 概率丢包
def loss_pkt():
    return random.randint(0, 9) == 0


# sr协议
class rdt_sr:
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
        self.time_limit = 1
        self.frag = 30

    # 发送数据包
    def __send(self, total, data, address):
        checksum = make_checksum(data)
        sndpkt = make_pkt(total, data, checksum)
        self.server_socket.sendto(sndpkt, address)

    #设置对面地址
    def set_add_sen_to(self, address):
        self.address_send = address

    # 接受单个数据
    def rdt_recv(self, address):
        while True:
            try:
                message = self.server_socket.recvfrom(1024)
                # 丢包
                if loss_pkt():
                    return None, None
                # 解析
                [seg_last, data, checksum] = analyse_pkt(message[0])
                seg = str(seg_last, encoding='utf-8')
                cs = make_checksum(data)
                # 接收数据并发送ack
                if checksum == cs:
                    print('已接受到', seg, data)
                    self.__send(int(seg) + 1, b'ACK', address)
                    return data, int(str(seg_last, encoding='utf-8'))
            except:
                pass

    # 发送数据
    def sendall(self, data):
        # 初始化
        data = bytes(data, encoding='utf-8')
        self.base = 0
        self.next_seq_num = 0
        self.expect = 0
        data_list = []
        timer_dict = {}
        reset_dict = {}
        # 数据切片
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
            if self.next_seq_num < self.base + self.window:
                for i in range(self.window):
                    if self.next_seq_num >= len(data_list):
                        continue
                    # 发送数据
                    self.__send(self.next_seq_num, data_list[self.next_seq_num], self.address_send)
                    # 设置计时器
                    timer_dict[data_list[self.next_seq_num]] = (time.time(), self.next_seq_num)
                    self.next_seq_num += 1
                    # 限制范围
                    if self.next_seq_num >= len(data_list):
                        break
            # 检查超时
            for key, timer in timer_dict.items():
                if timer[0] is None:
                    reset_dict[key] = timer
                    continue
                if time.time() - timer[0] >= self.time_limit:
                    self.__send(timer[1], key, self.address_send)
                    reset_dict[key] = (time.time(), timer[1])
            # 修改计时器
            for key, timer in reset_dict.items():
                if timer[0] is None:
                    del timer_dict[key]
                timer_dict[key] = timer
            # 接受ack
            try:
                message = self.server_socket.recvfrom(1024)
                # 模拟丢包
                if loss_pkt():
                    continue
                [seg_last, data, checksum] = analyse_pkt(message[0])
                cs = make_checksum(data)
                seg = int(seg_last) - 1
                # 记录收到的数据包
                if seg >= self.base and seg < self.next_seq_num:
                    timer_dict[data_list[seg]] = (None, timer_dict[data_list[seg]][1])
                    print('已发送' + str(seg) + ' ', data_list[seg])
                # 更新base
                pos = 0
                for i in range(self.base, self.next_seq_num):
                    if timer_dict[data_list[i]][0] is None:
                        if i == self.base + pos:
                            pos += 1
                self.base += pos
            except:
                pass

    # 接受数据
    def recv(self):
        self.base = 0
        self.next_seq_num = 0
        self.expect = 0
        recv_list = {}
        while True:
            data = None
            while data is None:
                data, pos = self.rdt_recv(self.address_send)
            if data == b'#__END__#':
                break
            recv_list[pos] = data
        # 整合数据
        result = b''
        for i in range(len(recv_list)):
            result += recv_list[i]
        return result
