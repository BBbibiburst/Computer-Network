import random
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
import time

import requests


# cache项定义
class Cached_File:
    def __init__(self, data, Last_modified):
        self.data = data
        self.Last_modified = Last_modified


# cache
header_cache = {}
# 网站限制
limited_web = {}
# 用户限制
limited_user = {}
# 钓鱼网站
fished_web = {}
# 钓鱼导向的网站
fish_to = b'today.hit.edu.cn/'
# 读取信息
with open('limited_web.txt', 'r', encoding='utf-8') as limited_file:
    for line in limited_file:
        limited_web[line.rstrip()] = 1
with open('limited_user.txt', 'r', encoding='utf-8') as limited_file:
    for line in limited_file:
        limited_user[line.rstrip()] = 1
with open('fished_web.txt', 'r', encoding='utf-8') as limited_file:
    for line in limited_file:
        fished_web[line.rstrip()] = 1


# 接收数据
def receive_header(client_socket):
    header = b''
    try:
        while True:
            msg = client_socket.recv(4096)
            # 拼接报文
            header = b"%s%s" % (header, msg)
            if header.endswith(b'\r\n\r\n') or not msg:
                return header
    except Exception:
        return header


# 分析报文，提取出url，port和method
def analyse_header(header):
    global url
    header_split = header.split(b'\r\n')
    head_line = header_split[0].decode('utf8')
    head_line_split = head_line.split(' ')
    method = head_line_split[0]
    # 代理服务器连接请求的情况
    if method == "CONNECT":
        url = head_line_split[1]
        if ':' in url:
            url, port = url.split(':')
            port = int(port)
        else:
            # 默认端口443
            port = 443
    # 其他请求的情况
    else:
        if header == b'':
            return
        # 查找Host行
        for line in header_split:
            if line.startswith(b"Host:"):
                url = line.split(b" ")
                if len(url) < 2:
                    continue
                url = url[1].decode('utf8')
                break
        if ':' in url:
            url, port = url.split(':')
            port = int(port)
        else:
            port = 80
    return url, port, method


# https的Web隧道
def exchange(server, client):
    try:
        while 1:
            data = server.recv(4096)
            if not data:
                return
            client.sendall(data)
    except:
        pass


# 获取Last-Modified信息
def get_cache_time_line(cache):
    for line in cache.split(b'\r\n'):
        if line.startswith(b'Date:'):
            return line[5:]
    return b''


def get_title(cache_header):
    title = {}
    header = cache_header.split(b'\r\n')
    for i in range(len(header)):
        if i == 0:
            continue
        if header[i] == b'':
            continue
        [t, item] = header[i].split(b': ')
        t = str(t, encoding='utf-8')
        item = str(item, encoding='utf-8')
        title[t] = item
    return title


# 检查是否为最新的cache
def check_cache(header, cache_header, url):
    headers_title = get_title(header)
    last_time = str(cache_header.Last_modified[1:], encoding="utf-8")
    headers_title['If-Modified-Since'] = last_time
    headers_title['Cache-Control'] = ''
    s = requests.get(url, headers=headers_title)
    if s.headers['Date'][:-6] == last_time[:-6]:
        return True
    else:
        return False


def http_solve(transform_socket, client_socket, header, method):
    url = header.split(b'\r\n')[0].split(b' ')[1]
    # 有cache的情况
    cache_header = header_cache.get(url)
    if method == 'GET':
        if cache_header is not None:
            # 检查是否为最新的cache
            if check_cache(header, cache_header, url):
                client_socket.sendall(cache_header.data)
                # 显示缓存数
                print('本地cache发送')
                print("cache大小:{}".format(len(header_cache)))
                return
    # 无cache的情况
    transform_socket.sendall(header)
    cache = b''
    try:
        while 1:
            data = transform_socket.recv(1024)
            cache += data
            if not data:
                break
            client_socket.sendall(data)
    except:
        return
    finally:
        if method == "GET" and cache:
            time_line = get_cache_time_line(cache)
            header_cache[url] = Cached_File(cache, time_line)
            # print('cached:\nurl:' + str(cache) + '\ntimeline:' + str(time_line))
        # 显示缓存数
        print("cache大小:{}".format(len(header_cache)))


def sub_thread(client_socket, pool, address):
    # 设置时间限制
    time_limit = 10
    client_socket.settimeout(time_limit)
    # 接受报文
    header = receive_header(client_socket)
    # 无视空报文
    if not header:
        client_socket.close()
        return
    # 解析报文内容
    url, port, method = analyse_header(header)
    # 不允许访问某些网站
    for key in url.split('.'):
        if key in limited_web.keys():
            return
    # 不支持某些用户访问外部网站
    if address[0] in limited_user.keys():
        return
    # 打印客户端请求详情
    if method != 'CONNECT':
        print(
            time.ctime() + ':' + threading.current_thread().name + ' ' + method + ' request to ' + url + ':' + str(
                port))
        # print(header)
    # 建立代理服务器和客户端目标服务器连接socket
    transform_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # 连接目标服务器
        transform_socket.connect((url, port))
        transform_socket.settimeout(time_limit)
        # 钓鱼
        if url in fished_web.keys():
            data = header.replace(b'jwts.hit.edu.cn',b'today.hit.edu.cn')
            socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket1.connect(('today.hit.edu.cn', 80))
            http_solve(socket1, client_socket, data, 'GET')
            print('已钓鱼到：http://today.hit.edu.cn/')
        # https代理服务器隧道连接报文
        if method == 'CONNECT':
            # 完成代理服务器隧道连接
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client_socket.sendall(data)
            # Web隧道盲转发
            pool.submit(exchange, client_socket, transform_socket)
            pool.submit(exchange, transform_socket, client_socket)
        # 其他报文
        else:
            # 传递报文
            pool.submit(http_solve, transform_socket, client_socket, header, method)
            # http_solve(transform_socket, client_socket, header, method)

    except Exception:
        # 关闭socket
        transform_socket.close()
        client_socket.close()


# 服务器主程序
def server_main(ip, port):
    # 服务器初始化
    # 初始化线程池
    pool = ThreadPoolExecutor(max_workers=100)
    # 设置服务器socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(10)
    # 打印提示信息
    print(time.ctime() + ":Server Start")
    print(time.ctime() + ":Server Listening Port {}".format(port))
    print(time.ctime() + ":Waiting for requests...")
    # 主循环
    while True:
        # 接受HTTP请求
        client_socket, address = server_socket.accept()
        # 使用线程池中的线程处理HTTP请求
        # sub_thread(client_socket, pool, address)
        pool.submit(sub_thread, client_socket, pool, address)


if __name__ == '__main__':
    # 服务器ip地址
    IPAddr = '127.0.0.1'
    # 服务器端口
    Port = 8080
    # 服务器开始运行
    server_main(IPAddr, Port)
