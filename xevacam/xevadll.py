'''
Created on 16.11.2016

@author: Samuli Rahkonen
'''

from sys import platform as sys_plat
import os
import ctypes
from ctypes import windll, cdll, CDLL, WINFUNCTYPE, CFUNCTYPE, \
                   c_void_p, c_int32, c_char_p, c_bool, c_ulong, \
                   create_string_buffer, c_uint


# Callback Function Type
# if sys_plat == "win32":
#     CB_FUNCTYPE = WINFUNCTYPE
# else:
#     # Untested!
#     CB_FUNCTYPE = CFUNCTYPE


def error2str(errcode):
    s = create_string_buffer(1024)
    size = XDLL.error_to_string(errcode, s, 1024)
    return 'Error code: %s (%s), msgsize: %s, msg: %s' % (str(errcode),
                                                          XDLL.errcodes[errcode],
                                                          str(size),
                                                          repr(s.value))


def print_error(errcode):
    print(error2str(errcode))

if os.name == 'nt':
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    def check_bool(result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return args

    kernel32.LoadLibraryExW.errcheck = check_bool
    kernel32.LoadLibraryExW.restype = wintypes.HMODULE
    kernel32.LoadLibraryExW.argtypes = (wintypes.LPCWSTR,
                                        wintypes.HANDLE,
                                        wintypes.DWORD)


class CDLLEx(ctypes.CDLL):
    def __init__(self, name, mode=0, handle=None,
                 use_errno=True, use_last_error=False):
        if os.name == 'nt' and handle is None:
            handle = kernel32.LoadLibraryExW(name, None, mode)
        super(CDLLEx, self).__init__(name, mode, handle,
                                     use_errno, use_last_error)


class WinDLLEx(ctypes.WinDLL):
    def __init__(self, name, mode=0, handle=None,
                 use_errno=False, use_last_error=True):
        if os.name == 'nt' and handle is None:
            handle = kernel32.LoadLibraryExW(name, None, mode)
        super(WinDLLEx, self).__init__(name, mode, handle,
                                       use_errno, use_last_error)

DONT_RESOLVE_DLL_REFERENCES = 0x00000001
LOAD_LIBRARY_AS_DATAFILE = 0x00000002
LOAD_WITH_ALTERED_SEARCH_PATH = 0x00000008
LOAD_IGNORE_CODE_AUTHZ_LEVEL = 0x00000010  # NT 6.1
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020  # NT 6.0
LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE = 0x00000040  # NT 6.0

# These cannot be combined with LOAD_WITH_ALTERED_SEARCH_PATH.
# Install update KB2533623 for NT 6.0 & 6.1.
LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR = 0x00000100
LOAD_LIBRARY_SEARCH_APPLICATION_DIR = 0x00000200
LOAD_LIBRARY_SEARCH_USER_DIRS = 0x00000400
LOAD_LIBRARY_SEARCH_SYSTEM32 = 0x00000800
LOAD_LIBRARY_SEARCH_DEFAULT_DIRS = 0x00001000


class XDLL(object):
    ''' Talks to xeneth64.dll '''

    # ctypes.WinDLL('kernel32')
    # directory = 'C:\\MyTemp\\envs\\xevacam\\Lib\\site-packages\\'
    directory = r'C:\Program Files\Common Files\XenICs\Runtime'
    # directory = ''
    # print(xenethC_path)
    # os.chdir(directory)
    # _xenethDLL = windll.LoadLibrary(os.path.join(directory, 'xeneth64.dll'))
    _xenethDLL = WinDLLEx(os.path.join(directory, 'xeneth64.dll'),
                          LOAD_WITH_ALTERED_SEARCH_PATH)

    # C Enumerations

    # Error codes
    I_OK = 0
    I_DIRTY = 1
    E_BUG = 10000
    E_NOINIT = 10001
    E_LOGICLOADFAILED = 10002
    E_INTERFACE_ERROR = 10003
    E_OUT_OF_RANGE = 10004
    E_NOT_SUPPORTED = 10005
    E_NOT_FOUND = 10006
    E_FILTER_DONE = 10007
    E_NO_FRAME = 10008
    E_SAVE_ERROR = 10009
    E_MISMATCHED = 10010
    E_BUSY = 10011
    E_INVALID_HANDLE = 10012
    E_TIMEOUT = 10013
    E_FRAMEGRABBER = 10014
    E_NO_CONVERSION = 10015
    E_FILTER_SKIP_FRAME = 10016
    E_WRONG_VERSION = 10017
    E_PACKET_ERROR = 10018
    E_WRONG_FORMAT = 10019
    E_WRONG_SIZE = 10020
    E_CAPSTOP = 10021
    E_OUT_OF_MEMORY = 10022
    E_RFU = 10023

    # Used for conversion to string
    errcodes = {I_OK: 'I_OK',
                I_DIRTY: 'I_DIRTY',
                E_BUG: 'E_BUG',
                E_NOINIT: 'E_NOINIT',
                E_LOGICLOADFAILED: 'E_LOGICLOADFAILED',
                E_INTERFACE_ERROR: 'E_INTERFACE_ERROR',
                E_OUT_OF_RANGE: 'E_OUT_OF_RANGE',
                E_NOT_SUPPORTED: 'E_NOT_SUPPORTED',
                E_NOT_FOUND: 'E_NOT_FOUND',
                E_FILTER_DONE: 'E_FILTER_DONE',
                E_NO_FRAME: 'E_NO_FRAME',
                E_SAVE_ERROR: 'E_SAVE_ERROR',
                E_MISMATCHED: 'E_MISMATCHED',
                E_BUSY: 'E_BUSY',
                E_INVALID_HANDLE: 'E_INVALID_HANDLE',
                E_TIMEOUT: 'E_TIMEOUT',
                E_FRAMEGRABBER: 'E_FRAMEGRABBER',
                E_NO_CONVERSION: 'E_NO_CONVERSION',
                E_FILTER_SKIP_FRAME: 'E_FILTER_SKIP_FRAME',
                E_WRONG_VERSION: 'E_WRONG_VERSION',
                E_PACKET_ERROR: 'E_PACKET_ERROR',
                E_WRONG_FORMAT: 'E_WRONG_FORMAT',
                E_WRONG_SIZE: 'E_WRONG_SIZE',
                E_CAPSTOP: 'E_CAPSTOP',
                E_OUT_OF_MEMORY: 'E_OUT_OF_MEMORY',
                E_RFU: 'E_RFU'}  # The last one is uncertain

    # Frame types, ulong
    FT_UNKNOWN = -1
    FT_NATIVE = 0
    FT_8_BPP_GRAY = 1
    FT_16_BPP_GRAY = 2
    FT_32_BPP_GRAY = 3
    FT_32_BPP_RGBA = 4
    FT_32_BPP_RGB = 5
    FT_32_BPP_BGRA = 6
    FT_32_BPP_BGR = 7

    # Pixel size in bytes, used for conversion
    pixel_sizes = {FT_UNKNOWN: 0,  # Unknown
                   FT_NATIVE: 0,  # Unknown, ask with get_frame_type
                   FT_8_BPP_GRAY: 1,
                   FT_16_BPP_GRAY: 2,
                   FT_32_BPP_GRAY: 4,
                   FT_32_BPP_RGBA: 4,
                   FT_32_BPP_RGB: 4,
                   FT_32_BPP_BGRA: 4,
                   FT_32_BPP_BGR: 4}

    # GetFrameFlags, ulong
    XGF_Blocking = 1
    XGF_NoConversion = 2
    XGF_FetchPFF = 4
    XGF_RFU_1 = 8
    XGF_RFU_2 = 16
    XGF_RFU_3 = 32

    # LoadCalibration flags
    # Starts the software correction filter after unpacking the
    # calibration data
    XLC_StartSoftwareCorrection = 1
    XLC_RFU_1 = 2
    XLC_RFU_2 = 4
    XLC_RFU_3 = 8

    # C functions

    # XCHANDLE XC_OpenCamera (const char * pCameraName = "cam://default",
    #                         XStatus pCallBack = 0, void * pUser = 0);
    open_camera = _xenethDLL.XC_OpenCamera
    open_camera.restype = c_int32  # XCHANDLE
    # open_camera.argtypes = (c_char_p,)
    # open_camera.argtypes = (c_char_p, CB_FUNCTYPE(None), c_void_p)

    error_to_string = _xenethDLL.XC_ErrorToString
    error_to_string.restype = c_int32
    error_to_string.argtypes = (c_int32, c_char_p, c_int32)

    is_initialised = _xenethDLL.XC_IsInitialised
    is_initialised.restype = c_int32
    is_initialised.argtypes = (c_int32,)

    start_capture = _xenethDLL.XC_StartCapture
    start_capture.restype = c_ulong  # ErrCode
    start_capture.argtypes = (c_int32,)

    is_capturing = _xenethDLL.XC_IsCapturing
    is_capturing.restype = c_bool
    is_capturing.argtypes = (c_int32,)

    get_frame_size = _xenethDLL.XC_GetFrameSize
    get_frame_size.restype = c_ulong
    get_frame_size.argtypes = (c_int32,)  # Handle

    get_frame_type = _xenethDLL.XC_GetFrameType
    get_frame_type.restype = c_ulong  # Returns enum
    get_frame_type.argtypes = (c_int32,)  # Handle

    get_frame_width = _xenethDLL.XC_GetWidth
    get_frame_width.restype = c_ulong
    get_frame_width.argtypes = (c_int32,)  # Handle

    get_frame_height = _xenethDLL.XC_GetHeight
    get_frame_height.restype = c_ulong
    get_frame_height.argtypes = (c_int32,)  # Handle

    get_frame = _xenethDLL.XC_GetFrame
    get_frame.restype = c_ulong  # ErrCode
    get_frame.argtypes = (c_int32, c_ulong, c_ulong, c_void_p, c_uint)

    stop_capture = _xenethDLL.XC_StopCapture
    stop_capture.restype = c_ulong  # ErrCode
    stop_capture.argtypes = (c_int32,)

    close_camera = _xenethDLL.XC_CloseCamera
    # Returns void
    close_camera.argtypes = (c_int32,)  # Handle

    # Calibration
    load_calibration = _xenethDLL.XC_LoadCalibration
    load_calibration.restype = c_ulong  # ErrCode
    # load_calibration.argtypes = (c_int32, c_char_p, c_ulong)

    # ColourProfile
    load_colour_profile = _xenethDLL.XC_LoadColourProfile
    load_colour_profile.restype = c_ulong
    load_colour_profile.argtypes = (c_char_p,)

    # Settings
    load_settings = _xenethDLL.XC_LoadSettings
    load_settings.restype = c_ulong
    load_settings.argtypes = (c_char_p, c_ulong)

    # FileAccessCorrectionFile
    set_property_value = _xenethDLL.XC_SetPropertyValue
    set_property_value.restype = c_ulong  # ErrCode
    # set_property_value.argtypes = (c_int32, c_char_p, c_char_p, c_char_p)
