import numpy as np
import os
import ctypes

__all__ = ['move_to_next_event','file_open','close_file',
           'get_global_event_count','get_run_number',
           'get_num_telescope','get_telescope_with_data_list',
           'get_teldata_list',
           'get_num_teldata','get_num_channel','get_num_pixels',
           'get_num_samples','get_adc_sample','get_adc_sum',
           'get_data_for_calibration','get_pixel_position',
           'get_pixel_timing_timval','get_mirror_area',
           'get_num_types',
           'get_pixel_timing_threshold','get_pixel_timing_peak_global',
           'HessioTelescopeIndexError','HessioGeneralError']

_path = os.path.dirname(__file__)
lib = np.ctypeslib.load_library('pyhessio', _path)

lib.close_file.restype = None
lib.file_open.argtypes = [ctypes.c_char_p]
lib.file_open.restype=ctypes.c_int
lib.get_adc_sample.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_uint16, flags="C_CONTIGUOUS")]
lib.get_adc_sample.restype = ctypes.c_int
lib.get_adc_sum.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int32, flags="C_CONTIGUOUS")]
lib.get_adc_sum.restype = ctypes.c_int
lib.get_data_for_calibration.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),
                                        np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
lib.get_data_for_calibration.restype=ctypes.c_int
lib.get_global_event_count.restype = ctypes.c_int
lib.get_mirror_area.argtypes = [ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
lib.get_mirror_area.restype = ctypes.c_int
lib.get_num_channel.argtypes = [ctypes.c_int]
lib.get_num_channel.restype = ctypes.c_int
lib.get_num_pixels.argtypes = [ctypes.c_int]
lib.get_num_pixels.restype = ctypes.c_int
lib.get_num_samples.argtypes = [ctypes.c_int]
lib.get_num_samples.restype = ctypes.c_int
lib.get_num_teldata.restype = ctypes.c_int
lib.get_num_telescope.restype = ctypes.c_int
lib.get_num_types.argtypes = [ctypes.c_int]
lib.get_num_types.restype = ctypes.c_int
lib.get_pixel_position.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),
                                  np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
lib.get_pixel_position.restype=ctypes.c_int
lib.get_pixel_timing_peak_global.argtypes = [ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_float, flags="C_CONTIGUOUS")]
lib.get_pixel_timing_peak_global.restype = ctypes.c_int
lib.get_pixel_timing_threshold.argtypes = [ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int, flags="C_CONTIGUOUS")]
lib.get_pixel_timing_threshold.restype = ctypes.c_int
lib.get_pixel_timing_timval.argtypes = [ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_float, flags="C_CONTIGUOUS")]
lib.get_pixel_timing_timval.restype=ctypes.c_int
lib.get_run_number.restype = ctypes.c_int
lib.get_telescope_with_data_list.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int, flags="C_CONTIGUOUS")]
lib.get_telescope_with_data_list.restype = ctypes.c_int
lib.move_to_next_event.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int)]
lib.move_to_next_event.restype = ctypes.c_int

TEL_INDEX_NOT_VALID  =-2

class HessioGeneralError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class HessioTelescopeIndexError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


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
    Returns
    -------
    counter for system trigger 
    """
    return lib.get_global_event_count()

def get_run_number():
    """
    Returns
    -------
    run number read in data file
    or -1 if not available
    
    Raises
    ------
    HessioGeneralError
    If hsdata->run_header.run is not available
    """
    run =  lib.get_run_number()
    if run > 0 : return run
    else:
        raise(HessioGeneralError("run number not available"))
        

def get_num_telescope():
    """
    Returns
    -------
    number of telescopes in current run.

    Raises
    ------
    HessioGeneralError
    If hsdata->event.num_tel is not available
    """
    number =  lib.get_num_telescope()
    if number > 0 : return number
    else:
        raise(HessioGeneralError("number of telescopes in current run not available"))

def get_mirror_area(telescope_id):
    """
    Returns
    -------
    total area of individual mirrors corrected
    for inclination [m^2].

    Parameters
    ----------
    telescope_id: int
    
    Raises
    ------
    HessioGeneralError
    if hsdata->camera_set[itel].mirror_area not available

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    
    data = np.zeros(1,dtype=np.double)
    result = lib.get_mirror_area(telescope_id,data)
    if result == 0:
        return data[0]
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    raise(HessioGeneralError("hsdata->camera_set[itel].mirror_area not available"))

