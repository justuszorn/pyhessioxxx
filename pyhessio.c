/** @file pyhessio.c
 *  @short A wrapper program reading H.E.S.S. data with python
 *
 * Suggestions/complains to jacquem@lapp.in2p3.fr
 *
 */
#include "initial.h"      
#include "io_basic.h"  
#include "io_hess.h"
#include "fileopen.h"
#include "stdio.h"


void close_file(void);
int  file_open(const char* filename);
int  fill_hsdata(int* event_id);
int  get_adc_sample(int telescopeId, int channel, uint16_t *data );
int  get_adc_sum(int telescopeId, int channel, uint32_t *data );
int  get_data_for_calibration(int telescopeId,double* pedestal,double* calib);
int  get_global_event_count(void);
int  get_mirror_area(int telescopeId,double* mirror_area);
int  get_num_channel(int telescopeId);
int  get_num_pixels(int telescopeId);
int  get_num_samples(int telescopeId);
int  get_num_teldata(void);
int  get_num_telescope(void);
int  get_num_types(int telescopeId);
int  get_pixel_position(int telescopeId, double* xpos, double* ypos );
int  get_pixel_timing_threshold(int telescopeId, int* result);
int  get_pixel_timing_timval(int telescopeId,float *data);
int  get_pixel_timing_peak_global(int telescopeId, float* peak);
int  get_run_number(void);
int  get_telescope_with_data_list(int* list);
int  get_telescope_index(int telescopeId);
int  move_to_next_event(int *event_id);


static AllHessData *hsdata = NULL;
static IO_ITEM_HEADER item_header;
static IO_BUFFER *iobuf = NULL;
static int file_is_opened = 0;
#define TEL_INDEX_NOT_VALID -2

//-----------------------------------
// Return array index for specific id
//-----------------------------------

int get_telescope_index(int telescopeId)
{
	int itel=0;
    for (itel=0; itel<hsdata->run_header.ntel; itel++)
    {
    	 if ((hsdata)->run_header.tel_id[itel] == telescopeId) return itel;
    }
    return TEL_INDEX_NOT_VALID;
}

//----------------------------------
//Read input file and fill hsdata
// and item_header global var 
//----------------------------------
int file_open(const char* filename)
{
  if (filename)
  {
    if (file_is_opened) { close_file(); }

    /* Check assumed limits with the ones compiled into the library. */
    H_CHECK_MAX();
   
    if ( (iobuf = allocate_io_buffer(1000000L)) == NULL )
    {
      Error("Cannot allocate I/O buffer");
      exit(1);
    }
    iobuf->max_length = 100000000L;

    if ( (iobuf->input_file = fileopen(filename,READ_BINARY)) == NULL )
    {
      perror(filename);
      Error("Cannot open input file.");
      return -1 ;
    }

    fflush(stdout);
    fprintf(stderr,"%s\n",filename);
    printf("\nInput file '%s' has been opened.\n",filename);
    file_is_opened = 1;
  }
  return 0;
}

//----------------------------------
//Read input file and fill hsdata
// and item_header global var 
//----------------------------------
int move_to_next_event(int *event_id)
{
  
  if (! file_is_opened) return -1;

  int rc = 0;
  while(   rc != IO_TYPE_HESS_EVENT )
  {
    rc = fill_hsdata( event_id);
    if (rc < 0) 
    {
       close_file(); 
       return -1; 
    }  
  }
 return  get_run_number();
}

/*--------------------------------*/
//  Cleanly close iobuf
//----------------------------------
void close_file()
{

  if ( iobuf->input_file != NULL && iobuf->input_file != stdin )
  {
    fileclose(iobuf->input_file);
    iobuf->input_file = NULL;
    reset_io_block(iobuf);
  }
  if (iobuf->output_file != NULL) fileclose(iobuf->output_file);
}



//------------------------------------------
//  return run number from last readed event
//------------------------------------------
int get_run_number(void)
{
  if ( hsdata != NULL)
  {
    return hsdata->run_header.run;
  }
  return -1;
}

//------------------------------------
// Return number of telescopes in run.
//------------------------------------
int get_num_telescope(void)
{
  if ( hsdata != NULL)
  {
    return hsdata->event.num_tel;
  }
  return -1;
}

