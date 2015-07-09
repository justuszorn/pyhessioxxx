/** @file read_cta_4toy.c
 *  @short A skeleton program reading H.E.S.S. data.
 *
 *  A set of different functions to read H.E.S.S. data and to stream
 *  the read data into a given format for the Data Management toy pipeline
 *  The code is a 90%-"copy-paste" version of read_hess_nr.c 
 *  and read_hess.c (this directory) 
 *  so it has the same License rights.
 *  This program also created FITS tables with infomation about MC simulations 
 *  data, CTA array and telescopes/cameras included in the simulations.
 *  A description of how to use it is in CTA Readmine.
 *
 * Suggestions/complains to reyes@mpi-hd.mpg.de
 *
 */
#include "initial.h"      /* This file includes others as required. */
#include "io_basic.h"     /* This file includes others as required. */
#include "io_hess.h"
#include "fileopen.h"
#include "warning.h"
#include <fitsio.h>
#include <signal.h>

#ifndef _UNUSED_
# ifdef __GNUC__
#  define _UNUSED_ __attribute__((unused))
# else
#  define _UNUSED_
# endif
#endif

#define CALIB_SCALE 0.92

#define LSTMA 400
#define MSTMA 100
#define SSTMA 15
#define SCTMA 1000

int debug = 0;

static int interrupted;

void stop_signal_function (int isig);
static void syntax (char *program);
static void show_run_summary(AllHessData *hsdata, int nev, int ntrg, double plidx,
   double wsum_all, double wsum_trg, double rmax_x, double rmax_y, double rmax_r);
static char* find_ctadata_dir(void);
static void select_cta_array(AllHessData *hsdata,const char* ctalayout);
static int find_telescope(int tel_id, char *telarray);
static void print_hess_event_4prototype(AllHessData *hsdata,int evt_id, int level, int scenario);
static void create_hess_fits_tables_4prototype(fitsfile *fptrH,fitsfile *fptrT,fitsfile *fptrP,fitsfile *fptrM,AllHessData *hsdata);
static void fill_hess_fits_tables_headers_4prototype(fitsfile *fptrH,AllHessData *hsdata);
static void fill_hess_fits_tables_telescopes_4prototype(fitsfile *fptrT,AllHessData *hsdata);
static void fill_hess_fits_tables_pixels_4prototype(fitsfile *fptrP,AllHessData *hsdata);
static void fill_hess_fits_tables_mcshower_4prototype(fitsfile *fptrM,AllHessData *hsdata, int events);
double calibrate_pixel_amplitude(AllHessData *hsdata, int itel, int ipix, 
   int dummy, double cdummy);

double calibrate_pixel_amplitude(AllHessData *hsdata, int itel, int ipix, 
   _UNUSED_ int dummy, _UNUSED_ double cdummy)
{
   int i = ipix, npix, significant, hg_known;
   double npe, sig_hg, npe_hg;
#if (H_MAX_GAINS >= 2)
   double sig_lg, npe_lg;
   int lg_known;
#endif
   AdcData *raw;

   if ( hsdata == NULL || itel < 0 || itel >= H_MAX_TEL )
      return 0.;
   npix = hsdata->camera_set[itel].num_pixels;
   if ( ipix < 0 || ipix >= npix )
      return 0.;
   raw = hsdata->event.teldata[itel].raw;
   if ( raw == NULL )
      return 0.;
   if ( ! raw->known )
      return 0.;
 
   significant = hsdata->event.teldata[itel].raw->significant[i];

   hg_known = hsdata->event.teldata[itel].raw->adc_known[HI_GAIN][i];
   sig_hg = hg_known ? (hsdata->event.teldata[itel].raw->adc_sum[HI_GAIN][i] -
        hsdata->tel_moni[itel].pedestal[HI_GAIN][i]) : 0.;
   npe_hg = sig_hg * hsdata->tel_lascal[itel].calib[HI_GAIN][i];


#if (H_MAX_GAINS >= 2 )
   lg_known = hsdata->event.teldata[itel].raw->adc_known[LO_GAIN][i];
   sig_lg = lg_known ? (hsdata->event.teldata[itel].raw->adc_sum[LO_GAIN][i] -
        hsdata->tel_moni[itel].pedestal[LO_GAIN][i]) : 0.;
   npe_lg = sig_lg * hsdata->tel_lascal[itel].calib[LO_GAIN][i];
#endif

   if ( !significant ) 
      npe = 0.;
#if (H_MAX_GAINS >= 2 )
   /* FIXME: we should be more flexible here: */
   else if ( hg_known && sig_hg < 10000 && sig_hg > -1000 )
      npe = npe_hg;
   else if ( raw->num_gains >= 2 )
      npe = npe_lg;
#endif
   else
      npe = npe_hg;

   /* npe is in units of 'mean photo-electrons'. */
   /* We convert to experimentalist's */
   /* 'peak photo-electrons' now. */
   return CALIB_SCALE * npe;
}

/* ---------------------- stop_signal_function -------------------- */
/*
 *  Stop the program gracefully when it catches an INT or TERM signal.
 *
 *  @param isig  Signal number.
 *
 *  @return (none)
 */

void stop_signal_function (int isig)
{
   if ( isig >= 0 )
   {
      fprintf(stderr,"Received signal %d\n",isig);
   }
   if ( !interrupted )
      fprintf(stderr,
      "Program stop signal. Stand by until current data block is finished.\n");

   interrupted = 1;
   
   signal(SIGINT,SIG_DFL);
   signal(SIGTERM,SIG_DFL);
}


