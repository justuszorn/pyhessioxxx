from hessio import *
import argparse

#---------------- MAIN  ---------------------
if __name__ == '__main__':


  parser = argparse.ArgumentParser(description='Tel_id, pixel id and number of event to compute.')
  parser.add_argument('-f', dest='filename', required=True, help='simetelarray data file name')
  parser.add_argument('--tel', type=int, required=True, help='telescope id')
  parser.add_argument('--pix', type=int, required=True, help='pixel id')
  parser.add_argument('--limit',type=int,  dest='limit', help='limit number of events to compute')
  parser.add_argument('--plot',  dest='plot', action='store_true',  help='plot the result')


  args = parser.parse_args()

  rc = 0
  run = 0
  limit = 0
  if args.limit : limit = args.limit


  if file_open(args.filename) == 0 :

    evt_num=0
    intensity_evts=list()
    for rc,event_id in move_to_next_event(): 
      print("--< Start Event",evt_num,">--", end="\r")


      if get_run_number() != run:
        run = get_run_number()
        print("-- number of telescopes in run", get_num_telescope())
        print("--run number:", run)

      tel_id = args.tel
      tel_ids = get_teldata_list()
      if not tel_id in tel_ids : continue # no trigger for this telescope during this event

      nb_sample = get_num_samples(tel_id) 
      nb_pixel =  get_num_pixels(tel_id)
      data_ch1 = get_pixel_data(channel = 1, telescopeId = tel_id)
      
      # get trace for pixel 10 in channel 1:
      trace = data_ch1[args.pix]
      
      # sum samples for that trace:
      intensity = trace.sum()

      # sum samples for all pixels at once:
      intensities = data_ch1[:,:].sum()

      intensity_evts.append(intensity)
      evt_num=evt_num+1
      if limit != 0 and evt_num >limit: break


     
    print("DEBUG",args.plot)
    if(args.plot):
      import matplotlib.mlab as mlab
      import matplotlib.pyplot as plt


      # example data
      mu = 100 # mean of distribution
      sigma = 15 # standard deviation of distribution

      num_bins = 50
      # the histogram of the data
      n, bins, patches = plt.hist(intensity_evts, num_bins, normed=1, facecolor='green', alpha=0.5)
      # add a 'best fit' line
      y = mlab.normpdf(bins, mu, sigma)
      plt.plot(bins, y, 'r--')
      plt.xlabel('Smarts')
      plt.ylabel('Probability')
      title = 'ADC sum for telescope ' + str(args.tel)  + ', pixel '+ str(args.pix)
      plt.title(title)

      # Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      plt.show()

    print("\n\nDone")

