'''
Created on 23.11.2016

@author: Samuli Rahkonen
'''
import io
import threading


class XevaStream(io.IOBase):

    def __init__(self):
        super().__init__()
        self.queue_lock = threading.Lock()
        self._queue = []
        # self.remaining = bytearray()
        # self.memview = memoryview(self.remaining)

    def readable(self):
        return True

    def writable(self):
        return True

    def write(self, b):
        self.queue_lock.acquire()
        self._queue.append(b)
        self.queue_lock.release()
        return len(b)

    def read(self, n=-1):
        self.queue_lock.acquire()
        if len(self._queue) > 0:
            b = self._queue.pop(0)
        else:
            b = b''
        self.queue_lock.release()
        return b

    def is_queue_empty(self):
        self.queue_lock.acquire()
        size = len(self._queue)
        self.queue_lock.release()
        return size == 0

    def clear_queue(self):
        self.queue_lock.acquire()
        self._queue = []
        self.queue_lock.release()


class PreviewStream(io.IOBase):

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._current_frame = bytes()

    def readable(self):
        return True

    def writable(self):
        return True

    def write(self, b):
        with self._lock:
            self._current_frame = b
        return len(b)

    def read(self, n=-1):
        with self._lock:
            b = self._current_frame
        return b

# class XevaBufferedStream(io.BufferedRandom):
#     def __init__(self, buffer_size=io.DEFAULT_BUFFER_SIZE):
#         super().__init__(DataStream(), buffer_size=buffer_size)