static void syntax (char *program)
{
   printf("Syntax: %s [ options ] [ - | input_fname ... ]\n",program);
   printf("Options:\n");
   printf("   --debug            (Display debug messages.)\n"); 
   printf("   --prototype        (Display event information for CTA pipelines prototype.)\n"); 
   printf("   --level            (Display data level to stream (0, 1 or 2). Only if --prototype)\n"); 
   printf("   --s                (Scenario (1 or 2) (Only if --prototype and for level=0).)\n"); 
   printf("   --max-events n     (Skip remaining data after so many triggered events.)\n"); 
   printf("   --array-layout n     (CTA array layout to be extracted from the MC)\n"); 

   exit(1);
}

static void show_run_summary(AllHessData *hsdata, int nev, int ntrg, double plidx,
   double wsum_all, double wsum_trg, double rmax_x, double rmax_y, double rmax_r)
{
   static int explained = 0;

   if ( ! explained )
   {
      printf("\n#@; Column 1: Run number\n"
             "#@;        2: ID of primary particle\n"
             "#@;        3: Number of events, total\n"
             "#@;        4: Number of events, triggered\n"
             "#@;        5: Altitude (mean) [deg.]\n"
             "#@;        6: Azimuth (mean) [deg.]\n"
             "#@;        7: Cone (max) [deg.]\n"
             "#@;        8: Lower limit of energy range [TeV]\n"
             "#@;        9: Upper limit of energy range [TeV]\n"
             "#@;       10: Spectral index in simulation\n"
             "#@;       11: Spectral index in weighting\n"
             "#@;       12: Weighted sum of events, total\n"
             "#@;       13: Weighted sum of events, triggered\n"
             "#@;       14: Maximum horizontal core distance in X\n"
             "#@;       15: Maximum horizontal core distance in Y\n"
             "#@;       16: Maximum core distance in shower plane\n"
             "#@;       17: Supposed maximum core distance\n");
      explained = 1;
   }
   printf("\n@; %d %d %d %d   %5.2f %5.2f %4.2f    %6.4f %6.4f %5.3f %5.3f   %f %f   %3.1f %3.1f %3.1f %3.1f\n", 
     hsdata->run_header.run, hsdata->mc_shower.primary_id, nev, ntrg,
     0.5*(180./M_PI)*
      (hsdata->mc_run_header.alt_range[0]+hsdata->mc_run_header.alt_range[1]),
     0.5*(180./M_PI)*
      (hsdata->mc_run_header.az_range[0]+hsdata->mc_run_header.az_range[1]),
     (180./M_PI)*hsdata->mc_run_header.viewcone[1],
     hsdata->mc_run_header.E_range[0], hsdata->mc_run_header.E_range[1],
     hsdata->mc_run_header.spectral_index, plidx,
     wsum_all, wsum_trg, rmax_x, rmax_y, rmax_r,
     hsdata->mc_run_header.core_range[1]);
}
static void print_hess_event_4prototype (AllHessData *hsdata, int evt_id, int level, int scenario)
{
  // Check if in the current configuration enough telescopes (>=2) give trigger in this event
  int itel=0;
  int tti=0, nout=0;
  for(tti=0;tti<hsdata->event.central.num_teltrg;tti++)
    {
      int tid = hsdata->event.central.teltrg_list[tti];
      for (itel=0; itel<=hsdata->run_header.ntel; itel++)
	{
	  if (hsdata->camera_set[itel].tel_id!=tid) continue;
	  if (hsdata->camera_set[itel].num_mirrors == -1 )
	    nout = nout+1;
	}					       
    }
  /*printf("DEBUG A hsdata->event.central.num_teltrg[%d], nout[%d], hsdata->run_header.min_tel_trig[%d]\n",
		  hsdata->event.central.num_teltrg, nout, hsdata->run_header.min_tel_trig );
  */
  if ( (hsdata->event.central.num_teltrg - nout) < hsdata->run_header.min_tel_trig) return;
    

  for (itel=0; itel<=hsdata->run_header.ntel; itel++)
    {
	// printf("-> tel index[%d]\n", itel);

      switch (level)
	{
	  AdcData *raw;
	  ImgData *img;
	  
	case 0:
	  raw = hsdata->event.teldata[itel].raw;
	  if (hsdata->event.teldata[itel].known)
	    {
	      int ipix =0.;
	      for(ipix=0.;ipix<raw->num_pixels;ipix++)
			{
			  if (ipix>=atoi(getenv("MAX_PRINT_ARRAY"))) break;
			  int igain=0.;
			  for(igain=0.;igain<raw->num_gains;igain++)
				{
				 // printf("-> igain[%d]\n", igain);

				//  printf("RDLR evt[%d] tel_id[%d] pix[%d] num_gain[%d]\n",evt_id,hsdata->event.teldata[itel].tel_id,ipix,raw->num_gains);
				  switch (scenario)
				{
				case 1:
				  if(raw->num_samples>0)
					{
					  int isamp=0.;
					  for (isamp=0.;isamp<raw->num_samples;isamp++)
				//	printf(" sample[%d]",raw->adc_sample[igain][ipix][isamp]);
					  printf("\n");
					}
				  else
					{
					  fprintf(stderr,"Something is wrong in my kingdom\n");
					}
				  break;
				case 2:
				  printf(" %d\n",raw->adc_sum[igain][ipix]);
				  break;
				case 3:
				  if(!raw->significant[ipix]){
					printf(" adc-sum[%d]\n",raw->adc_sum[igain][ipix]);
				  }
				  else{
					if(raw->num_samples>0)
					  {
						int isamp=0.;
						for (isamp=0.;isamp<raw->num_samples;isamp++)
						{
					//	  printf("-> isamp[%d]\n", isamp);
						  printf("evt_id[ %d ], tel_id[ %d ],channel[ %d ],pix[ %d ], slice[ %d ] ->  %d\n",
								  evt_id,
								  hsdata->event.teldata[itel].tel_id,
								  raw->num_gains,
								  ipix,
								  isamp,
								  raw->adc_sample[igain][ipix][isamp]);
						  //telId[ 118 ],channel[ 1  ],pix[ 1 ], slice[ 7 ] ->  21.0

						  printf("\n");
						}
					  }
					else{
					  fprintf(stderr,"Something is wrong in my kingdom\n");
					}
				  }
				  break;
				default:
				  fprintf(stderr,"Wrong scenario for data level 0. %d != 1, 2 or 3\n",scenario);
				}// end switch over the scenarios
				} // end loop gains
			} // end loop over pixels
	    } // if triggered telescopes
	  break; // end data level 0
	case 1:
	  raw = hsdata->event.teldata[itel].raw;
	  if (hsdata->event.teldata[itel].known)
	    {
	      int ipix =0.;
	      for(ipix=0.;ipix<raw->num_pixels;ipix++)
		{
		  if (ipix>=atoi(getenv("MAX_PRINT_ARRAY"))) break;
		  printf("RDLR %d %d %d",evt_id,hsdata->event.teldata[itel].tel_id,ipix);
		  double pe = calibrate_pixel_amplitude(hsdata,itel,ipix,0.,0.);
		  printf(" %.3f\n",pe);
		} // end loop over pixels
	    } // if triggered telescopes
	  break; // end data level 1
	case 3: // FIXME: NO SIMULATED DATA FOR THIS!!!!
	  img = hsdata->event.teldata[itel].img;
	  if (hsdata->event.teldata[itel].known)
	    {
	      printf("RDLR %d %d %.3f\n",evt_id,hsdata->event.teldata[itel].tel_id,img->amplitude);
	    } // if triggered telescopes
	  break; // end data level 2
	    default:
	      if (debug) fprintf(stderr,"Wrong data level. %d != 0,1 or 3\n",level);
	} // end switch levels
    } // end loop over telescopes
}

