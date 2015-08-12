import numpy as np
import os
import ctypes

__all__ = ['move_to_next_event','file_open','close_file',
           'get_global_event_count','get_run_number',
           'get_num_telescope','get_teldata_list',
           'get_num_teldata','get_num_channel','get_num_pixels',
           'get_num_samples','get_adc_sample','get_adc_sum'
           ,'get_data_for_calibration','get_pixel_position'
           ,'get_pixelTiming_timval','get_mirror_area']

_path = os.path.dirname(__file__)
lib = np.ctypeslib.load_library('pyhessio', _path)

lib.get_teldata_list.restype = None
lib.close_file.restype = None
lib.get_teldata_list.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int, flags="C_CONTIGUOUS")]
lib.get_num_channel.argtypes = [ctypes.c_int]
lib.get_num_samples.argtypes = [ctypes.c_int]
lib.get_num_types.argtypes = [ctypes.c_int]
lib.get_num_pixels.argtypes = [ctypes.c_int]
lib.get_mirror_area.argtypes = [ctypes.c_int]
lib.get_mirror_area.restype = ctypes.c_double
lib.get_adc_sample.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_uint16, flags="C_CONTIGUOUS")]
lib.get_adc_sum.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int32, flags="C_CONTIGUOUS")]
lib.get_pixelTiming_timval.argtypes = [ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_float, flags="C_CONTIGUOUS")]
lib.get_data_for_calibration.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),\
                              np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
                              
lib.get_pixel_position.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),\
                              np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
lib.move_to_next_event.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int)]
lib.file_open.argtypes = [ctypes.c_char_p]


def move_to_next_event(limit=0):
    """
    Read data form input file
    and fill corresponding container
    Data can be then access with 
    other available functions in
    this module
    By default all events are computed

    Parameters
    ----------
    limit: int,optional
        limit allows to limit the number of event generated
    """
    result = np.zeros(1,dtype=np.int32)
    res = 0
    evt_num = 0
    while  res >= 0 and ( limit == 0 or evt_num < limit): 
        res = lib.move_to_next_event(result)
        if res != -1:
            yield res,result[0]
            evt_num = evt_num + 1

def file_open(filename):
    """
    Open input data file 
    
    Parameters
    ----------
    filename: str
    
    Returns
    --------
    0 in case of success, otherwise -1
    """
    b_filename = filename.encode('utf-8')
    return lib.file_open(b_filename)

def close_file():
    """
    Close opened iobuf 
    """
    lib.close_file()

def get_global_event_count():
    """
    Returns counter for system trigger 
    """
    return lib.get_global_event_count()

def get_run_number():
    """
    Returns run number read in data file
    """
    return lib.get_run_number()

def get_num_telescope():
    """
    Returns number of telescopes in current run.
    """
    return lib.get_num_telescope()

def get_mirror_area(telescopeId):
    """
    Returns total area of individual mirrors corrected
    for inclination [m^2].

    Parameters
    ----------
    telescopeId: int
    """
    return float(lib.get_mirror_area(telescopeId))

def get_teldata_list():
    """
    Returns list of IDs of telescopes with data for current event
    """
    num_teldata= get_num_teldata()
    array = np.zeros(num_teldata,dtype=np.int32)
    lib.get_teldata_list(array)
    return array

def get_num_teldata():
    """
    Returns number of telescopes for which we actually have data
    """
    return lib.get_num_teldata()

def get_num_channel(telescopeId):
    """
    Returns  type of channel used
    HI_GAIN          0     /**< Index to high-gain channels in adc_sum, adc_sample, pedestal, ... */
    LO_GAIN          1     /**< Index to low-gain channels in adc_sum, adc_sample, pedestal, ... */

    Parameters
    ----------
    telescopeId: int
    """
    return lib.get_num_channel(telescopeId)

def get_num_pixels(telescopeId):
    """
    Returns the number of pixels in the camera (as in configuration)

    Parameters
    ----------
    telescopeId: int
    """
    return lib.get_num_pixels(telescopeId)

def get_num_types(telescopeId):
    """
    Returns how many different types of times can we store

    Parameters
    ----------
    telescopeId: int
    """
    return lib.get_num_types(telescopeId)

def get_num_samples(telescopeId):
    """
    Returns  the number of samples (time slices) recorded

    Parameters
    ----------
    telescopeId: int
    """
    return lib.get_num_samples(telescopeId)


def get_adc_sample(telescopeId,channel):
    """
    Returns pulses sampled
   
    Parameters
    ----------
    telescopeId: int
    channel: int (0->HI_GAIN, 1->LOW_GAIN)
    """
    npix = get_num_pixels(telescopeId)
    ntimeslices = get_num_samples(telescopeId)
    data = np.zeros(npix*ntimeslices,dtype=np.uint16)
    lib.get_adc_sample(telescopeId,channel ,data)
    # convert 1D array to 2D array
    d_data = data.reshape(npix,ntimeslices)
    return d_data

def get_adc_sum(telescopeId,channel):
    """
    Returns the sum of ADC values. 
    
    Parameters
    ----------
    telescopeId: int
    channel: int (0->HI_GAIN, 1->LOW_GAIN)
    """
    npix = get_num_pixels(telescopeId)
    data = np.zeros(npix,dtype=np.int32)
    lib.get_adc_sum(telescopeId,channel ,data)

    return data

def get_pixelTiming_timval(telescopeId):
    """
    Returns PixelTiming.timval
    
    Parameters
    ----------
    telescopeId: int
    """
    npix = get_num_pixels(telescopeId)
    ntimes = get_num_types(telescopeId)
    data = np.zeros(npix*ntimes,dtype=np.float32)
    lib.get_pixelTiming_timval(telescopeId,data)
    d_data = data.reshape(npix,ntimes)
    return d_data
  
def get_data_for_calibration(telescopeId):
    """
    Returns pedestal, calibration 2D array
    
    Parameters
    ----------
    telescopeId: int
    """
    npix = get_num_pixels(telescopeId)

    ngain = 2 # LOW and HI Gain
    pedestal = np.zeros(ngain*npix,dtype=np.double)
    calibration = np.zeros(ngain*npix,dtype=np.double)

    lib.get_data_for_calibration(telescopeId,pedestal,calibration)
    d_ped = pedestal.reshape(ngain,npix)
    d_cal = calibration.reshape(ngain,npix)

    return d_ped, d_cal
  
def get_pixel_position(telescopeId):
    """
    Returns pixels position for a telecsope id

    Parameters
    ----------
    telescopeId: int
    """
    npix = get_num_pixels(telescopeId)

    pos_x = np.zeros(npix,dtype=np.double)
    pos_y = np.zeros(npix,dtype=np.double)

    lib.get_pixel_position(telescopeId,pos_x,pos_y)

    return pos_x, pos_y
