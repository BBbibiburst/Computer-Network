#coding:gbk
import rdt_sr

# 建立sr连接
address = ('127.0.0.1', 9090)
my_rdt = rdt_sr.rdt_sr(address)
add_send = ('127.0.0.1', 8090)
my_rdt.set_add_sen_to(add_send)
# 接收并写入数据
message = my_rdt.recv()
message = str(message,encoding='utf-8')
with open('recv.txt', 'w', encoding='utf-8') as file:
    file.write(message)