static char* find_ctadata_dir()
{
  //printf("Finding CTA data directory...\n");
  char *dir;
  if (strcmp(getenv("CTADATA"),"") == 0)
    {
      dir = "./";
    }
  else
    {
      dir = getenv("CTADATA");
    }
  return dir;

}
/*
20A = string
J = Integer
E = float 
 */
static void create_hess_fits_tables_4prototype(fitsfile *fptrH,fitsfile *fptrT,fitsfile *fptrP,fitsfile *fptrM,AllHessData *hsdata)
{
  if (debug) printf("Creating FITS run headers tables...\n");
  int rc = 0;
  int status = 0;

  {
    // --------------- RUN HEADERS -------------------
    const int NCOL = 17;
    char *type[] = {"run_number","run_start_time","run_type",
		    "tracking_mode","tracking_pos_x","tracking_pos_y",
		    "offset_fov_x","off_fov_y","reverse_flag",
		    "conv_depth","conv_ref_pos_x","conv_ref_pos_y",
		    "number_telescopes","min_number_telescopes_trigger",
		    "duration","target","observer"};
    char *form[] = {"J","20A","J",
		    "J","E","E",
		    "E","E","J",
		    "E","E","E",
		    "J","J",
		    "J","100A","100A"};
    char *unit[] = {"DN","DN","DN",
		    "DN","DN","DN",
		    "DN","DN","DN",
		    "DN","DN","DN",
		    "DN","DN",
		    "DN","DN","DN"};
    char extname[255] = "HEADER_RUN";
    int numhdu=-1;
    if (fits_get_num_hdus(fptrH,&numhdu,&status)) fits_report_error(stderr,status);
    if (numhdu==0)
      {
	if (fits_create_tbl(fptrH,BINARY_TBL,0,NCOL,type,form,unit,extname,&status)) fits_report_error(stderr,status);
      }
  }
  

  {
    // --------------- Initialize TELESCOPES tables -------------------
    if (debug) printf("Creating FITS TELESCOPES tables...\n");
    const int NCOL = 10;
    char *type[] = {"tel_id","tel_pos_x","tel_pos_y","tel_pos_z",
		    "focal_length","mirror_area",
		    "num_pixels","camera_rot","num_gains","num_slides"};
    char *form[] = {"J","E","E","E",
		    "E","E",
		    "J","E","J","J"};
    char *unit[] = {"DN","DN","DN","DN",
		    "DN","DN",
		    "DN","DN","DN","DN"};
    char extname[255] = "";
    int t=0;
    // Loop over the telescopes in run
    for (t=0; t<hsdata->run_header.ntel;t++)
      {
	int tel_id = hsdata->run_header.tel_id[t];
	rc = sprintf(extname,"HEADER_TEL_%d",tel_id);
	// FIXME: que abra una tabla por telescopio
	if (fits_create_tbl(fptrT,BINARY_TBL,0,NCOL,type,form,unit,extname,&status)) fits_report_error(stderr,status);
      } // end loop over the telescopes in run
  } 

  {
    // --------------- Initialize PIXELS tables -------------------
    if (debug) printf("Creating FITS PIXELS tables...\n");
    const int NCOL = 6;
    char *type[] = {"pixel_id","pixel_pos_x","pixel_pos_y","pixel_area","pixel_size","drawer"};
    char *form[] = {"J","E","E","E","E","J"};
    char *unit[] = {"DN","[m]","[m]","[m^2]","[m]","DN"};
    char extname[255] = "";
    int t=0;
    // Loop over the telescopes in run
    for (t=0; t<hsdata->run_header.ntel;t++)
      {
	int tel_id = hsdata->run_header.tel_id[t];
	rc = sprintf(extname,"HEADER_CAM_%d",tel_id);
	// FIXME: que abra una tabla por telescopio
	if (fits_create_tbl(fptrP,BINARY_TBL,0,NCOL,type,form,unit,extname,&status)) fits_report_error(stderr,status);
      } // end loop over the telescopes in run
  }

  {
    // --------------- Initialize MCSHOWER tables -------------------
    if (debug) printf("Creating FITS MC tables...\n");
    const int NCOL = 11;
    char *type[] = {"shower_num","primary_id","energy",
		    "azimuth","altitude","depth_start",
		    "h_first_int","xmax","hmax","emax","cmax"};
    char *form[] = {"J","J","E",
		    "E","E","E",
		    "E","E","E","E","E"};
    char *unit[] = {"DN","DN","[TeV]",
		    "rad","rad","[g/cm^2]",
		    "[m]","[g/cm^2]","[m]","DN","DN"};
    char extname[255] = "EVENTS_MC_SHOWER";
    if (fits_create_tbl(fptrM,BINARY_TBL,0,NCOL,type,form,unit,extname,&status)) fits_report_error(stderr,status);
  }

}
static void fill_hess_fits_tables_headers_4prototype(fitsfile *fptrH,AllHessData *hsdata)
{

  int status = 0;
  char extname[255] = "HEADER_RUN";
  if (fits_movnam_hdu(fptrH,BINARY_TBL,extname,0,&status)) fits_report_error(stderr,status);
  long nrows = 0;
  if (fits_get_num_rows(fptrH,&nrows,&status)) fits_report_error(stderr,status);
  nrows = nrows+1;
  if(fits_write_col(fptrH,TINT,1,nrows,1,1,&hsdata->run_header.run,&status)) fits_report_error(stderr,status);
// FIXME: if(fits_write_col(fptrH,TSTRING,2,1,1,1,*"ciento-tres",&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,3,nrows,1,1,&hsdata->run_header.run_type,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,4,nrows,1,1,&hsdata->run_header.tracking_mode,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,5,nrows,1,1,&hsdata->run_header.direction[0],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,6,nrows,1,1,&hsdata->run_header.direction[1],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,7,nrows,1,1,&hsdata->run_header.offset_fov[0],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,8,nrows,1,1,&hsdata->run_header.offset_fov[1],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,9,nrows,1,1,&hsdata->run_header.reverse_flag,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,10,nrows,1,1,&hsdata->run_header.conv_depth,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,11,nrows,1,1,&hsdata->run_header.conv_ref_pos[0],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TDOUBLE,12,nrows,1,1,&hsdata->run_header.conv_ref_pos[1],&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,13,nrows,1,1,&hsdata->run_header.ntel,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,14,nrows,1,1,&hsdata->run_header.min_tel_trig,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TINT,15,nrows,1,1,&hsdata->run_header.duration,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TSTRING,16,nrows,1,1,&hsdata->run_header.target,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrH,TSTRING,17,nrows,1,1,&hsdata->run_header.observer,&status)) fits_report_error(stderr,status);

}

