# -*- coding: utf-8 -*-

def fib(n):
    if n <= 2:
        return 1
    else:
        return fib(n-1) + fib(n-2)


# fib microservice

from socket import *

def fib_server(address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = sock.accept()
        print('Connection', addr)
        fib_handler(client)

def fib_handler(client):
    while True:
        req = client.recv(100)
        if not req:
            break
        n = int(req)
        result = fib(n)
        resp = str(result).encode('ascii') + b'\n'
        client.send(resp)
    print('Closed')


# The problem with it is that it cann't handle multiple client.


# use thread programming

from socket import *
from threading import Thread

def fib_server(address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = sock.accept()
        print('Connection', addr)
        Thread(target=fib_handler, args=(client,), daemon=True).start()


# perf1
# Time of a long running request

from socket import *
import time

sock = socket(AF_INET, SOCK_STREAM)
sock.connect(('localhost', 25000))

while True:
    start = time.time()
    sock.send(b'30')
    resp = sock.recv(100)
    end = time.time()
    print(end-start)


# run perf1 twice, the running time doubled
# By the way, time of a fast running request
# will not affected by the GIL.


# perf2
# requests/sec of fast requests

from socket import *
from threading import Thread
import time

n = 0

def monitor():
    global n
    while True:
        time.sleep(1)
        print(n, 'reqs/sec')
        n = 0

Thread(target=monitor).start()

sock = socket(AF_INET, SOCK_STREAM)
sock.connect(('localhost', 25000))

while True:
    sock.send(b'1')
    resp = sock.recv(100)
    n += 1


# If somebody requests something that request a bit of CPU work,
# the requests/sec of the fast thing drop off a cliff.
# The GIL prioritizes things that want to run on the CPU.


# use a pool

from socket import *
from concurrent.futures import ProcessPoolExcutor as Pool

pool = Pool(4)

def fib_server(address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    while True:
        client, addr = sock.accept()
        print('Connection', addr)
        fib_handler(client)

def fib_handler(client):
    while True:
        req = client.recv(100)
        if not req:
            break
        n = int(req)
        future = pool.submit(fib, n)
        result = future.result()
        resp = str(result).encode('ascii') + b'\n'
        client.send(resp)
    print('Closed')


# One kind of negative of doing things with the pool like
# that is it does introduce way more overhead on the server side.
# Because you're no longer just computing the one Fibnacci number,
# you're like serializing data, you're sending it off to a 
# subprocess it's computing a result.


# That's one of the things you have to think about with threads.
# If you're going to program with threads you have to stay away
# from CPU bound work, you have to think about pools and other 
# things.


# 综上所述，由于GIL的存在，在python中，对于CPU密集型任务，多线程
# 往往会造成更差的效果。使用进程池可以解决一部分CPU密集型任务的
# 并发问题。另外，GIL有一个调度特点，GIL会高优调度CPU密集型任务，
# 因此如果同时处理长时间的CPU密集型任务和短时间任务，短时间任务的
# qps会受到非常大的影响。