def get_telescope_with_data_list():
    """
    Returns
    -------
    list of telescope with data for current event

    Raises
    ------
    HessioGeneralError
    if information is not available
    """

    try: 
        return get_teldata_list()
    except:
        raise(HessioGeneralError("hsdata->event.teldata_list is not available"))
        

def get_teldata_list():
    """
    Returns
    -------
    list of IDs of telescopes with data for current event

    Raises
    ------
    HessioGeneralError
    if information is not available
    """
    num_teldata= get_num_teldata()
    if num_teldata >= 0:
        array = np.zeros(num_teldata,dtype=np.int32)
        lib.get_telescope_with_data_list(array)
        return array
    else:
        raise(HessioGeneralError("hsdata->event.num_teldata is not available"))


def get_num_teldata():
    """
    Returns
    -------
    number of telescopes for which we actually have data
    
    Raises
    ------
    HessioGeneralError
        If hsdata->event.num_teldata is not available
    """
      
    number =  lib.get_num_teldata()
    if number > 0:
        return number
    else:
        raise(HessioGeneralError("hsdata->event.num_teldata is not available"))

def get_num_channel(telescope_id):
    """
    Returns
    -------
    type of channel used
    HI_GAIN          0     /**< Index to high-gain channels in adc_sum, adc_sample, pedestal, ... */
    LO_GAIN          1     /**< Index to low-gain channels in adc_sum, adc_sample, pedestal, ... */

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
        If hsdata->event.teldata[itel].raw
    HessioTelescopeIndexError 
        if no telescope exist with this id
    """
    result =  lib.get_num_channel(telescope_id)
    print("result",result)
    if result >= 0: return result
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError(" hsdata->event.teldata[itel].raw not available"))
        

def get_num_pixels(telescope_id):
    """
    Returns
    -------
    the number of pixels in the camera (as in configuration)

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
        If  hsdata->camera_set[itel].num_pixels

    HessioTelescopeIndexError
        if no telescope exist with this id
    """
    result = lib.get_num_pixels(telescope_id)
    if result >= 0 : return result
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("hsdata->camera_set[itel].num_pixels not available"))
        

def get_pixel_timing_threshold(telescope_id):
    """
    Returns
    -------
    PixelTiming threshold:
    - Minimum base-to-peak raw amplitude difference applied in pixel selection

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
        If hsdata->event.teldata[itel].pixtm
    HessioTelescopeIndexError
        if no telescope exist with this id
    """
    threshold = np.zeros(1,dtype=np.int32)
    result = lib.get_pixel_timing_threshold(telescope_id,threshold)
    if result == 0: return threshold[0]
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("hsdata->event.teldata[itel].pixtm not available"))
       

def get_pixel_timing_peak_global(telescope_id):
    
    """
    Returns 
    -------
    PixelTiming peak_global:
     - Camera-wide (mean) peak position [time slices]

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    If hsdata->event.teldata[itel].pixtm; not available

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    
    peak = np.zeros(1,dtype=np.float32)
    result = lib.get_pixel_timing_peak_global(telescope_id,peak)
    if result == 0: return peak[0]
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("hsdata->event.teldata[itel].pixtm; not available"))
        

def get_num_types(telescope_id):
    """
    Returns
    -------
    how many different types of times can we store

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    If hsdata->event.teldata[itel].pixtm->num_types not available

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    result = lib.get_num_types(telescope_id)
    if result >= 0: return result
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("hsdata->event.teldata[itel].pixtm->num_types  not available"))