static void fill_hess_fits_tables_telescopes_4prototype(fitsfile *fptrT,AllHessData *hsdata)
{
  int rc = 0;
  int status = 0;
  char extname[255] = "";

  int t=0;
  // Loop over the telescopes in run
  for (t=0; t<hsdata->run_header.ntel;t++)
    {
      int tel_id = hsdata->run_header.tel_id[t];
      //if (hsdata->camera_set[t].num_mirrors == -1) continue;
      rc = sprintf(extname,"HEADER_TEL_%d",tel_id);
      if (rc==-1) return;
      if (fits_movnam_hdu(fptrT,BINARY_TBL,extname,0,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TINT,1,1,1,1,&hsdata->run_header.tel_id[t],&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,2,1,1,1,&hsdata->run_header.tel_pos[t][0],&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,3,1,1,1,&hsdata->run_header.tel_pos[t][1],&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,4,1,1,1,&hsdata->run_header.tel_pos[t][2],&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,5,1,1,1,&hsdata->camera_set[t].flen,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,6,1,1,1,&hsdata->camera_set[t].mirror_area,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TINT,7,1,1,1,&hsdata->camera_set[t].num_pixels,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TDOUBLE,8,1,1,1,&hsdata->camera_set[t].cam_rot,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TINT,9,1,1,1,&hsdata->camera_org[t].num_gains,&status)) fits_report_error(stderr,status);
      if(fits_write_col(fptrT,TINT,10,1,1,1,&hsdata->pixel_set[t].sum_bins,&status)) fits_report_error(stderr,status);
    } // end loop over the telescopes
}

