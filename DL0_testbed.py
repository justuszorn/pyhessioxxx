# This file verify data read by pyhessio and
# compares results with DL0_testbed: https://forge.in2p3.fr/projects/model/wiki/DL0_testbed
# run this testbed with:
# python DL0_testbed.py 
#


from hessio import *
import xlwt
import matplotlib.pyplot as plt
import argparse
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages


LSTMA=400
MSTMA=100
SSTMA=15
SCTMA=70

LST = 'LST'
MST = 'MST'
SST = 'SST'
SCT = 'SCT'

TRIGGER = 'TRIGGER'
SUM     = 'SUM'
TIMVAL  = 'TIMVAL'
PEAK    = 'PEAK'

TEL_TYPE =(LST, MST , SST , SCT)
HIST_TYPE=(TRIGGER, SUM, TIMVAL , PEAK)

"""
TEL_ID_TYPE=dict()
TEL_ID_TYPE[4]=LST
TEL_ID_TYPE[25]=MST
TEL_ID_TYPE[50]=SST
TEL_ID_TYPE[110]=SCT
"""

NORMAL = 'NORMAL' 
READ   = 'READ'
WRITE  = 'WRITE'


def get_data_filename(filename, tel_type,hist_type):
    return filename+"_"+tel_type+'_'+hist_type +'.dat'
                
                
def get_telescope_type(telescopeId):
    ma = get_mirror_area(telescopeId)

    if ma >(LSTMA-50) and ma <(LSTMA+50): return LST
    elif ma >(MSTMA-10) and ma <(MSTMA+10): return MST
    elif ma >(SSTMA-10) and ma <(SSTMA+10): return SST
    elif ma > (SCTMA-10) and ma < (SCTMA+10): return SCT



