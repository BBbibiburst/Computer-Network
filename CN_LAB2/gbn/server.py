#coding:gbk
import rdt_gbn

# ����gbn����
my_rdt = rdt_gbn.rdt_gbn(('127.0.0.1', 8090))
add_send = ('127.0.0.1', 9090)
my_rdt.set_add_sen_to(add_send)
# ��������
message = ''
with open('file.txt', 'r', encoding='utf-8') as file:
    for line in file:
        message += line
    my_rdt.sendall(message)
# ���ղ�д������
message = my_rdt.recv()
message = str(message, encoding='utf-8')
with open('recv2.txt', 'w', encoding='utf-8') as file:
    file.write(message)
