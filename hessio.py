import numpy as np
import os
import ctypes
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

__all__ = ['move_to_next_event','file_open','close_file','get_global_event_count','get_run_number','get_num_telescope','get_teldata_list','get_num_teldata','get_num_channel','get_num_pixels','get_num_samples','printAmp','get_adc_sample','get_adc_sum','get_data_for_calibration','get_pixel_position']

_path = os.path.dirname(__file__)
lib = np.ctypeslib.load_library('pyhessio', _path)

lib.get_teldata_list.restype = None
lib.close_file.restype = None
lib.get_teldata_list.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int, flags="C_CONTIGUOUS")]
lib.get_num_channel.argtypes = [ctypes.c_int]
lib.get_num_samples.argtypes = [ctypes.c_int]
lib.get_num_pixels.argtypes = [ctypes.c_int]
lib.get_adc_sample.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int16, flags="C_CONTIGUOUS")]
lib.get_adc_sum.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int32, flags="C_CONTIGUOUS")]
lib.get_data_for_calibration.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),\
                              np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
                              
lib.get_pixel_position.argtypes=[ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS"),\
                              np.ctypeslib.ndpointer(ctypes.c_double, flags="C_CONTIGUOUS")]
lib.move_to_next_event.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int)]
lib.file_open.argtypes = [ctypes.c_char_p]


#--------------------------------------
def move_to_next_event(limit=0):
    """ Read data form input file
        and fill corresponding container
        Data can be then access with 
        other available functions in
        this module
    """
    result = np.zeros(1,dtype=np.int32)
    res = 0
    evt_num = 0
    while  res >= 0 and ( limit == 0 or evt_num < limit): 
      res = lib.move_to_next_event(result)
      yield res,result[0]
      evt_num = evt_num + 1


#--------------------------------------
def file_open(filename):
  """
  Open input data file 
  """
  b_filename = filename.encode('utf-8')
  return lib.file_open(b_filename)
#--------------------------------------

#--------------------------------------
def close_file():
  """
  Close opened iobuf 
  """
  return lib.close_file()

#--------------------------------------
def get_global_event_count():
    return lib.get_global_event_count()
#--------------------------------------
def get_run_number():
    return lib.get_run_number()
#--------------------------------------
def get_num_telescope():
  """
   Return number of telescopes in run.
  """
  return lib.get_num_telescope()
#--------------------------------------

#--------------------------------------
def get_teldata_list():
  """
   Return list of IDs of telescopes with data
  """
  num_teldata= get_num_teldata()
  array = np.zeros(num_teldata,dtype=np.int32)
  lib.get_teldata_list(array)
  return array
#--------------------------------------

#--------------------------------------
def get_num_teldata():
  """
   Return number of telescopes for which we actually have data
  """
  return lib.get_num_teldata()
#--------------------------------------


#--------------------------------------
def get_num_channel(telescopeId):
  """
   Return  type of channel used
   HI_GAIN          0     /**< Index to high-gain channels in adc_sum, adc_sample, pedestal, ... */
   LO_GAIN          1     /**< Index to low-gain channels in adc_sum, adc_sample, pedestal, ... */
  """
  return lib.get_num_channel(telescopeId)
#--------------------------------------


#--------------------------------------
def get_num_pixels(telescopeId):
  """
   Return the number of pixels in the camera (as in configuration)
  """
  return lib.get_num_pixels(telescopeId)
#--------------------------------------

#--------------------------------------
def get_num_samples(telescopeId):
  """
   Return  the number of samples (time slices) recorded
  """
  return lib.get_num_samples(telescopeId)
#--------------------------------------

#--------------------------------------
def printAmp():
  """
   Return  the number of samples (time slices) recorded
  """
  lib.printAmp()
#--------------------------------------

#--------------------------------------
def get_adc_sample(telescopeId,channel):
  """
   Return pulses sampled
  """
  npix = get_num_pixels(telescopeId)
  ntimeslices = get_num_samples(telescopeId)
  data = np.zeros(npix*ntimeslices,dtype=np.int16)
  lib.get_adc_sample(telescopeId,channel ,data)

  # convert 1D array to 2D array
  d_data = data.reshape(npix,ntimeslices)
  return d_data

#--------------------------------------
def get_adc_sum(telescopeId,channel):
  """
   Return sum of ADC values. 
  """
  npix = get_num_pixels(telescopeId)
  data = np.zeros(npix,dtype=np.int32)
  lib.get_adc_sum(telescopeId,channel ,data)

  return data
#--------------------------------------
def get_data_for_calibration(telescopeId):
  """
   Return pedestal, calibration 2D array
  """
  npix = get_num_pixels(telescopeId)

  ngain = 2 # LOW and HI Gain
  pedestal = np.zeros(ngain*npix,dtype=np.double)
  calibration = np.zeros(ngain*npix,dtype=np.double)

  lib.get_data_for_calibration(telescopeId,pedestal,calibration)
  d_ped = pedestal.reshape(ngain,npix)
  d_cal = calibration.reshape(ngain,npix)


  return d_ped, d_cal
  
  #--------------------------------------
def get_pixel_position(telescopeId):
  """
   Return pixels position for a telecsope id
  """
  npix = get_num_pixels(telescopeId)

  pos_x = np.zeros(npix,dtype=np.double)
  pos_y = np.zeros(npix,dtype=np.double)

  lib.get_pixel_position(telescopeId,pos_x,pos_y)

  return pos_x, pos_y
