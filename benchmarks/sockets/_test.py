import socket
import threading
import time

BYTES = 1000
SIZE = 1
CONCURRENCY = 100
TRIES = 5


def reader(sock):
    expect = BYTES
    while expect > 0:
        d = sock.recv(min(expect, SIZE))
        expect -= len(d)


def writer(addr, socket_impl):
    sock = socket_impl(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(addr)
    sent = 0
    while sent < BYTES:
        d = b'xy' * (max(min(SIZE / 2, BYTES - sent), 1))
        sock.sendall(d)
        sent += len(d)


def accepter(server_sock, pool):
    for i in range(CONCURRENCY):
        sock, addr = server_sock.accept()
        t = threading.Thread(None, reader, "reader thread", (sock,))
        t.start()
        pool.append(t)


def launch_threads():
    threads = []
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(('localhost', 0))
    server_sock.listen(CONCURRENCY)
    addr = ('localhost', server_sock.getsockname()[1])
    accepter_thread = threading.Thread(
        None, accepter, "accepter thread", (server_sock, threads))
    accepter_thread.start()
    threads.append(accepter_thread)
    for i in range(CONCURRENCY):
        client_thread = threading.Thread(None, writer, "writer thread", (addr, socket.socket))
        client_thread.start()
        threads.append(client_thread)
    for t in threads:
        t.join()


def main():
    now = time.perf_counter()
    launch_threads()
    print('%f' % (time.perf_counter() - now))


main()