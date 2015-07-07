import numpy as np
import os
import ctypes
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

_path = os.path.dirname('__file__')
lib = np.ctypeslib.load_library('pyhessio', _path)

lib.get_teldata_list.restype = None
lib.close_file.restype = None
lib.get_teldata_list.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int, flags="C_CONTIGUOUS")]
lib.get_num_channel.argtypes = [ctypes.c_int]
lib.get_num_samples.argtypes = [ctypes.c_int]
lib.get_num_pixels.argtypes = [ctypes.c_int]
lib.get_pixel_data.argtypes = [ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(ctypes.c_int16, flags="C_CONTIGUOUS")]
lib.move_to_next_event.argtypes = [np.ctypeslib.ndpointer(ctypes.c_int)]
lib.file_open.argtypes = [ctypes.c_char_p]


#--------------------------------------
def move_to_next_event():
    """ Read data form input file
        and fill corresponding container
        Data can be then access with 
        other available functions in
        this module
    """
    result = np.zeros(1,dtype=np.int32)
    res = 0
    while  res >= 0: 
      res = lib.move_to_next_event(result)
      yield res,result[0]

    yield res,result[0]

def get_run_number():
    return lib.get_run_number()
#--------------------------------------

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
def get_pixel_data(telescopeId,channel):
  """
   Return pulses sampled
  """
  npix = get_num_pixels(telescopeId)
  ntimeslices = get_num_samples(telescopeId)
  data = np.zeros(npix*ntimeslices,dtype=np.int16)
  lib.get_pixel_data(telescopeId,channel ,data)

  # convert 1D array to 2D array
  d_data = data.reshape(npix,ntimeslices)
  return d_data
