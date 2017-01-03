'''
Created on 9.11.2016

@author: Samuli Rahkonen
'''

import xevacam.camera as camera
# import matplotlib
# import pylab  # Shows the figure in Eclipse + PyDev
# from ctypes import create_string_buffer, c_char_p
# import numpy as np
import io
import xevacam.utils as utils
import xevacam.streams as streams


'''
def image(stream, size, dims, pixel_size_bytes):
    while True:
        img = stream.read(size)
        if img == b'':
            continue
        break
    frame_buffer = np.frombuffer(img, dtype='u%d' % pixel_size_bytes, count=int(frame_size/2))
    frame_buffer = np.reshape(frame_buffer, frame_dims)
    return frame_buffer
'''


if __name__ == '__main__':
    cam = camera.XevaCam(calibration='C:\\MyTemp\\envs\\xevacam\\Lib\\site-packages\\3ms_196_xeneth3.xca')
    # stream = streams.XevaStream()
    file_stream = open('myfile.bin', 'wb')
    # bytes_stream = io.BytesIO()

    # cam.set_handler(stream)
    cam.set_handler(file_stream)
    # cam.set_handler(bytes_stream)
    # cam.set_handler(preview_stream)
    with cam.opened(sw_correction=True) as c:
        window = utils.LineScanWindow(cam, 30)
        c.start_recording()
        window.show()
        c.wait_recording(5)
        meta = c.stop_recording()

        utils.create_envi_hdr(meta, 'myfile.hdr')
    # window.close()
    # from xevacam.envi import ENVIImage
    # with ENVIImage('myfile.bin').open() as img:
    #     print(img.read_numpy_array())

    # window.wait()
    # input('Press enter')