def get_num_samples(telescope_id):
    """
    Returns  
    -------
    the number of samples (time slices) recorded

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    data->event.teldata[itel].raw->num->samples not available

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    result = lib.get_num_samples(telescope_id)
    if result >= 0: return result
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("ata->event.teldata[itel].raw->num->samples not available"))
        
        


def get_adc_sample(telescope_id,channel):
    """
    Returns
    ------- 
    pulses sampled
   
    Parameters
    ----------
    telescope_id: int
    channel: int (0->HI_GAIN, 1->LOW_GAIN)

    Raises
    ------
    HessioGeneralError
    If information is not available

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    npix = get_num_pixels(telescope_id)
    ntimeslices = get_num_samples(telescope_id)
    data = np.zeros(npix*ntimeslices,dtype=np.uint16)
    result = lib.get_adc_sample(telescope_id,channel ,data)
    if result >= 0:
        # convert 1D array to 2D array
        d_data = data.reshape(npix,ntimeslices)
        return d_data
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("adc sample not available for telescope "+
                               str(telescope_id) +
                               " and channel " + str(channel)))

def get_adc_sum(telescope_id,channel):
    """
    Returns 
    -------
    the sum of ADC values. 
    
    Parameters
    ----------
    telescope_id: int
    channel: int (0->HI_GAIN, 1->LOW_GAIN)

    Raises
    ------
    HessioGeneralError
    If No adc_sum for telescope 

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    npix = get_num_pixels(telescope_id)
    data = np.zeros(npix,dtype=np.int32)
    result = lib.get_adc_sum(telescope_id,channel ,data) 
    if result == 0:
        return data
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("No adc_sum for telescope "+ str(telescope_id)))
        

def get_pixel_timing_timval(telescope_id):
    """
    Returns 
    -------
    PixelTiming.timval
    
    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    if hsdata->event.teldata[itel]->timval[ipix][itimes] not available

    HessioTelescopeIndexError
    if no telescope exist with this id
            
    """
    npix = get_num_pixels(telescope_id)
    ntimes = get_num_types(telescope_id)
    data = np.zeros(npix*ntimes,dtype=np.float32)
    result = lib.get_pixel_timing_timval(telescope_id,data)
    if result == 0:
        d_data = data.reshape(npix,ntimes)
        return d_data
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("no pixel timing timval for telescope "
                              + str(telescope_id)))
        
  
def get_data_for_calibration(telescope_id):
    """
    Returns
    ------- 
    pedestal, calibration 2D array
    
    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    if data not available for this telescope

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    npix = get_num_pixels(telescope_id)

    ngain = 2 # LOW and HI Gain
    pedestal = np.zeros(ngain*npix,dtype=np.double)
    calibration = np.zeros(ngain*npix,dtype=np.double)

    result = lib.get_data_for_calibration(telescope_id,pedestal,calibration)
    if result == 0:
        d_ped = pedestal.reshape(ngain,npix)
        d_cal = calibration.reshape(ngain,npix)
        return d_ped, d_cal
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("no calibration data for telescope "
                              + str(telescope_id)))

  
def get_pixel_position(telescope_id):
    """
    Returns
    ------- 
    pixels position for a telecsope id

    Parameters
    ----------
    telescope_id: int

    Raises
    ------
    HessioGeneralError
    if pixel position not available for this telescope

    HessioTelescopeIndexError
    if no telescope exist with this id
    """
    npix = get_num_pixels(telescope_id)

    pos_x = np.zeros(npix,dtype=np.double)
    pos_y = np.zeros(npix,dtype=np.double)

    result = lib.get_pixel_position(telescope_id,pos_x,pos_y)
    if result == 0:
        return pos_x, pos_y
    elif result == TEL_INDEX_NOT_VALID:
        raise(HessioTelescopeIndexError("no telescope wth id " + str(telescope_id))) 
    else:
        raise(HessioGeneralError("no pixel position for telescope "
                              + str(telescope_id)))
