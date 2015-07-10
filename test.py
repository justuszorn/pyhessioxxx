from hessio import *
import argparse
import sys

CALIB_SCALE = 0.98

#---------------- MAIN  ---------------------
if __name__ == '__main__':


  # Declare and parse command line option
  parser = argparse.ArgumentParser(description='Tel_id, pixel id and number of event to compute.')
  parser.add_argument('-f', dest='filename', required=True, help='simetelarray data file name')
  parser.add_argument('--tel', type=int, required=True, help='telescope id')
  parser.add_argument('--pix', type=int, required=True, help='pixel id')
  parser.add_argument('--channel', type=int, required=False, help='channel 0/1 (gain)')
  parser.add_argument('--limit',type=int,  dest='limit', help='limit number of events to compute')
  parser.add_argument('--plot',  dest='plot', action='store_true',  help='plot the result')
  args = parser.parse_args()

  rc = 0
  run = 0
  limit = 0
  if args.limit : limit = args.limit
  channel = 1
  if args.channel != None:
    channel = args.channel

  if file_open(args.filename) == 0 :


    evt_num=0
    intensity_evts=list()
    npe_evts=list()
    for rc,event_id in move_to_next_event(limit=limit): 
      print("--< Start Event",evt_num,">--",end="\r")

      tel_id = args.tel
      tel_ids = get_teldata_list()
      if not tel_id in tel_ids :
        evt_num=evt_num+1
        continue # no trigger for this telescope during this event

      nb_sample = get_num_samples(tel_id) 
      nb_pixel =  get_num_pixels(tel_id)
      data_ch = get_adc_sample(channel = channel , telescopeId = tel_id)
      data_ch_sum = get_adc_sum(channel = channel , telescopeId = tel_id)
      
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