//------------------------------------------------------------
// Return number of telescopes for which we actually have data
//------------------------------------------------------------
int get_num_teldata(void)
{
  if ( hsdata != NULL)
  {
    return hsdata->event.num_teldata;
  }
  return -1;
}
//-------------------------------------------
// Return list of IDs of telescopes with data
//-------------------------------------------
int get_telescope_with_data_list(int* list)
{
  if ( hsdata != NULL)
  {
    int num_teldata = get_num_teldata();
    int loop = 0;
    for ( loop = 0; loop < num_teldata ; loop++)
    {
      *list++ =hsdata->event.teldata_list[loop];
    }
    return 0;
  }
  return -1;
}

//-------------------------------------------
// Return  Global event count
//-------------------------------------------
int get_global_event_count(void)
{
  if ( hsdata != NULL)
  {
	  	 return hsdata->event.central.glob_count;
  }
  return -1;
}


//----------------------------------------------------------------
// Return he number of different gains per pixel for a telscope id
//----------------------------------------------------------------
int get_num_channel(int telescopeId)
{

  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
	if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    AdcData* raw = hsdata->event.teldata[itel].raw;
    if ( raw != NULL && raw->known  )
    {
      return raw->num_gains;
    }
  }
  return -1;
}

//-------------------------------------------
// Return  PixelTiming.timval[H_MAX_PIX][H_MAX_PIX_TIMES]
//-------------------------------------------
int get_pixel_timing_timval(int telescopeId,float *data)
{
  if ( hsdata != NULL)
  {
    int itel = get_telescope_index(telescopeId);
	if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    PixelTiming* pt = hsdata->event.teldata[itel].pixtm;
	if ( pt != NULL )
	{
	//   float timval[H_MAX_PIX][H_MAX_PIX_TIMES]
	  int ipix= 0;
	  for (ipix = 0; ipix < pt->num_pixels; ipix++)
	  {
	    int itimes = 0;
	    for (itimes = 0; itimes < pt->num_types && itimes<H_MAX_PIX_TIMES  ; itimes++)
	    {
	    	*data++ = pt->timval[ipix][itimes];
	    }
	  } // end for ipix
	} // end if pt != NULL
	return 0;
  } // end if hsdata
  return -1;
}
//----------------------------------------------------------------
int get_adc_sample(int telescopeId, int channel, uint16_t *data )
//----------------------------------------------------------------
// Return Pulses sampled
{
  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
	if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
 	AdcData* raw = hsdata->event.teldata[itel].raw;
    if ( raw != NULL && raw->known  ) // If triggered telescopes
    {
      int ipix =0.;
      for(ipix=0.;ipix<raw->num_pixels;ipix++) //  loop over pixels
      {
        if(raw->significant[ipix])
        {
          int isamp=0.;
          for (isamp=0.;isamp<raw->num_samples;isamp++)
            { *data++ = raw->adc_sample[channel][ipix][isamp]; }
        } // end if raw->significant[ipix]
      }  // end of  loop over pixels
    } // end if triggered telescopes
    return 0;
  }
  return -1;
}

