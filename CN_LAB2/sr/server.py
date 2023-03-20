#coding:gbk
import rdt_sr

# 建立sr连接
my_rdt = rdt_sr.rdt_sr(('127.0.0.1', 8090))
add_send = ('127.0.0.1', 9090)
my_rdt.set_add_sen_to(add_send)
# 发送数据
message = ''
with open('file.txt', 'r', encoding='utf-8') as file:
    for line in file:
        message += line
    my_rdt.sendall(message)
