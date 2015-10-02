import pytest
import numpy as np
from hessio import HessioChannelIndexError

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
    v get_telescope_with_data_list
    v get_pixel_timing_timval(telescope_id)
    v get_mirror_area(telescope_id)
    v get_pixel_timing_num_times_types(telescope_id)
    v get_pixel_timing_threshold(telescope_id)
    v get_pixel_timing_peak_global(telescope_id)
    """
    tel_id = 47
    channel = 0
    
    # test exception by usging getter before read the first event 
    try: 
        print("DEBUG", get_num_pixels(1))
        assert()
    except HessioGeneralError: pass 
  
    # test reading file
    assert file_open("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz") == 0 

    #for run_id, event_id in move_to_next_event(limit = 1):
        
    run_id, event_id = next(move_to_next_event())

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
    try:
        get_num_pixels(4000)
        assert()
    except HessioTelescopeIndexError: pass
    
    #get_adc_sample
    data_ch = get_adc_sample(tel_id, channel)
    assert np.array_equal(data_ch[10:11],[[22,20,21,24,22,19,22,27,22,21,20,22,21,20,19,22,23,20,22,20,20,23,20,20,22]]) == True
    
    try:
        get_adc_sample(-1, 0)
        assert()
    except HessioTelescopeIndexError: pass
    
    try:
        data_ch = get_adc_sample(47, 5)
        assert()
    except HessioChannelIndexError: pass 
    
    #get_adc_sum
    data_ch_sum = get_adc_sum(tel_id,channel)
    assert  np.array_equal(data_ch_sum[0:10], [451, 550,505,465,519,467,505,496,501,478]) == True
    
    try:
        data_ch_sum = get_adc_sum(-1,channel)
        assert()
    except HessioTelescopeIndexError: pass

    try:
        data_ch_sum = get_adc_sum(47,2)
        assert()
    except HessioChannelIndexError: pass
    
    
    
    #get_num_sampple
    nb_sample = get_num_samples(tel_id) 
    assert nb_sample == 25
    try: 
        get_num_samples(70000) 
        assert()
    except HessioTelescopeIndexError:pass
        
        
    #get_data_for_calibration 
    pedestal, calibration = get_data_for_calibration(tel_id)
    assert pedestal[0][0] == 457.36550903320312
    assert calibration[0][2] ==  0.092817604541778564
    try :
        get_data_for_calibration(0)
        assert()
    except HessioTelescopeIndexError: pass
        
    #get_pixel_position
    pos_x,pos_y = get_pixel_position(tel_id)
    assert pos_x[2] == -0.085799999535083771
    assert pos_y[2] == -0.14880000054836273
    try: 
        get_pixel_position(0)
        assert()
    except HessioTelescopeIndexError: pass
        
        
        
    
    assert(np.array_equal(get_telescope_with_data_list() , [38, 47]) == True)

    #get_mirror_area
    assert(get_mirror_area(tel_id) ==  14.562566757202148)
    try:
        get_mirror_area(-1)
        assert()
    except HessioTelescopeIndexError: pass
    
    # get_pixel_timing_num_times_types
    assert(get_pixel_timing_num_times_types(tel_id) == 7)
    try:
        get_pixel_timing_num_times_types(4000)
        assert()
    except HessioTelescopeIndexError: pass
    assert(get_pixel_timing_num_times_types(1) == 0)

    
    #get_pixel_threashold
    assert(get_pixel_timing_threshold(tel_id)== -6)
    try:
        get_pixel_timing_threshold(-1)
        assert()
    except  HessioTelescopeIndexError: pass
    
    #get_pixel_timing_peak_global
    assert(float(get_pixel_timing_peak_global(tel_id)) == float(9.740449905395508))
    try:
        get_pixel_timing_peak_global(1000)
        assert()
    except HessioTelescopeIndexError: pass

    assert(float(get_pixel_timing_timval(tel_id)[8][0]) ==  float(11.069999694824219) )
    try:
        get_pixel_timing_timval(-1)
        assert()
    except HessioTelescopeIndexError: pass


       
    """
    xcode 1129.6055908203125
    ycode 547.77001953125
    shower energy 0.3820943236351013
    shower azimuth 6.283185005187988
    shower altitude 1.2217304706573486
    teltrig_list [38 47]
    get_adc_knows(38,0,1000) 1
    get_ref_shape(38,0,2) 0.0269622802734375
    get_ref_step(38) 0.3003003001213074
    get_time_slice(38) 3.0030031204223633
    tel_event gps seconds 0 nanoseconds 0
    central_event_gps_time 1319627141 nanoseconds 1275579058
    num tel trig 2
    teltrig_list [38 47]

    """
        
        
    assert(float(get_mc_event_xcore()) == float(1129.6055908203125))
    assert(float(get_mc_event_ycore()) == float(547.77001953125))
    assert(float(get_mc_shower_energy()) == float(.3820943236351013))
    assert(float(get_mc_shower_azimuth()) == float(6.283185005187988))
    assert(float(get_mc_shower_altitude()) == float( 1.2217304706573486))
    
    assert(get_adc_known(38,0,1000)== 1 )

    assert(float(get_ref_shape(38,0,2)) == float(.0269622802734375))
    assert(float(get_ref_step(38)) == float(.3003003001213074))
    assert(float(get_time_slice(38))== float(3.0030031204223633))

    seconds, nanoseconds = get_tel_event_gps_time(38)
    assert(seconds == 0)
    assert(nanoseconds == 0)
    
    seconds, nanoseconds = get_central_event_gps_time()
    assert(seconds == 1319627141)
    assert(nanoseconds == 1275579058)

    num_tel_trig = get_num_tel_trig()
    assert(num_tel_trig == 2 )
    
    assert(np.array_equal(get_central_event_teltrg_list() ,[38, 47]) == True)

    close_file()
    
        
if __name__ == "__main__":
    test_hessio()