//----------------------------------------------------------------
int get_adc_sum(int telescopeId, int channel, uint32_t *data )
//----------------------------------------------------------------
{
  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
	if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
 	AdcData* raw = hsdata->event.teldata[itel].raw;
    if ( raw != NULL && raw->known  ) // If triggered telescopes
    {
      int ipix =0.;
      for(ipix=0.;ipix<raw->num_pixels;ipix++) //  loop over pixels
      {
        *data++ = raw->adc_sum[channel][ipix];
      }  // end of  loop over pixels
      return 0;
    } // end if triggered telescopes
  }
  return -1;
}
//----------------------------------------------------------------
// Return needed informations for calibration process
//   double pedestal[H_MAX_GAINS][H_MAX_PIX];  ///< Average pedestal on ADC sums
//   double calib[H_MAX_GAINS][H_MAX_PIX]; /**< ADC to laser/LED p.e. conversion,
//
int get_data_for_calibration(int telescopeId, double* pedestal, double* calib )
//----------------------------------------------------------------
{
  if ( hsdata != NULL)
  {
	  int itel = get_telescope_index(telescopeId);
	  if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
 	  TelMoniData monitor= hsdata->tel_moni[itel];
 	  LasCalData  calibration = hsdata->tel_lascal[itel];
      int ipix =0.;
      int num_pixels = hsdata->camera_set[itel].num_pixels;
      for(ipix=0.;ipix<num_pixels;ipix++) //  loop over pixels
      {
        int igain=0, num_gain=2; // LOW and HI Gain
        for(igain=0;igain<num_gain;igain++)
        {
        	*pedestal++=monitor.pedestal[igain][ipix];
        	*calib++=calibration.calib[igain][ipix];
        } // end loop gain
      }  // end of  loop over pixels
      return 0;
  }
  return -1;
}
//----------------------------------------------------------------
//----------------------------------------------------------------
// Return pixel position information
// -1 if hsdata == NULL
//
int get_pixel_position(int telescopeId, double* xpos, double* ypos )
{
  if ( hsdata != NULL)
  {
	  int itel = get_telescope_index(telescopeId);
	  if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
      int ipix =0.;
      int num_pixels = hsdata->camera_set[itel].num_pixels;
      for(ipix=0.;ipix<num_pixels;ipix++) //  loop over pixels
      {
    	  *xpos++=hsdata->camera_set[itel].xpix[ipix];
    	  *ypos++=hsdata->camera_set[itel].ypix[ipix];
      }
      return 0;
  }
  return -1;
}
//----------------------------------------------------------------
// Return the number of pixels in the camera (as in configuration)
//----------------------------------------------------------------
int get_num_pixels(int telescopeId)
{
  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
	return hsdata->camera_set[itel].num_pixels;
  }
  return -1;
}

