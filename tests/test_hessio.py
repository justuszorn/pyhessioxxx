import pytest
import numpy as np

try:
    from hessio import *
except ImportError as err:
    print("the `hessio` python module is required to access MC data: {}"
                 .format(err))
    assert(err)

def test_hessio():
  rc = 0
  run = 0
  tel_id = 47
  channel = 0
  
  assert file_open("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz") == 0 

  evt_num=0
  for run_id, event_id in move_to_next_event(limit = 1):
    print("event_id", event_id)
    assert run_id == 31964
    assert event_id == 408
 

    tel_ids = get_teldata_list()
    res = [38, 47]
    assert set(tel_ids) == set(res)

    nb_pixel =  get_num_pixels(tel_id)
    print(nb_pixel)
    assert nb_pixel == 2048
    data_ch = get_adc_sample(channel = channel , telescopeId = tel_id)
    print(data_ch[10:11])
    assert np.array_equal(data_ch[10:11],[[22,20,21,24,22,19,22,27,22,21,20,22,21,20,19,22,23,20,22,20,20,23,20,20,22]]) == True
    data_ch_sum = get_adc_sum(channel = channel , telescopeId = tel_id)
    print(data_ch_sum[50:51])

    evt_num=evt_num+1
    print("evt_num", evt_num)

  assert()
  """
      nb_sample = get_num_samples(tel_id) 
      
      try: 
        # get trace for pixel args.pix and channel channel
        trace = data_ch[args.pix]
        # sum samples for that trace:
        intensity = trace.sum()
        # And intensity to  intensity_evts list
        intensity_evts.append(intensity)
        # Get pedestal and calibration information
        pedestal, calibration = get_data_for_calibration(args.tel)
        #print(" calibration")
        
        sig = data_ch_sum[args.pix] - pedestal[channel][args.pix]
        npe = sig * calibration[channel][args.pix] * CALIB_SCALE;
        npe_evts.append(npe)
        pos_x,pos_y = get_pixel_position(args.tel)


      except IndexError:
        print("Telescope id", args.tel, "does not have pixel id", args.pix,file=sys.stderr)
        args.plot = False
        break

      evt_num=evt_num+1
    print("pixel pos x=", pos_x[args.pix],"pos y=",pos_y[args.pix])

    if(args.plot):
      import matplotlib.mlab as mlab
      import matplotlib.pyplot as plt

      # example data
      mu = 100 # mean of distribution
      sigma = 15 # standard deviation of distribution

      num_bins = 50
      # the histogram of the data
      n, bins, patches = plt.hist(npe_evts, num_bins, normed=1, facecolor='green', alpha=0.5)
      # add a 'best fit' line
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.xlabel('Smarts')
      plt.ylabel('Probability')
      title = 'ADC sum for telescope ' + str(args.tel)  + ', pixel '+  \
      str(args.pix)+ ', channel ' +   str(args.channel)
      plt.title(title)

      # Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.show()

    print("\n\nDone")
  """
