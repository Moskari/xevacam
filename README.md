# xevacam

## Synopsis

This Python 3 package is for controlling and capturing image stream from a Xenics XEVA-196 or similar camera. The camera is capable of capturing wider electromagnetic spectrum than a normal camera.

The motivation for this software was the hyperspectral camera which captures light like a line scanner. The electromagnetic spectrum is dispersed through a prism to the sensor of XEVA-196. Moving the camera while continuously recording creates a large image data cube, which can be further analyzed. This software's purpose is to make capturing the data cube easier.   

Only Windows 64 bit compatibility is tested with Xeneth v2.6. See section 'Installation' for required dependencies.

![alt tag](https://dl.dropboxusercontent.com/u/39458993/github/xevacam/images/xeva196_1_mod.jpg)

## Code Example:

### Video capture to a file and stream

Capture 5 seconds of raw data from the camera to a `file object` and `BytesIO` stream. (or any user specified stream that has `write()` and `read()` functions).

```python
import xevacam.camera as camera
import io
# Specify Xeneth calibration file if any
cam = camera.XevaCam(calibration='C:\\calibration_file.xca')
# Specify stream objects to which camera writes its output
file_stream = open('myfile.bin', 'wb')
bytes_stream = io.BytesIO()
cam.set_handler(file_stream)
cam.set_handler(bytes_stream)
# Open connection to camera
with cam.opened() as c:
    c.start_recording()
    c.wait_recording(5)  # Record for 5 seconds
    meta = c.stop_recording()  # Return metadata about the clip
    # Optional: Create ENVI formatted header for the clip 
    utils.create_envi_hdr(meta, 'myfile.hdr')
# Connection closed
```

### Experimental video feed with Matplotlib

![alt tag](https://dl.dropboxusercontent.com/u/39458993/github/xevacam/images/linescanwindow.png)

`xevacam.utils` includes window classes for showing a real-time video feed. At the moment a window is opened in its own thread which is not especially Matplotlib compatible and ends in a run-time exception when window closes (Matplotlib mandates that the plot window has to run in the main thread).

```python
import xevacam.camera as camera
import xevacam.utils as utils
cam = camera.XevaCam(calibration='C:\\calibration_file.xca')
# Open connection to camera
with cam.opened() as c:
	# Create a window and connect it to the camera output
	# Line scanner view. Show 30th line in the frame (30th band in data cube)  
    window = utils.LineScanWindow(cam, 30)
    c.start_recording()
    window.show()  # Show it
    c.wait_recording(5)
    meta = c.stop_recording()
```

## Installation

Tested only with Python 3.5 (Windows). Numpy is required, Matplotlib is optional.

**Windows**
Requires Xeneth SDK 64 bit runtime DLL's (mainly Xeneth64.dll and its dependencies). They are not provided in this package.

Current version expects the runtime DLL's to locate under "C:\Program Files\Common Files\XenICs\Runtime".

**Linux**
Not supported at the moment. (However, installing Linux SDK with dynamically linking libraries and modifying xevadll.py to use those files instead could work)

Install with pip:
`pip install <directory path to setup.py>`


## License

The MIT License (MIT)

**Disclaimer**
The author disclaims all responsibility for possible damage to equipment and/or people. Use the software with your own risk.
