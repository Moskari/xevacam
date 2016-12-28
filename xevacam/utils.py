'''
Created on 23.11.2016

@author: Samuli Rahkonen
'''

import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pylab
import numpy as np
import xevacam.streams as streams
import threading

def datatype2envitype(datatype):
    DATATYPES = {'u1': 1,
                 'i2': 2,
                 'i4': 3,
                 'f4': 4,
                 'f8': 5,
                 'c4': 6,
                 'c8': 9,
                 'u2': 12,
                 'u4': 13,
                 'i8': 14,
                 'u8': 15}
    t = DATATYPES.get(datatype, None)
    if t is None:
        raise Exception(
            'Given datatype string %s is not valid type.' % str(datatype))
    return t


class PreviewWindow(object):

    def __init__(self, camera, title='XenICs'):
        self.camera = camera
        self.stream = streams.PreviewStream()
        camera.set_handler(self.stream)
        self.size = camera.get_frame_size()
        self.dims = camera.get_frame_dims()
        self.pixel_size = camera.get_pixel_size()
        self.pixel_dtype = camera.get_pixel_dtype()
        self.title = title
        # self._window_thread = threading.Thread(name='window thread',
        #                                        target=self.show_thread,
        #                                        args=(30, 500, 60))

    def _image(self, stream, size, dims, pixel_size_bytes):
        while True:
            img = stream.read(size)
            if img == b'':
                continue
            break
        frame_buffer = np.frombuffer(img,
                                     dtype=self.pixel_dtype,
                                     count=int(size/pixel_size_bytes))
        frame_buffer = np.reshape(frame_buffer, dims)
        return frame_buffer

    def show(self):
        # self._window_thread.start()
        raise NotImplementedError()

    def show_thread(self):
        raise NotImplementedError()

    def close(self):
        # pylab.close()
        plt.close()

    def wait(self):
        print('Waiting for window %s to close.' % str(self))
        self._window_thread.join()
        print('Window closed.')


class RawPreviewWindow(PreviewWindow):

    def __init__(self, camera, interval=60,
                 title='Line scan'):
        super().__init__(camera, title)
        self.interval = interval

    def show(self):
        self._window_thread = threading.Thread(name='raw window thread',
                                               target=self.show_thread,
                                               args=(self.interval))
        self._window_thread.start()

    def show_thread(self, interval=60):
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.title)
        im = plt.imshow(self._image(self.stream,
                                    self.size,
                                    self.dims,
                                    self.pixel_size))
        # im.set_data(image(stream))

        def updatefig(*args):
            img = self._image(self.stream,
                              self.size,
                              self.dims,
                              self.pixel_size)
            im.set_data(img)
            im.set_clim(vmin=0, vmax=10000)
            return im,

        _ = animation.FuncAnimation(self.fig,
                                    updatefig,
                                    interval=60,
                                    blit=True)
        pylab.show()


class LineScanWindow(PreviewWindow):

    def __init__(self, camera, layer_num, num_of_lines=500, interval=60,
                 title='Line scan'):
        super().__init__(camera, title)
        self.layer_num = layer_num
        self.num_of_lines = num_of_lines
        self.interval = interval

    def show(self):
        self._window_thread = threading.Thread(name='line scan window thread',
                                               target=self.show_thread,
                                               args=(self.layer_num,
                                                     self.num_of_lines,
                                                     self.interval))
        self._window_thread.start()

    def show_thread(self, layer_num, num_of_lines=500, interval=60):
        self.fig = plt.figure()
        self.fig.canvas.set_window_title(self.title)
        canvas = np.zeros(
            (num_of_lines, self.dims[1]), dtype=self.pixel_dtype)
        im = plt.imshow(canvas)
        # im.set_data(image(stream))

        def updatefig(*args):
            # plt.pause(0.001)
            img = self._image(self.stream,
                              self.size,
                              self.dims,
                              self.pixel_size)
            canvas[:num_of_lines-1, :] = canvas[1:, :]
            canvas[num_of_lines-1, :] = img[layer_num, :]

            im.set_data(canvas)
            im.set_clim(vmin=0, vmax=10000)
            # self.fig.draw()
            return im,

        _ = animation.FuncAnimation(self.fig,
                                    updatefig,
                                    interval=60,
                                    blit=True)
        pylab.show()
        print('Window thread closed')
        plt


def create_envi_hdr(meta, filepath, extra=None):
    print('Writing to file \'%s\' metadata: %s, extra: %s' % (str(filepath),
                                                              str(meta),
                                                              str(extra)))
    if not isinstance(filepath, str):
        raise Exception(
            'Illegal filepath %s. Metadata: %s' % (str(filepath), str(meta)))
    head, tail = os.path.split(filepath)
    if head != '' and not os.path.exists(head):
        raise Exception(
            'Directory \'%s\' does not exist. Metadata: %s' % (head, str(meta)))
    if tail == '':
        raise Exception(
            'No file name given. Metadata: %s' % str(meta))
    m = meta
    if isinstance(extra, dict):
        m.update(extra)
    with open(filepath, 'w') as f:
        f.write('ENVI\n')
        for name, value in meta:
            line = str(name) + ' = ' + str(value) + '\n'
            print(line)
            f.write(line)


def kbinterrupt_decorate(func):
    '''
    Decorator.

    Adds KeyboardInterrupt handling to for camera methods.
    '''
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            this = args[0]
            this.close()
            raise
    return func_wrapper
