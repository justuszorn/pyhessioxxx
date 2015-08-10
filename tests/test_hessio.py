import pytest
import numpy as np

try:
    from hessio import *
except ImportError as err:
    print("the `hessio` python module is required to access MC data: {}"
                 .format(err))
    assert(err)

def test_hessio():
  tel_id = 47
  channel = 0
  
  assert file_open("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz") == 0 

  evt_num=0
  for run_id, event_id in move_to_next_event(limit = 1):
    assert run_id == 31964
    assert event_id == 408

    assert set(get_teldata_list()) == set([38, 47])
    assert  get_num_pixels(tel_id)== 2048

    data_ch = get_adc_sample(channel = channel , telescopeId = tel_id)
    assert np.array_equal(data_ch[10:11],[[22,20,21,24,22,19,22,27,22,21,20,22,21,20,19,22,23,20,22,20,20,23,20,20,22]]) == True

    data_ch_sum = get_adc_sum(channel = channel , telescopeId = tel_id)
    assert  np.array_equal(data_ch_sum[0:10], [451, 550,505,465,519,467,505,496,501,478]) == True

    nb_sample = get_num_samples(tel_id) 
    assert nb_sample == 25
      
    pedestal, calibration = get_data_for_calibration(tel_id)
    assert pedestal[0][0] == 457.36550903320312
    assert calibration[0][2] ==  0.092817604541778564
        
    pos_x,pos_y = get_pixel_position(tel_id)
    assert pos_x[2] == -0.085799999535083771
    assert pos_y[2] == -0.14880000054836273


