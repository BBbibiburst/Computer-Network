#coding:gbk
import rdt_gbn

# 建立gbn连接
address = ('127.0.0.1', 9090)
my_rdt = rdt_gbn.rdt_gbn(address)
add_send = ('127.0.0.1', 8090)
my_rdt.set_add_sen_to(add_send)
# 接收并写入数据
message = my_rdt.recv()
message = str(message,encoding='utf-8')
with open('recv1.txt', 'w', encoding='utf-8') as file:
    file.write(message)
# 发送数据
message = ''
with open('file.txt', 'r', encoding='utf-8') as file:
    for line in file:
        message += line
    my_rdt.sendall(message)
