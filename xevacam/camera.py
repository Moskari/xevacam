'''
Created on 9.11.2016

@author: Samuli Rahkonen
'''

import numpy as np
import xevacam.xevadll as xdll
# from xevacam.xevadll import XDLL, error2str, print_error
from contextlib import contextmanager
import threading
import time
import xevacam.utils as utils
from xevacam.utils import kbinterrupt_decorate


class XevaCam(object):

    def __init__(self, calibration=''):
        '''
        Constructor

        @param calibration: Bytes string path to the calibration file (.xca)
        '''
        self.handle = 0
        # self.lines = []
        self._enabled = False
        self.enabled_lock = threading.Lock()
        self.handlers = []  # For storing, streaming etc the data
        self.calibration = calibration.encode('utf-8')  # Path to .xca file
        self._capture_thread = threading.Thread(name='capture_thread',
                                                target=self.capture_frame_stream)
                                        # args=(self.handlers))

    @contextmanager
    def open(self, camera_path='cam://0', sw_correction=True):
        '''
        Opens connection to the camera and closes it in controlled fashion when
        exiting the context.

        @param camera_path: String path to the camera. Default is 'cam://0'
        @param sw_correction: Use previously defined calibration file (.xca)
        '''
        try:
            self.handle = \
                xdll.XDLL.open_camera(camera_path.encode('utf-8'), 0, 0)
            print('XCHANDLE:', self.handle)
            if self.handle == 0:
                raise Exception('Handle is NULL')
            if not xdll.XDLL.is_initialised(self.handle):
                raise Exception('Initialization failed.')
            if self.calibration:
                if sw_correction:
                    flag = xdll.XDLL.XLC_StartSoftwareCorrection
                else:
                    flag = 0
                error = xdll.XDLL.load_calibration(self.handle,
                                                   self.calibration,
                                                   flag)
                if error != xdll.XDLL.I_OK:
                    msg = 'Could\'t load' + \
                        'calibration file ' + \
                        str(self.calibration) + \
                        xdll.error2str(error)
                    raise Exception(msg)
            yield self
        finally:
            self.close()

    def close(self):
        '''
        Stops capturing, closes capture thread, closes connection.
        '''
        try:
            if xdll.XDLL.is_capturing(self.handle):
                print('Stop capturing')
                error = xdll.XDLL.stop_capture(self.handle)
                if error != xdll.XDLL.I_OK:
                    xdll.print_error(error)
                    raise Exception('Could not stop capturing')
                self.enabled = False
                self._capture_thread.join(1)
                if self._capture_thread.isAlive():
                    raise Exception('Thread didn\'t stop.')
        except:
            print('Something went wrong closing the camera.')
            raise
        finally:
            if xdll.XDLL.is_initialised(self.handle):
                print('Closing connection.')
                xdll.XDLL.close_camera(self.handle)

    @property
    def enabled(self):
        '''
        Is capture thread enabled.
        @return: True/False
        '''
        with self.enabled_lock:
            val = self._enabled
        return val

    @enabled.setter
    def enabled(self, value):
        '''
        Signals capture thread to shut down when set to False.
        Otherwise always True.
        '''
        with self.enabled_lock:
            self._enabled = value

    def get_frame_size(self):
        '''
        Asks the camera what is the frame size in bytes.
        @return: c_ulong
        '''
        frame_size = xdll.XDLL.get_frame_size(self.handle)  # Size in bytes
        return frame_size

    def get_frame_dims(self):
        '''
        Returns frame dimensions in tuple(height, width).
        @return: tuple (c_ulong, c_ulong)
        '''
        frame_width = xdll.XDLL.get_frame_width(self.handle)
        frame_height = xdll.XDLL.get_frame_height(self.handle)
        print('width:', frame_width, 'height:', frame_height)
        return frame_height, frame_width

    def get_frame_type(self):
        '''
        Returns enumeration of camera's frame type.
        @return: c_ulong
        '''
        return xdll.XDLL.get_frame_type(self.handle)

    def get_pixel_dtype(self):
        '''
        Returns numpy dtype of the camera's configured data type for frame
        @return: Numpy dtype (np.uint8, np.uint16 or np.uint32)
        '''
        bytes_in_pixel = self.get_pixel_size()
        conversions = (None, np.uint8, np.uint16, None, np.uint32)
        try:
            pixel_dtype = conversions[bytes_in_pixel]
        except:
            raise Exception('Unsupported pixel size %s' % str(bytes_in_pixel))
        if conversions is None:
            raise Exception('Unsupported pixel size %s' % str(bytes_in_pixel))
        return pixel_dtype

    def get_pixel_size(self):
        '''
        Returns a frame pixel's size in bytes.
        @return: int
        '''
        frame_t = xdll.XDLL.get_frame_type(self.handle)
        return xdll.XDLL.pixel_sizes[frame_t]

    def get_frame(self, buffer, frame_t, size, flag=0):
        '''
        Reads a frame from camera. Raises an exception on errors.

        @param buffer: bytes buffer (output) to which a frame is read from
                       the camera.
        @param frame_t: frame type enumeration. Use get_frame_type() to find
                        the native type.
        @param size: frame size in bytes. Use get_frame_dims()
        @param flag: Type of execution. 0 is non-blocking, xdll.XGF_Blocking
                     is blocking.
        @return: True if got frame, otherwise False
        '''
        # frame_buffer = \
        #     np.zeros((frame_size / pixel_size,),
        #              dtype=np.int16)
        # frame_buffer = bytes(frame_size)
        error = xdll.XDLL.get_frame(self.handle,
                                    frame_t,
                                    flag,
                                    # frame_buffer.ctypes.data,
                                    buffer,
                                    size)
        # ctypes.cast(buffer, ctypes.POINTER(ctypes.c))
        if error not in (xdll.XDLL.I_OK, xdll.XDLL.E_NO_FRAME):
            raise Exception(
                'Error while getting frame: %s' % xdll.error2str(error))
        # frame_buffer = np.reshape(frame_buffer, frame_dims)
        return error == xdll.XDLL.I_OK  # , frame_buffer

    def set_handler(self, handler):
        '''
        Adds a new output to which frames are written.

        @param handler: a file-like object, a stream or object with write()
                        and read() methods.
        '''
        self.handlers.append(handler)

    @kbinterrupt_decorate
    def start_recording(self):
        '''
        Starts recording frames to handlers.
        '''
        self.enabled = True
        self._capture_thread.start()

    @kbinterrupt_decorate
    def wait_recording(self, seconds):
        '''
        Blocks execution.
        @param seconds: Time how long the function blocks the execution.
        '''
        time.sleep(seconds)

    @kbinterrupt_decorate
    def stop_recording(self):
        '''
        Stops capturing frames after the latest one is done capturing.
        @return: Metadata tuple array
        '''
        self.enabled = False
        self._capture_thread.join(5)
        if self._capture_thread.isAlive():
            raise Exception('Thread didn\'t stop.')
        error = xdll.XDLL.stop_capture(self.handle)
        if error != xdll.XDLL.I_OK:
            xdll.print_error(error)
            raise Exception(
                'Could not stop capturing. %s' % xdll.error2str(error))
        # Return ENVI metadata about the recording
        frame_dims = self.get_frame_dims()
        frame_type = self.get_frame_type()
        meta = (('samples', frame_dims[1]),
                ('bands', self.frames_count),
                ('lines', frame_dims[0]),
                ('data type',
                 utils.datatype2envitype(
                     'u' + str(xdll.XDLL.pixel_sizes[frame_type]))),
                ('interleave', 'bil'),
                ('byte order', 1))
        return meta

    def capture_frame_stream(self):
        '''
        Thread function for continuous camera capturing.
        Keeps running until 'enabled' property is set to False.
        '''
        name = 'capture_frame_stream'
        error = xdll.XDLL.start_capture(self.handle)
        if error != xdll.XDLL.I_OK:
            xdll.print_error(error)
            raise Exception(
                '%s Starting capture failed! %s' % (name, xdll.error2str(error)))
        if xdll.XDLL.is_capturing(self.handle) == 0:
            for i in range(5):
                if xdll.XDLL.is_capturing(self.handle) == 0:
                    print(name, 'Camera is not capturing. Retry number %d' % i)
                    time.sleep(0.1)
                else:
                    break
        if xdll.XDLL.is_capturing(self.handle) == 0:
            raise Exception('Camera is not capturing.')
        elif xdll.XDLL.is_capturing(self.handle):
            self.frames_count = 0
            size = self.get_frame_size()
            dims = self.get_frame_dims()
            frame_t = self.get_frame_type()
            # pixel_size = self.get_pixel_size()
            print(name, 'Size:', size, 'Dims:', dims, 'Frame type:', frame_t)
            frame_buffer = bytes(size)
            while self._enabled:
                # frame_buffer = \
                #     np.zeros((size / pixel_size,),
                #              dtype=np.int16)
                # buffer = memoryview(frame_buffer)
                while True:
                    ok = self.get_frame(frame_buffer,
                                        frame_t=frame_t,
                                        size=size,
                                        flag=0)  # Non-blocking
                    # xdll.XGF_Blocking
                    if ok:
                        for h in self.handlers:
                            print(name,
                                  'Writing to %s' % str(h.__class__.__name__))
                            wrote_bytes = h.write(frame_buffer)
                            print(name,
                                  'Wrote to %s:' % str(h.__class__.__name__),
                                  wrote_bytes,
                                  'bytes')
                        break
                    # else:
                    #     print(name, 'Missed frame', i)
                self.frames_count += 1
        else:
            raise Exception('Camera is not capturing.')
        print(name, 'Thread closed')

    def capture_single_frame(self):
        '''
        TODO: Not tested
        '''
        name = 'capture_single_frame'
        frame = None
        error = xdll.XDLL.start_capture(self.handle)
        if error != xdll.XDLL.I_OK:
            xdll.print_error(error)
            raise Exception(
                '%s Starting capture failed! %s' % (name, xdll.error2str(error)))
        if xdll.XDLL.is_capturing(self.handle) == 0:
            for i in range(5):
                if xdll.XDLL.is_capturing(self.handle) == 0:
                    print(name, 'Camera is not capturing. Retry number %d' % i)
                    time.sleep(0.1)
                else:
                    break
        if xdll.XDLL.is_capturing(self.handle) == 0:
            raise Exception('Camera is not capturing.')
        elif xdll.XDLL.is_capturing(self.handle):
            size = self.get_frame_size()
            dims = self.get_frame_dims()
            frame_t = self.get_frame_type()
            # pixel_size = self.get_pixel_size()
            print(name, 'Size:', size, 'Dims:', dims, 'Frame type:', frame_t)
            frame_buffer = bytes(size)

            while True:
                ok = self.get_frame(frame_buffer,
                                    frame_t=frame_t,
                                    size=size,
                                    dims=dims,
                                    flag=0)  # Non-blocking
                # xdll.XGF_Blocking
                if ok:
                    frame = frame_buffer
                    break
                # else:
                #     print(name, 'Missed frame', i)
        else:
            raise Exception('Camera is not capturing.')
        print(name, 'Finished')
        return frame, size, dims, frame_t


class XevaImage(object):

    def __init__(self, byte_stream, dims, dtype):
        import io
        if not isinstance(byte_stream, io.BytesIO):
            raise Exception('')
        self.stream = byte_stream

    @contextmanager
    def open(self, mode='r'):
        try:
            yield self
        finally:
            pass

    def read_numpy_array(self, target_order=None):
        ''' Reads BytesIO stream Numpy 3D ndarray '''
        self.stream.read()
        # TODO:
        # map(lambda x: x, self.lines)
        # trans = self._get_permutation_tuple(interleave_order, target_order)
        # data = np.transpose(data, trans)
        # return data
        return 0