def get_data(filename,wanted,xls=None,mode=NORMAL):
    
    # create a dictionary containig 16 lists (one by histogram and one by telescope type)
    lists=dict()
    lists.append(2)
    for tel_type in TEL_TYPE:
        lists[tel_type] = dict()
        for hist_type in HIST_TYPE:
            lists[tel_type][hist_type]=list()
    
    if (mode == NORMAL or mode == WRITE) and file_open(filename) == 0: 
        
        evt_id = 0
        for run_id, event_id in move_to_next_event():
            print("--< Start Event",evt_id,">--",end="\r")
            evt_id = evt_id + 1
           
            #define counters 
            counters=dict()
            for tel_type in TEL_TYPE:
                counters[tel_type] = dict()
                for hist_type in HIST_TYPE:
                    counters[tel_type][hist_type]=0

            # get list of telescope with data
            tel_list = get_telescope_with_data_list()

            # loop over telescope id for telescope with data
            for tel_id in tel_list: 
                # get telescope type by its id(then by in mirror_area)
                tel_type = get_telescope_type(tel_id)

                # increment  TRIGGER list for corresponding telescope type
                counters[tel_type][TRIGGER] = counters[tel_type][TRIGGER] + 1 

                adc_sums = get_adc_sum(tel_id,0)
                tim_vals = get_pixel_timing_timval(tel_id)# get a 2D np array
                peak = get_pixel_timing_peak_global(tel_id)
                
                if tel_id == 4 or tel_id == 25 or tel_id == 50 or tel_id == 110:
                    # if tel_id is 4,25,50 or 100 get corresponding counter
                    counter = counters[tel_type]
                        
                    # sum counter[SUM] for this telescope type
                    for adc_sum in adc_sums:
                        if adc_sum > 1000:
                            counter[SUM]= counter[SUM]+1

                    # sum counter[TIMVAL] for this telescope type
                    for tim_val_per_pixel in tim_vals:
                        if tim_val_per_pixel[5] > 4: 
                            counter[TIMVAL] = counter[TIMVAL]+1
                            
                    # append peak value to corresponding list
                    if peak > 0. : 
                        lists[tel_type][PEAK].append(int(peak))


            # append counters values to corresponding list
            for tel_type in [LST,MST,SST,SCT]:
                for hist in [SUM,TRIGGER,TIMVAL]:
                  lists[tel_type][hist].append(counters[tel_type][hist])   
            
            # for questionary
            wanted_for_run=wanted[run_id]
            glob_count = get_global_event_count()
            if ( glob_count in wanted_for_run):
                couple_list = wanted_for_run[glob_count]
                for item in couple_list:
                    tel_id = item[0]
                    pix_id = item[1]

                    if tel_id in tel_list:
                        channel = 0
                        adc_sample = get_adc_sample(tel_id,channel)
                        time_slice = 7
                        trace = adc_sample[pix_id]
                        sample_7 = trace[time_slice]
                        adc_sum = get_adc_sum(tel_id,channel)
                        time_val = get_pixel_timing_timval(tel_id)
                            
                        current=(run_id,glob_count,tel_id,pix_id,int(sample_7),
                        int(adc_sum[pix_id]),
                        float(time_val[pix_id][0]),
                        float(time_val[pix_id][1]),
                        float(time_val[pix_id][4]),
                        float(time_val[pix_id][5]),
                        float(time_val[pix_id][6]))
                    else: # no trigger for this telescope during this event
                        current=(run_id,glob_count,tel_id,pix_id,'NA',
                        'NA',
                        'NA',
                        'NA',
                        'NA',
                        'NA',
                        'NA')   
                    if xls != None:
                        xls.append(current)
                                    
        # if mode = WRITE, write data in a data file
        if  mode == WRITE: 
            for tel_type in TEL_TYPE:
                for hist in HIST_TYPE:
                    data_filename= get_data_filename(filename,tel_type,hist)
                    with open(data_filename, 'w') as f:
                        for s in lists[tel_type][hist]:
                            f.write(str(s) + '\n')
    
    # if mode == READ get data in a data file
    elif mode == READ:                    
        for tel_type in TEL_TYPE:
            for hist in HIST_TYPE:
                data_filename= get_data_filename(filename,tel_type,hist)
                with open(data_filename, 'r') as f:
                    lists[tel_type][hist] = [float(line.rstrip('\n')) for line in f]
                    
                    

        

   

    if mode == NORMAL or mode == READ: 
        if mode == READ: run_id = 0
        color_list = {MST: 'b', SST: 'r', LST: 'g', SCT: 'y'}
        label_list = {MST: 'MST (tel_id=25)', SST: 'SST (tel_id=50)', LST: 'LST (tel_id=4)', SCT: 'SCT (tel_id=110)'}
        
        pdf_filename = 'DL0_testbed'+ '_' + filename.split('/')[-1]+  '.pdf'
        pp = PdfPages(pdf_filename)
        # TRIGGER hist
        maximum = 0
        for tel_type in TEL_TYPE:
            cur_list = lists[tel_type][TRIGGER]
            foo = max(cur_list)
            if foo > maximum :
                maximum = foo

        plt.clf()
        for tel_type in TEL_TYPE:
            cur_list = lists[tel_type][TRIGGER]
            if len(cur_list) > 0:
                average = round(np.mean(cur_list),2)
                plt.hist(cur_list,edgecolor=color_list[tel_type],
                    bins=int(13),
                    fill=False,
                    label=tel_type+" "+str(average), range = (0,26)) 
        
        plt.title("Triggered telescope " + str(run_id))
        plt.yscale('log')
        plt.legend()
        plt.grid()
        plt.xlabel("#telescopes")
        plt.ylabel("#events")
        plt.axis((0,26,0.1,10000))
        plt.savefig(pp, format='pdf') 
        
        plt.
    
    
        # SUM hist
        plt.clf()
        for tel_type in TEL_TYPE:
            cur_list = lists[tel_type][SUM]
            if len(cur_list) > 0:
                plt.hist(cur_list,edgecolor=color_list[tel_type],bins=200, fill = False, label=label_list[tel_type])

        plt.title("sum > 1000 Adcs " + str(run_id))
        plt.yscale('log')
        plt.legend(loc='upper center')
        plt.grid()
        plt.axis((0,2500,0.1,10000))
        plt.xlabel("#pixels (sum>1000 ADCcts")
        plt.ylabel("#events")
        plt.savefig(pp, format='pdf') 
        
    
        # TIMVAL hist
        plt.clf()
        for tel_type in TEL_TYPE:
            cur_list = lists[tel_type][TIMVAL]
            if len(cur_list) > 0:
                plt.hist(cur_list,edgecolor=color_list[tel_type],bins=200, fill = False, label=label_list[tel_type],range=(0,2000))

        plt.title("timval[5]>4 " + str(run_id))
        plt.yscale('log')
        plt.legend(loc='upper center')
        plt.grid()
        plt.axis((0,2500,0.1,10000))
        plt.xlabel("#pixels (pulse width over threshold>4")
        plt.ylabel("#events")
        plt.savefig(pp, format='pdf') 
            
        # PEAK hist
        plt.clf()
        for tel_type in TEL_TYPE:
            cur_list = lists[tel_type][PEAK]
            if len(cur_list) > 0:
                plt.hist(cur_list,edgecolor=color_list[tel_type],bins=29, fill = False, label=label_list[tel_type],range=(0,29))
        plt.title("Camera mean peak position " + str(run_id))
        plt.yscale('log')
        plt.legend()
        plt.grid()
        plt.axis((0,29,0.1,10000))
        plt.xlabel("#Camera mean peak position (time slice")
        plt.ylabel("#events")
        
        
        plt.savefig(pp, format='pdf') 
        print(pdf_filename + ' saved')   
        pp.close()
        
        
