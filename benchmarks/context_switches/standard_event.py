from threading import Event
import time

CONTEXT_SWITCHES = 1000000


def run():
    wait_event = Event()
    wait_event.set()
    counter = 0
    while counter <= CONTEXT_SWITCHES:
        wait_event.wait()
        wait_event.clear()
        counter += 1
        wait_event.set()


def main():
    now = time.perf_counter()
    run()
    print('%f' % (time.perf_counter() - now))


main()