static void fill_hess_fits_tables_pixels_4prototype(fitsfile *fptrP,AllHessData *hsdata)
{
  int rc = 0;
  int status = 0;
  char extname[255] = "";

  int t=0;
  // Loop over the telescopes in run
  for (t=0; t<hsdata->run_header.ntel;t++)
    {
      int tel_id = hsdata->run_header.tel_id[t];
      rc = sprintf(extname,"HEADER_CAM_%d",tel_id);
      if (rc==-1) return;
      if (fits_movnam_hdu(fptrP,BINARY_TBL,extname,0,&status)) fits_report_error(stderr,status);
      
      int p = 0;
      for (p=0; p<hsdata->camera_set[t].num_pixels;p++)
	{
	  int pix_id = p;
	  if(fits_write_col(fptrP,TINT,1,p+1,1,1,&pix_id,&status)) fits_report_error(stderr,status);
	  if(fits_write_col(fptrP,TDOUBLE,2,p+1,1,1,&hsdata->camera_set[t].xpix[pix_id],&status)) fits_report_error(stderr,status);
	  if(fits_write_col(fptrP,TDOUBLE,3,p+1,1,1,&hsdata->camera_set[t].ypix[pix_id],&status)) fits_report_error(stderr,status);
	  if(fits_write_col(fptrP,TDOUBLE,4,p+1,1,1,&hsdata->camera_set[t].area[pix_id],&status)) fits_report_error(stderr,status);
	  if(fits_write_col(fptrP,TDOUBLE,5,p+1,1,1,&hsdata->camera_set[t].size[pix_id],&status)) fits_report_error(stderr,status);
	  if(fits_write_col(fptrP,TDOUBLE,6,p+1,1,1,&hsdata->camera_org[t].drawer[pix_id],&status)) fits_report_error(stderr,status);
	} // end loop over the pixels
    } // end loop over the telescopes
}

static void fill_hess_fits_tables_mcshower_4prototype(fitsfile *fptrM,AllHessData *hsdata, int events)
{
  int status = 0;
  char extname[255] = "EVENTS_MC_SHOWER";
  if (fits_movnam_hdu(fptrM,BINARY_TBL,extname,0,&status)) fits_report_error(stderr,status);
  int n = hsdata->mc_shower.shower_num;
  if(fits_write_col(fptrM,TINT,1,n,1,1,&hsdata->mc_shower.shower_num,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TINT,2,n,1,1,&hsdata->mc_shower.primary_id,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,3,n,1,1,&hsdata->mc_shower.energy,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,4,n,1,1,&hsdata->mc_shower.azimuth,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,5,n,1,1,&hsdata->mc_shower.altitude,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,6,n,1,1,&hsdata->mc_shower.depth_start,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,7,n,1,1,&hsdata->mc_shower.h_first_int,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,8,n,1,1,&hsdata->mc_shower.xmax,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,9,n,1,1,&hsdata->mc_shower.hmax,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,10,n,1,1,&hsdata->mc_shower.emax,&status)) fits_report_error(stderr,status);
  if(fits_write_col(fptrM,TDOUBLE,11,n,1,1,&hsdata->mc_shower.cmax,&status)) fits_report_error(stderr,status);
}
static void select_cta_array(AllHessData *hsdata,const char* ctalayout)
{
  if (debug) printf("select_cta_array\n");
  int itel=0, rc =0, status=0, nri=0;
  fitsfile *fptr=NULL;
  char fitsfilename[500] = "";
  rc = sprintf(fitsfilename,"%s/ArraysLayouts.fits",find_ctadata_dir());
  if (debug) printf("ctalayout = %s\n",fitsfilename);
  if (fits_open_data(&fptr,fitsfilename,READONLY,&status)) fits_report_error(stderr,status);
  long nrows=0;
  int ncols=0;
  if (fits_get_num_rows(fptr,&nrows,&status)) fits_report_error(stderr,status); 
  if (fits_get_num_cols(fptr,&ncols,&status)) fits_report_error(stderr,status); 
  if (debug) printf("Rows = %ld, Cols = %d\n",nrows,ncols);
  char telarray[1000]="", *val;
  char lstarray[1000]="", mstarray[1000]="", sstarray[1000]="", sctarray[1000]="";
  int anynul;
  for(nri=1;nri<=nrows;nri++){
    val=telarray;
    if (fits_read_col_str(fptr,1,nri,1,1,"*",&val,&anynul,&status)) fits_report_error(stderr,status);
    char *conf = strtok(val," ");
    if (strcmp(conf,ctalayout)==0)
      {
	val=lstarray;
	if (fits_read_col_str(fptr,2,nri,1,1,"*",&val,&anynul,&status)) fits_report_error(stderr,status);
	if (debug) printf("LST = %s\n",lstarray);
	val=mstarray;
	if (fits_read_col_str(fptr,3,nri,1,1,"*",&val,&anynul,&status)) fits_report_error(stderr,status);
	if (debug) printf("MST = %s\n",mstarray);
	val = sstarray;
	if (fits_read_col_str(fptr,4,nri,1,1,"*",&val,&anynul,&status)) fits_report_error(stderr,status);
	if (debug) printf("SST = %s\n",sstarray);
	val= sctarray;
	if (fits_read_col_str(fptr,5,nri,1,1,"*",&val,&anynul,&status)) fits_report_error(stderr,status);
	if (debug) printf("SCT = %s\n",sctarray);
	break;
      } 
  }

  for (itel=0; itel<hsdata->run_header.ntel; itel++)
    {
      int num_mirrors = hsdata->camera_set[itel].num_mirrors;
      hsdata->camera_set[itel].num_mirrors = -1;
      // LSTs:
      if (hsdata->camera_set[itel].mirror_area>(LSTMA-50) && hsdata->camera_set[itel].mirror_area<(LSTMA+50) && find_telescope(hsdata->run_header.tel_id[itel],lstarray)){
      	if (debug) printf("Tel: %d in array = %s\n",hsdata->run_header.tel_id[itel],lstarray);
      	  hsdata->camera_set[itel].num_mirrors = num_mirrors;
      }
      // MSTs:
	if (hsdata->camera_set[itel].mirror_area>(MSTMA-50) && hsdata->camera_set[itel].mirror_area<(MSTMA+50) && find_telescope(hsdata->run_header.tel_id[itel],mstarray)){
	  if (debug) printf("Tel: %d in array = %s\n",hsdata->run_header.tel_id[itel],mstarray);
      	hsdata->camera_set[itel].num_mirrors = num_mirrors;
      }
      // SSTs:
	if (hsdata->camera_set[itel].mirror_area>(SSTMA-10) && hsdata->camera_set[itel].mirror_area<(SSTMA+10) && find_telescope(hsdata->run_header.tel_id[itel],sstarray))
      	{
      	  if (debug) printf("Tel: %d in array = %s\n",hsdata->run_header.tel_id[itel],sstarray);
      	  hsdata->camera_set[itel].num_mirrors = num_mirrors;
      	}


    } // end loop over the telescopes
  if(fits_close_file(fptr,&status)) fits_report_error(stderr,status);

}
static int find_telescope(int tel_id, char *telarray)
{
  char str[1000]="";
  strcpy(str,telarray);
  char *pch = strtok(str,",");
  while(pch!=NULL)
    {
      if(atoi(pch) == tel_id) return 1;
      char interval[1000]="";
      strcpy(interval,pch);
      if(strchr(interval,'-')!=NULL){
	char substr[10]="";
	strncpy(substr,interval,(strchr(interval,'-')-interval));
	int first = atoi(substr);
	int last = atoi(strchr(interval,'-')+1);
	if (tel_id>=first && tel_id<=last) return 1;
      }

      pch = strtok(NULL,",");

    }

  return 0;
}