def questionary(mode = NORMAL):    
    wb = xlwt.Workbook()
    ws = wb.add_sheet("DL0_testbed")
    result = list()
    result.append(('run_id','glob_cout','telescope','pixel','sample 7','sum','tmax[0]', 'tmax[1]',  'twidth 4', 'twidth 5 ', 'twidth 6 '))
    
    wanted={}
    wanted[32364]={}
    wanted[32364][65314] = [[4,53]]
    wanted[32364][22480500]=[[17,1004]]
    wanted[32364][11793608]=[[2,35]]
    wanted[32364][12425512]=[[36,707]]
    wanted[32364][22480512]=[[103,878]]
    wanted[32364][24942910]=[[62,100],[25,100]]
    get_data("/home/jacquem/workspace/data/proton_20deg_180deg_run32364___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result,mode=mode)
    
    
    if mode == NORMAL or mode == WRITE: close_file()

    wanted={}
    wanted[31964]={}
    wanted[31964][31900] = [[4,53]]
    wanted[31964][5436400]=[[17,1008]]
    wanted[31964][5429500]=[[2,35]]
    wanted[31964][5559500]=[[99,707]]
    wanted[31964][9054700]=[[103,563]]
    wanted[31964][9996602]=[[38,100],[25,100]]
    get_data("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result,mode=mode)
    if mode == NORMAL or mode == WRITE: close_file()
    
    for line_id, row in enumerate(result):
        for col_id, data in enumerate(row):
            ws.write(line_id, col_id, data)
    wb.save("DL0_Testbed.xls")
    print("DL0_Testbed.xls saved")
    

    
    
if __name__ == "__main__":
    
    
    # Declare and parse command line option
    parser = argparse.ArgumentParser(description='Tel_id, pixel id and number of event to compute.')
    parser.add_argument('--m', dest='mode', required=False, help='mode READ WRITE NORMAL')
    args = parser.parse_args()

    mode = NORMAL
    if args.mode == 'WRITE' : mode = WRITE
    if args.mode == 'READ' : mode = READ
     
    questionary(mode = mode)
    print("\nDone")
    