//----------------------------------------------------------------
// Return total area of individual mirrors corrected  for inclination [m^2].
//----------------------------------------------------------------
int get_mirror_area(int telescopeId,double* result)
{
  if ( hsdata != NULL && result != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
	*result = hsdata->camera_set[itel].mirror_area;
	return 0;
  }
  return -1.;
}
//-----------------------------------------------------
// Return the number of samples (time slices) recorded
//-----------------------------------------------------
int get_num_samples(int telescopeId)
{
  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    AdcData* raw = hsdata->event.teldata[itel].raw;
    if ( raw != NULL )//&& raw->known  )
    {
      return raw->num_samples;
    }
  }
  return -1;
}
//-----------------------------------------------------
// Return the number of different types of times can we store
//-----------------------------------------------------
int get_num_types(int telescopeId)
{
  if ( hsdata != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    PixelTiming* pt = hsdata->event.teldata[itel].pixtm;
    if ( pt != NULL )
    {
      return pt->num_types;
    }
  }
  return -1;
}
//---------------------------------------------
// Return PixelTiming threshold:
//  - Minimum base-to-peak raw amplitude difference applied in pixel selection
//-----------------------------------------------------
int get_pixel_timing_threshold(int telescopeId,int *result)
{
  if ( hsdata != NULL && result != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    PixelTiming* pt = hsdata->event.teldata[itel].pixtm;
    if ( pt != NULL ) *result  = pt->threshold;
    return 0;
  }
  return -1;
}
//---------------------------------------------
// Return PixelTiming peak_global:
//   Camera-wide (mean) peak position [time slices]
//-----------------------------------------------------
int get_pixel_timing_peak_global(int telescopeId,float *result)
{
  if ( hsdata != NULL && result != NULL)
  {
	int itel = get_telescope_index(telescopeId);
    if (itel == TEL_INDEX_NOT_VALID) return TEL_INDEX_NOT_VALID;
    PixelTiming* pt = hsdata->event.teldata[itel].pixtm;
    if ( pt != NULL )
    {
      *result =  pt->peak_global;
    }
    return 0;
  }
  return -1;
}
//--------------------------------------------------
// fill hsdata global variable by decoding data file
//--------------------------------------------------
 int fill_hsdata(int* event_id)//,int *header_readed)
 {
  
  int itel;
  int rc = 0;
  int ignore = 0;

  int tel_id;

  /* Find and read the next block of data. */
  /* In case of problems with the data, just give up. */
  if ( find_io_block(iobuf,&item_header) != 0 )
   {
    return -1;
   }
  if ( read_io_block(iobuf,&item_header) != 0 )
  {
    return -1;
  }

 // if ( ( !header_readed) && 
  if ( hsdata == NULL &&
       item_header.type > IO_TYPE_HESS_RUNHEADER &&
       item_header.type < IO_TYPE_HESS_RUNHEADER + 200)
    {
      fprintf(stderr,"Trying to read event data before run header.\n");
      fprintf(stderr,"Skipping this data block.\n");
      return -1;

    }
    


  switch ( (int) item_header.type )
    {
      /* =================================================== */
    case IO_TYPE_HESS_RUNHEADER:

     /* Structures might be allocated from previous run */
    if ( hsdata != NULL )
    {
      /* Free memory allocated inside ... */
      for (itel=0; itel<hsdata->run_header.ntel; itel++)
      {
        if ( hsdata->event.teldata[itel].raw != NULL )
        {
         free(hsdata->event.teldata[itel].raw);
          hsdata->event.teldata[itel].raw = NULL;
        }
        if ( hsdata->event.teldata[itel].pixtm != NULL )
        {
          free(hsdata->event.teldata[itel].pixtm);
          hsdata->event.teldata[itel].pixtm = NULL;
        }
        if ( hsdata->event.teldata[itel].img != NULL )
        {
          free(hsdata->event.teldata[itel].img);
          hsdata->event.teldata[itel].img = NULL;
        }
        if ( hsdata->event.teldata[itel].pixcal != NULL )
        {
          free(hsdata->event.teldata[itel].pixcal);
          hsdata->event.teldata[itel].pixcal = NULL;
        }
      }
      /* Free main structure */
      free(hsdata);
      hsdata = NULL;
    }


      hsdata = (AllHessData *) calloc(1,sizeof(AllHessData));
      if ( (rc = read_hess_runheader(iobuf,&(hsdata)->run_header)) < 0 )
      {
        Warning("Reading run header failed.");
        exit(1);
      }
      fprintf(stderr,"\nStarting run %d\n",(hsdata)->run_header.run);
      for (itel=0; itel<=(hsdata)->run_header.ntel; itel++)
      {

        tel_id = (hsdata)->run_header.tel_id[itel];
        (hsdata)->camera_set[itel].tel_id = tel_id;
        (hsdata)->camera_org[itel].tel_id = tel_id;
        (hsdata)->pixel_set[itel].tel_id = tel_id;
        (hsdata)->pixel_disabled[itel].tel_id = tel_id;
        (hsdata)->cam_soft_set[itel].tel_id = tel_id;
        (hsdata)->tracking_set[itel].tel_id = tel_id;
        (hsdata)->point_cor[itel].tel_id = tel_id;
        (hsdata)->event.num_tel = (hsdata)->run_header.ntel;
        (hsdata)->event.teldata[itel].tel_id = tel_id;
        (hsdata)->event.trackdata[itel].tel_id = tel_id;
        if ( ((hsdata)->event.teldata[itel].raw = 
            (AdcData *) calloc(1,sizeof(AdcData))) == NULL )
        {
          Warning("Not enough memory");
          exit(1);
        }
        (hsdata)->event.teldata[itel].raw->tel_id = tel_id;
        if ( ((hsdata)->event.teldata[itel].pixtm =
            (PixelTiming *) calloc(1,sizeof(PixelTiming))) == NULL )
        {
          Warning("Not enough memory");
          exit(1);
        }
        (hsdata)->event.teldata[itel].pixtm->tel_id = tel_id;
        if ( ((hsdata)->event.teldata[itel].img = 
            (ImgData *) calloc(2,sizeof(ImgData))) == NULL )
        {
          Warning("Not enough memory");
          exit(1);
        }
        (hsdata)->event.teldata[itel].max_image_sets = 2;
        (hsdata)->event.teldata[itel].img[0].tel_id = tel_id;
        (hsdata)->event.teldata[itel].img[1].tel_id = tel_id;
        (hsdata)->tel_moni[itel].tel_id = tel_id;
        (hsdata)->tel_lascal[itel].tel_id = tel_id;
      }
  

      break;
    // end case IO_TYPE_HESS_RUNHEADER:
      /* =================================================== */
    case IO_TYPE_HESS_MCRUNHEADER:
      
      rc = read_hess_mcrunheader(iobuf,&(hsdata)->mc_run_header);
      break;
      /* =================================================== */
    case IO_TYPE_MC_INPUTCFG:
      {
      }
      break;
      /* =================================================== */
    case 70: /* How sim_hessarray was run and how it was configured. */
      break;

      /* =================================================== */
    case IO_TYPE_HESS_CAMSETTINGS:

      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Camera settings for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_camsettings(iobuf,&(hsdata)->camera_set[itel]);

      break;
      /* =================================================== */
    case IO_TYPE_HESS_CAMORGAN:

      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Camera organisation for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_camorgan(iobuf,&(hsdata)->camera_org[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_PIXELSET:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Pixel settings for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_pixelset(iobuf,&(hsdata)->pixel_set[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_PIXELDISABLE:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Pixel disable block for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_pixeldis(iobuf,&(hsdata)->pixel_disabled[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_CAMSOFTSET:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Camera software settings for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_camsoftset(iobuf,&(hsdata)->cam_soft_set[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_POINTINGCOR:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Pointing correction for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_pointingcor(iobuf,&(hsdata)->point_cor[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_TRACKSET:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Tracking settings for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_trackset(iobuf,&(hsdata)->tracking_set[itel]);
      break;
      /* =================================================== */
      /* =============   IO_TYPE_HESS_EVENT  =============== */
      /* =================================================== */
    case IO_TYPE_HESS_EVENT:
      rc = read_hess_event(iobuf,&(hsdata)->event,-1);
      *event_id = item_header.ident;
      break;
      /* =================================================== */
    case IO_TYPE_HESS_CALIBEVENT:
      {
        printf("RDLR: CALIBEVENT!\n");
      }
      break;
      /* =================================================== */
    case IO_TYPE_HESS_MC_SHOWER:
      rc = read_hess_mc_shower(iobuf,&(hsdata)->mc_shower);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_MC_EVENT:
      rc = read_hess_mc_event(iobuf,&(hsdata)->mc_event);

      break;
      /* =================================================== */
    case IO_TYPE_MC_TELARRAY:
      if ( hsdata && (hsdata)->run_header.ntel > 0 )
      {
        rc = read_hess_mc_phot(iobuf,&(hsdata)->mc_event);
      } 
      break;
      /* =================================================== */
      /* With extended output option activated, the particles
   arriving at ground level would be stored as seemingly
   stray photon bunch block. */
    case IO_TYPE_MC_PHOTONS:
      break;
      /* =================================================== */
    case IO_TYPE_MC_RUNH:
    case IO_TYPE_MC_EVTH:
    case IO_TYPE_MC_EVTE:
    case IO_TYPE_MC_RUNE:
      break;
      /* =================================================== */
    case IO_TYPE_HESS_MC_PE_SUM:
      rc = read_hess_mc_pe_sum(iobuf,&(hsdata)->mc_event.mc_pesum);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_TEL_MONI:
      // Telescope ID among others in the header
      tel_id = (item_header.ident & 0xff) | 
        ((item_header.ident & 0x3f000000) >> 16); 
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
        "Telescope monitor block for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_tel_monitor(iobuf,&(hsdata)->tel_moni[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_LASCAL:
      tel_id = item_header.ident; // Telescope ID is in the header
      if ( (itel = find_tel_idx(tel_id)) < 0 )
      {
        char msg[256];
        snprintf(msg,sizeof(msg)-1,
           "Laser/LED calibration for unknown telescope %d.", tel_id);
        Warning(msg);
        exit(1);
      }
      rc = read_hess_laser_calib(iobuf,&hsdata->tel_lascal[itel]);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_RUNSTAT:
      rc = read_hess_run_stat(iobuf,&hsdata->run_stat);
      break;
      /* =================================================== */
    case IO_TYPE_HESS_MC_RUNSTAT:
      rc = read_hess_mc_run_stat(iobuf,&hsdata->mc_run_stat);
      break;
      /* (End-of-job or DST) histograms */
    case 100:
      {
      }
      break;
    default:
      if ( !ignore )
      fprintf(stderr,"WARNING: Ignoring unknown data block type %ld\n",item_header.type);
    } // end switch item_header.type

  /* What did we actually get? */
  return (int) item_header.type;
}

