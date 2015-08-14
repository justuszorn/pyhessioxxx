import pytest
import numpy as np

try:
    from hessio import *
except ImportError as err:
    print("the `hessio` python module is required to access MC data: {}"
                 .format(err))
    assert(err)

def test_hessio():
    """
    v move_to_next_event(limit=0):
    v file_open(filename):
    close_file():
    v get_global_event_count():
    v get_run_number():
    v get_num_telescope():
    v get_teldata_list():
    v get_num_teldata():
    v get_num_channel(telescope_id):
    v get_num_pixels(telescope_id):
    v get_num_samples(telescope_id):
    v get_adc_sample(telescope_id,channel):
    v get_adc_sum(telescope_id,channel):
    v get_data_for_calibration(telescope_id):
    v get_pixel_position(telescope_id):
    
    get_telescope_with_data_list
    get_pixel_timing_timval(telescope_id)
    get_mirror_area(telescope_id)
    get_num_types(telescope_id)
    get_pixel_timing_threshold(telescope_id)
    get_pixel_timing_peak_global(telescope_id)
    """
    tel_id = 47
    channel = 0
  
    assert file_open("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz") == 0 

    evt_num=0
    for run_id, event_id in move_to_next_event(limit = 1):
        assert run_id == 31964
        assert event_id == 408
    
        assert get_run_number() == 31964
        assert get_global_event_count() == 408
        assert get_num_telescope() == 126
        assert get_num_teldata() == 2
        
        #get_num_channel
        assert get_num_channel(tel_id) == 1
        
        try: 
            get_num_channel(-1)
            assert()
        except HessioTelescopeIndexError: pass
        try: 
            get_num_channel(1)
            assert()
        except HessioGeneralError: pass
    
        assert set(get_teldata_list()) == set([38, 47])

        #get_num_pixels
        assert get_num_pixels(tel_id)== 2048

        data_ch = get_adc_sample(tel_id, channel)
        assert np.array_equal(data_ch[10:11],[[22,20,21,24,22,19,22,27,22,21,20,22,21,20,19,22,23,20,22,20,20,23,20,20,22]]) == True
    
        data_ch_sum = get_adc_sum(tel_id,channel)
        assert  np.array_equal(data_ch_sum[0:10], [451, 550,505,465,519,467,505,496,501,478]) == True
    
        nb_sample = get_num_samples(tel_id) 
        assert nb_sample == 25
          
        pedestal, calibration = get_data_for_calibration(tel_id)
        assert pedestal[0][0] == 457.36550903320312
        assert calibration[0][2] ==  0.092817604541778564
            
        pos_x,pos_y = get_pixel_position(tel_id)
        assert pos_x[2] == -0.085799999535083771
        assert pos_y[2] == -0.14880000054836273
        
        assert(np.array_equal(get_telescope_with_data_list() , [38, 47]) == True)
        assert(get_mirror_area(tel_id) ==  14.562566757202148)
        assert(get_num_types(tel_id) == 7)
        
        assert(get_pixel_timing_threshold(tel_id)== -6)
        assert(float(get_pixel_timing_peak_global(tel_id)) == float(9.740449905395508))
    
        timval = get_pixel_timing_timval(tel_id)[8][0]
        verif = 11.069999694824219
        assert(float(timval) ==  float(verif) )
        close_file()