from hessio import *

#---------------- MAIN  ---------------------
if __name__ == '__main__':
  print("---------Main-------------")
  
  rc = 0
  run = 0

  if file_open("/home/jacquem/Downloads/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz") == 0 :

    for rc,event_id in move_to_next_event(): 

      if get_run_number() != run:
        run = get_run_number()
        print("-- number of telescopes in run", get_num_telescope())
        print("--run number:", run)

      tel_ids = get_teldata_list()
      for tel_id in tel_ids:
        print("-> Telescope", tel_id)
        nb_sample = get_num_samples(tel_id) 
        nb_pixel =  get_num_pixels(tel_id)
        data_ch1 = get_pixel_data(channel = 1, telescopeId = tel_id)
        
        # get trace for pixel 10 in channel 1:
        trace = data_ch1[10]
        print("----> trace", trace)
        
        # sum samples 5-10 for that trace:
        intensity = trace[5:10].sum()
        print("----> intensity", intensity)

        # sum samples 5-10 for all pixels at once:
        intensities = data_ch1[:,5:10].sum()
        print("----> intensities", intensities)
