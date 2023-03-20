# coding:gbk
import random
import socket
import time
import select


# �������ݰ�
def make_pkt(seg, data, checksum):
    return bytes(str(seg), encoding='utf-8') + b'% %' + data + b'% %' + checksum


# hash����
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


# ���ɼ����
def make_checksum(data):
    return bytes(str(ELFhash(str(data, encoding='utf-8'))), encoding='utf-8')


# �������ݰ�
def analyse_pkt(message):
    al = message.split(b'% %')
    return al


# ���ʶ���
def loss_pkt():
    return random.randint(0, 9) == 1


# gbnЭ��
class rdt_gbn:
    def __init__(self, address):
        # �����ַ
        self.address_send = None
        # ������ַ
        self.ip = address[0]
        self.port = address[1]
        # socket����
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(address)
        self.server_socket.settimeout(10)
        self.server_socket.setblocking(False)
        # ������������
        self.base = 0
        self.next_seq_num = 0
        self.window = 10
        self.expect = 0
        self.frag = 30

    # �������ݰ�
    def __send(self, total, data, address):
        checksum = make_checksum(data)
        sndpkt = make_pkt(total, data, checksum)
        self.server_socket.sendto(sndpkt, address)

    # ���ö����ַ
    def set_add_sen_to(self, address):
        self.address_send = address

    # ���ܵ�������
    def rdt_recv(self, address):
        while True:
            try:
                message = self.server_socket.recvfrom(1024)
                # ����
                if loss_pkt():
                    return None
                # ����
                [seg_last, data, checksum] = analyse_pkt(message[0])
                seg = bytes(str(self.expect), encoding='utf-8')
                cs = make_checksum(data)
                # �������ݲ�����ack
                if seg_last == seg and checksum == cs:
                    self.expect += 1
                    print('�ѽ��ܵ�', str(seg_last, encoding='utf-8'), data)
                    self.__send(self.expect, b'ACK', address)
                    return data
                if seg_last < seg and checksum == cs:
                    self.__send(self.expect, b'ACK', address)
                self.__send(self.expect, b'ACK', address)
            except:
                pass

    # ��������
    def sendall(self, data):
        # ��ʼ��
        data = bytes(data, encoding='utf-8')
        self.base = 0
        self.next_seq_num = 0
        self.expect = 0
        # ������Ƭ
        data_list = []
        while data != b'':
            data_list.append(data[:self.frag])
            data = data[self.frag:]
        # ��������
        while True:
            # �������η���
            if self.base >= len(data_list):
                self.__send(self.base, b'#__END__#', self.address_send)
                break
            # ���Ϳ��Է��͵����ݰ�
            if self.base == self.next_seq_num:
                # ���ü�ʱ��
                start = time.time()
                # ��������
                for i in range(self.window):
                    self.__send(self.next_seq_num, data_list[self.next_seq_num], self.address_send)
                    self.next_seq_num += 1
                    # ���Ʒ�Χ
                    if self.next_seq_num >= len(data_list):
                        break
            # ��鳬ʱ
            if time.time() - start >= 1:
                self.next_seq_num = self.base
            # ����ack
            try:
                message = self.server_socket.recvfrom(1024)
                # ģ�ⶪ��
                if loss_pkt():
                    continue
                [seg_last, data, checksum] = analyse_pkt(message[0])
                seg = bytes(str(self.base + 1), encoding='utf-8')
                cs = make_checksum(data)
                # ��¼�յ������ݰ�
                if seg_last >= seg and checksum == cs:
                    # ����base
                    self.base = int(seg_last)
                    print('�ѷ���' + str(self.base - 1) + ' ', data_list[self.base - 1])
            except:
                pass

    # ��������
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
            # ��������
            recv_list += data
        return recv_list
