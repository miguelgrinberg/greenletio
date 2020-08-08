import random
from eventlet.green import threading
from eventlet.green import time


def t():
    for i in range(1000):
        time.sleep(random.random() / 1000)


def run():
    threads = [threading.Thread(target=t) for i in range(300)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()


def main():
    now = time.perf_counter()
    run()
    print('%f' % (time.perf_counter() - now))


main()
