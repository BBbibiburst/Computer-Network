#coding:gbk
import rdt_gbn

# ����gbn����
address = ('127.0.0.1', 9090)
my_rdt = rdt_gbn.rdt_gbn(address)
add_send = ('127.0.0.1', 8090)
my_rdt.set_add_sen_to(add_send)
# ���ղ�д������
message = my_rdt.recv()
message = str(message,encoding='utf-8')
with open('recv1.txt', 'w', encoding='utf-8') as file:
    file.write(message)
# ��������
message = ''
with open('file.txt', 'r', encoding='utf-8') as file:
    for line in file:
        message += line
    my_rdt.sendall(message)