/* -------------------- main program ---------------------- */
/** 
 *  @short Main program 
 *
 *  Main program function of read_hess.c program.
 */

int main (int argc, char **argv)
{
  IO_BUFFER *iobuf = NULL;
  IO_ITEM_HEADER item_header;
  const char *input_fname = NULL;
  int itel, rc = 0;
  int iarg;
  char *program = argv[0];
  char *ctalayout = "";
  int quiet = 1, _UNUSED_ verbose = 0, ignore = 0;
  int prototype = 0, level = -1, scenario = -1;
  size_t events = 0, max_events = 0, mcevents=0;
  int knewrun = 0;

  int tel_id;

  double plidx = -2.7;
  double wsum_all = 0., wsum_trg = 0.;
  double rmax_x = 0., rmax_y = 0., rmax_r = 0.;
  int nev = 0, ntrg = 0;

  static AllHessData *hsdata;

  // Creation of the HEADERS FITS files
  fitsfile *fptrH=NULL;
  fitsfile *fptrT=NULL;
  fitsfile *fptrP=NULL;
  fitsfile *fptrM=NULL;
  //int rc = 0;
  int status = 0;
  char filename[255];
  rc = sprintf(filename,"!%s/RunHeaders.fits",find_ctadata_dir());
  if (fits_create_file(&fptrH,filename,&status)) fits_report_error(stderr,status);
  // end Creation of the HEADERS FITS files

  interrupted = 0;
  for (iarg=0; iarg<argc; iarg++)
    printf("%s ",argv[iarg]);
  printf("\n");
  /* Catch INTerrupt and TERMinate signals to stop program */
  signal(SIGINT,stop_signal_function);
  signal(SIGTERM,stop_signal_function);
  interrupted = 0;

  /* Check assumed limits with the ones compiled into the library. */
  H_CHECK_MAX();
  if ( (iobuf = allocate_io_buffer(1000000L)) == NULL )
    {
      Error("Cannot allocate I/O buffer");
      exit(1);
    }
  iobuf->max_length = 100000000L;


  if (argc == 1){
    syntax(program);
    exit(1);
  }

  while ( argc > 1 )
    {
      if ( strcmp(argv[1],"--help") == 0 )
	{
	  printf("\nread_cta_4toy: A 'hacked' version of the read_hess_nr.c program for viewing sim_hessarray data for the CTA pipeline toy.\n\n");
	  syntax(program);
	}
      else if ( strcmp(argv[1],"--debug") == 0)
	{
	  debug=1;
	  argc -= 1;
	  argv += 1;
	  continue;
	}
      else if ( strcmp(argv[1],"--prototype") == 0)
	{
	  prototype=1;
	  argc -= 1;
	  argv += 1;
	  continue;
	}
      else if ( strcmp(argv[1],"--level") == 0 && argc > 2)
	{
	  level = atol(argv[2]);
	  argc -= 2;
	  argv += 2;
	  continue;
	}
      else if ( strcmp(argv[1],"--s") == 0 && argc > 2)
	{
	  if (level == 0)
	    scenario = atol(argv[2]);
	  else
	    scenario = -1;
	  argc -= 2;
	  argv += 2;
	  continue;
	}
      else if ( strcmp(argv[1],"--max-events") == 0 && argc > 2 )
	{
	  max_events = atol(argv[2]);
	  argc -= 2;
	  argv += 2;
	  continue;
	}
      else if ( strcmp(argv[1],"--array-layout") == 0 && argc > 2 )
	{
	  ctalayout = argv[2];
	  argc -= 2;
	  argv += 2;
	  continue;
	}
      else if ( argv[1][0] == '-' && argv[1][1] != '\0' ) // Este tiene que ir el ultimo, nino todo casca
	{
	  printf("Syntax error at '%s'\n", argv[1]);
	  syntax(program);
	}
      else
	break;
    }

  /* if (prototype==1 && (level==-1 || level==-1)) */
  /*   { */
  /*     //printf("level=%d, scenario=%d\n", level,scenario); */
  /*     printf("Missing --level and -s options!!!\n"); */
  /*     syntax(program); */
  /*   } */

  /* Now go over rest of the command line */
  // Now read the rest of the command line = an array of input files

  while ( argc > 1 || input_fname != NULL )
    {
      if ( interrupted )
	break;
      if ( argc > 1 )
	{
	  if ( argv[1][0] == '-' && argv[1][1] != '\0' )
	    syntax(program);
	  else
	    {
	      input_fname = argv[1];
	      argc--;
	      argv++;
	    }
	}

      if ( strcmp(input_fname ,"-") == 0 )
	{
	  iobuf->input_file = stdin;
	}
      else if ( (iobuf->input_file = fileopen(input_fname,READ_BINARY)) == NULL )
	{
	  perror(input_fname);
	  Error("Cannot open input file.");
	  break;
	}


      fflush(stdout);
      fprintf(stderr,"%s\n",input_fname);
      printf("\nInput file '%s' has been opened.\n",input_fname);
      input_fname = NULL;
     

      for (;;) /* Loop over all data in the input file */
	{
	  if ( interrupted )
	    break;
	 
	  /* Find and read the next block of data. */
	  /* In case of problems with the data, just give up. */
	  if ( find_io_block(iobuf,&item_header) != 0 )
	    break;
	  if ( max_events > 0 && events >= max_events )
	    {
	      if ( iobuf->input_file != stdin )
		break;
	      if ( skip_io_block(iobuf,&item_header) != 0 )
		break;
	      continue;
	    }
	  if ( read_io_block(iobuf,&item_header) != 0 )
	    break;

	  //printf("RDLR: type %ld (%d,%d)\n",item_header.type,IO_TYPE_HESS_RUNHEADER,IO_TYPE_HESS_RUNHEADER + 200);

	  if ( hsdata == NULL && 
	       item_header.type > IO_TYPE_HESS_RUNHEADER &&
	       item_header.type < IO_TYPE_HESS_RUNHEADER + 200)
	    {
	      fprintf(stderr,"Trying to read event data before run header.\n");
	      fprintf(stderr,"Skipping this data block.\n");
	      continue;
	    }
	 
	  /* if (debug) */
	  /*   printf("DBG: evt=%zu : type %ld %ld\n",events,item_header.type,item_header.ident); */

	  switch ( (int) item_header.type )
	    {
	      /* =================================================== */
	    case IO_TYPE_HESS_RUNHEADER:
	      hsdata = (AllHessData *) calloc(1,sizeof(AllHessData));
	      if ( (rc = read_hess_runheader(iobuf,&hsdata->run_header)) < 0 )
		{
		  Warning("Reading run header failed.");
		  exit(1);
		}
	      fprintf(stderr,"\nStarting run %d\n",hsdata->run_header.run);
	      //print_hess_runheader(iobuf);
	      for (itel=0; itel<=hsdata->run_header.ntel; itel++)
		{
		  tel_id = hsdata->run_header.tel_id[itel];
		  hsdata->camera_set[itel].tel_id = tel_id;
		  hsdata->camera_org[itel].tel_id = tel_id;
		  hsdata->pixel_set[itel].tel_id = tel_id;
		  hsdata->pixel_disabled[itel].tel_id = tel_id;
		  hsdata->cam_soft_set[itel].tel_id = tel_id;
		  hsdata->tracking_set[itel].tel_id = tel_id;
		  hsdata->point_cor[itel].tel_id = tel_id;
		  hsdata->event.num_tel = hsdata->run_header.ntel;
		  hsdata->event.teldata[itel].tel_id = tel_id;
		  hsdata->event.trackdata[itel].tel_id = tel_id;
		  if ( (hsdata->event.teldata[itel].raw = 
			(AdcData *) calloc(1,sizeof(AdcData))) == NULL )
		    {
		      Warning("Not enough memory");
		      exit(1);
		    }
		  hsdata->event.teldata[itel].raw->tel_id = tel_id;
		  if ( (hsdata->event.teldata[itel].pixtm =
			(PixelTiming *) calloc(1,sizeof(PixelTiming))) == NULL )
		    {
		      Warning("Not enough memory");
		      exit(1);
		    }
		  hsdata->event.teldata[itel].pixtm->tel_id = tel_id;
		  if ( (hsdata->event.teldata[itel].img = 
			(ImgData *) calloc(2,sizeof(ImgData))) == NULL )
		    {
		      Warning("Not enough memory");
		      exit(1);
		    }
		  hsdata->event.teldata[itel].max_image_sets = 2;
		  hsdata->event.teldata[itel].img[0].tel_id = tel_id;
		  hsdata->event.teldata[itel].img[1].tel_id = tel_id;
		  hsdata->tel_moni[itel].tel_id = tel_id;
		  hsdata->tel_lascal[itel].tel_id = tel_id;
		}

	      if ( prototype && rc == 0){
		// Creation of the TELESCOPES, PIXELS and MC FITS files
		fptrT=NULL;
		fptrP=NULL;
		fptrM=NULL;
		rc = sprintf(filename,"!%s/TelescopesHeaders_%d.fits",find_ctadata_dir(),hsdata->run_header.run);
		if (fits_create_file(&fptrT,filename,&status)) fits_report_error(stderr,status);
		rc = sprintf(filename,"!%s/PixelsHeaders_%d.fits",find_ctadata_dir(),hsdata->run_header.run);
		if (fits_create_file(&fptrP,filename,&status)) fits_report_error(stderr,status);
		rc = sprintf(filename,"!%s/MC_%d.fits",find_ctadata_dir(),hsdata->run_header.run);
		if (fits_create_file(&fptrM,filename,&status)) fits_report_error(stderr,status);
		// end Creation of the TELESCOPES, PIXELS and MC FITS files
		printf("Creating FITS tables 4 prototype\n");
		create_hess_fits_tables_4prototype(fptrH,fptrT,fptrP,fptrM,hsdata);
		fill_hess_fits_tables_headers_4prototype(fptrH,hsdata);
		knewrun = 1;
	      }

	      break;
	      /* =================================================== */
	    case IO_TYPE_HESS_MCRUNHEADER:
	      rc = read_hess_mcrunheader(iobuf,&hsdata->mc_run_header);
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
	      rc = read_hess_camsettings(iobuf,&hsdata->camera_set[itel]);
	      //printf("CAMSET %d\n",tel_id);
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
	      rc = read_hess_camorgan(iobuf,&hsdata->camera_org[itel]);
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
	      rc = read_hess_pixelset(iobuf,&hsdata->pixel_set[itel]);
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
	      rc = read_hess_pixeldis(iobuf,&hsdata->pixel_disabled[itel]);
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
	      rc = read_hess_camsoftset(iobuf,&hsdata->cam_soft_set[itel]);
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
	      rc = read_hess_pointingcor(iobuf,&hsdata->point_cor[itel]);
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
	      rc = read_hess_trackset(iobuf,&hsdata->tracking_set[itel]);
	      break;
	      /* =================================================== */
	      /* =============   IO_TYPE_HESS_EVENT  =============== */
	      /* =================================================== */
	    case IO_TYPE_HESS_EVENT:
	      rc = read_hess_event(iobuf,&hsdata->event,-1);
	      /* if ( debug || rc != 0 ) */
	      /* 	printf("read_hess_event(), rc = %d\n",rc); */
	      if ( prototype && rc == 0 && level<4){
		if (knewrun==1 && level <3)
		  {
		    printf("For CTA layout = %s\n",ctalayout);
		    if (! strcmp(ctalayout,"")==0) select_cta_array(hsdata,ctalayout);
		    if (!debug){
		      printf("Filling FITS HEADERS: TELESCOPES and PIXELS...\n"); 
		      fill_hess_fits_tables_telescopes_4prototype(fptrT,hsdata);
		      fill_hess_fits_tables_pixels_4prototype(fptrP,hsdata);
		    }
		  }
		print_hess_event_4prototype(hsdata,item_header.ident,level,scenario);
		knewrun = 0;
		//fill_hess_fits_tables_mcshower_4prototype(fptrM,hsdata,events);

	      }
	      events++;
	      break;
	      /* =================================================== */
	    case IO_TYPE_HESS_CALIBEVENT:
	      {
		if (debug) printf("RDLR: CALIBEVENT!\n");
	      }
	      break;
	      /* =================================================== */
	    case IO_TYPE_HESS_MC_SHOWER:
	      rc = read_hess_mc_shower(iobuf,&hsdata->mc_shower);

	      if ( prototype && rc == 0 && level<3 ){
		fill_hess_fits_tables_mcshower_4prototype(fptrM,hsdata,mcevents+1);
	      }
	      mcevents++;
	      break;
	      /* =================================================== */
	    case IO_TYPE_HESS_MC_EVENT:
	      rc = read_hess_mc_event(iobuf,&hsdata->mc_event);
	      break;
	      /* =================================================== */
	    case IO_TYPE_MC_TELARRAY:
	      if ( hsdata && hsdata->run_header.ntel > 0 )
		{
		  rc = read_hess_mc_phot(iobuf,&hsdata->mc_event);
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
	      rc = read_hess_mc_pe_sum(iobuf,&hsdata->mc_event.mc_pesum);
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
	      rc = read_hess_tel_monitor(iobuf,&hsdata->tel_moni[itel]);
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


	} // end loop over all the data in the input file

      /* What did we actually get? */

      if ( iobuf->input_file != NULL && iobuf->input_file != stdin )
	fileclose(iobuf->input_file);
      iobuf->input_file = NULL;
      reset_io_block(iobuf);

      if ( hsdata != NULL && !quiet )
	show_run_summary(hsdata,nev,ntrg,plidx,wsum_all,wsum_trg,rmax_x,rmax_y,rmax_r);
      else if ( nev > 0 )
	printf("%d of %d events triggered\n", ntrg, nev);
    
      if ( hsdata != NULL )
	hsdata->run_header.run = 0;

   
      printf("Total number of events processed %zu\n",events);
      printf("Total number of MC events processed %zu\n",mcevents);

      if (fptrT!=NULL) if(fits_close_file(fptrT,&status)) fits_report_error(stderr,status);
      if (fptrP!=NULL) if(fits_close_file(fptrP,&status)) fits_report_error(stderr,status);
      if (fptrM!=NULL) if(fits_close_file(fptrM,&status)) fits_report_error(stderr,status);

    } // end loop on all the arguments in the command line -> array of input files
  if(fits_close_file(fptrH,&status)) fits_report_error(stderr,status);
  if (iobuf->output_file != NULL) fileclose(iobuf->output_file);

  return 0;
}
