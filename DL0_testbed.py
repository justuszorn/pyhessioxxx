# This file verify data read by pyhessio and
# compares results with DL0_testbed: https://forge.in2p3.fr/projects/model/wiki/DL0_testbed
# run this testbed with:
# python DL0_testbed.py 
#


from hessio import *
from tkinter.test.widget_tests import PixelSizeTests
import xlwt
import matplotlib.pyplot as plt
from numpy.random import normal
from matplotlib.lines import fillStyles

LSTMA=400
MSTMA=100
SSTMA=15
SCTMA=70

def get_telescope_type(telescopeId):
    ma = get_mirror_area(telescopeId)


    if ma >(LSTMA-50) and ma <(LSTMA+50):
        return LSTMA 
        
    elif ma >(MSTMA-10) and ma <(MSTMA+10):
        return MSTMA

    elif ma >(SSTMA-10) and ma <(SSTMA+10):
        return SSTMA
        
    elif ma > (SCTMA-10) and ma < (SCTMA+10): 
        return SCTMA

    
    

def get_data(filename,wanted,xls=None):
    
    
    """
    lst=list()
    mst=list()
    sst=list()
    sct=list()
    """

    if file_open(filename) == 0: 
        """
        evt_id = 0
        for run_id, event_id in move_to_next_event():
            print("--< Start Event",evt_id,">--",end="\r")
            evt_id = evt_id + 1
           
            tel_list = get_teldata_list()
            nb_lst = 0
            nb_mst = 0
            nb_sst = 0
            nb_sct = 0
            for id in tel_list: 
                tel_type = get_telescope_type(id)
                if tel_type   == LSTMA: nb_lst = nb_lst + 1 
                elif tel_type == MSTMA: nb_mst = nb_mst + 1
                elif tel_type == SSTMA: nb_sst = nb_sst + 1
                elif tel_type == SCTMA: nb_sct = nb_sct + 1
                
            lst.append(nb_lst)
            mst.append(nb_mst)
            sst.append(nb_sst)
            sct.append(nb_sct)
            
            # for questionary
            wanted_for_run=wanted[run_id]
            glob_count = get_global_event_count()
            if ( glob_count in wanted_for_run):
                couple_list = wanted_for_run[glob_count]
                for item in couple_list:
                        tel_id = item[0]
                        pix_id = item[1]

                        channel = 0
                        adc_sample = get_adc_sample(tel_id,channel)
                        time_slice = 7
                        trace = adc_sample[pix_id]
                        sample_7 = trace[time_slice]
    
                        adc_sum = get_adc_sum(tel_id,channel)
                        
                        time_val = get_pixelTiming_timval(tel_id)
                        
                        current=(run_id,glob_count,tel_id,pix_id,int(sample_7),
                        int(adc_sum[pix_id]),
                        float(time_val[pix_id][1]),
                        float(time_val[pix_id][5]))
                        if xls != None:
                            xls.append(current)
        """
        with open("32364_lst.dat", 'r') as f:
           lst = [int(line.rstrip('\n')) for line in f]

        with open("32364_mst.dat", 'r') as f:
           mst = [int(line.rstrip('\n')) for line in f]
           
        with open("32364_sst.dat", 'r') as f:
           sst = [int(line.rstrip('\n')) for line in f]
           
        with open("32364_sct.dat", 'r') as f:
           sct = [int(line.rstrip('\n')) for line in f]

        if len(lst)>0 : plt.hist( lst,bins=13, edgecolor='g',fill=False,   label='LST', range=(0,26))
                        
        if len(mst)>0 : plt.hist(mst,bins=13, edgecolor='b', fill=False, label='MST',range=(0,26))
        
        if len(sst)>0 : plt.hist(sst,bins=13,edgecolor='r', fill=False, label='SST',range=(0,26))
        
        if len(sct)>0 : plt.hist(sct,bins=13,edgecolor='y', fill=False, label='SCT', range=(0,26))

        plt.title("Triggered telescope")
        plt.yscale('log')
        plt.legend()
        plt.grid()
        plt.axis((0,26,0.1,10000))
        plt.show()
        """
        with open("32364_lst.dat", 'w') as f:
            for s in lst:
                f.write(str(s) + '\n')

        with open("32364_mst.dat", 'w') as f:
            for s in mst:
                f.write(str(s) + '\n')
                
        with open("32364_sst.dat", 'w') as f:
            for s in sst:
                f.write(str(s) + '\n')
                
        with open("32364_sct.dat", 'w') as f:
            for s in sct:
                f.write(str(s) + '\n')
        """

        
        
def questionary():    
    wb = xlwt.Workbook()
    ws = wb.add_sheet("DL0_testbed")
    result = list()
    result.append(('run_id','glob_cout','telescope','pixel','sample 7','sum','tmax', 'twidth'))
    
    wanted={}
    wanted[32364]={}
    wanted[32364][65314] = [[4,53]]
    wanted[32364][22480500]=[[17,1004]]
    wanted[32364][11793608]=[[2,35]]
    wanted[32364][12425512]=[[36,707]]
    wanted[32364][22480512]=[[103,878]]
    wanted[32364][24942910]=[[62,100],[25,100]]
    get_data("/home/jacquem/workspace/data/proton_20deg_180deg_run32364___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result)
    close_file()

    """ 
    wanted={}
    wanted[31964]={}
    wanted[31964][31900] = [[4,53]]
    wanted[31964][5436400]=[[17,1008]]
    wanted[31964][5429500]=[[2,35]]
    wanted[31964][5559500]=[[99,707]]
    wanted[31964][9054700]=[[103,563]]
    wanted[31964][9996602]=[[38,100],[25,100]]
    get_data("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result)
    close_file()
    """ 
    
    for line_id, row in enumerate(result):
        for col_id, data in enumerate(row):
            ws.write(line_id, col_id, data)
    wb.save("DL0Testbed.xls")
    

    
    
if __name__ == "__main__":
    
    questionary()
    print("Done")
    