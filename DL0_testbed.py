# This file verify data read by pyhessio and
# compares results with DL0_testbed: https://forge.in2p3.fr/projects/model/wiki/DL0_testbed
# run this testbed with:
# python DL0_testbed.py 
#


from hessio import *
from tkinter.test.widget_tests import PixelSizeTests
import xlwt


def find_samples(filename,wanted,xls=None):
    
    
    if file_open(filename) == 0: 
        for run_id, event_id in move_to_next_event():
            glob_count = get_global_event_count()
            wanted_for_run=wanted[run_id]
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
                        """
                        current=(run_id,glob_count)
                        """
                        if xls != None:
                            xls.append(current)
                        
if __name__ == "__main__":
    
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
    find_samples("/home/jacquem/workspace/data/proton_20deg_180deg_run32364___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result)
    close_file()

    
    wanted={}
    wanted[31964]={}
    wanted[31964][31900] = [[4,53]]
    wanted[31964][5436400]=[[17,1008]]
    wanted[31964][5429500]=[[2,35]]
    wanted[31964][5559500]=[[99,707]]
    wanted[31964][9054700]=[[103,563]]
    wanted[31964][9996602]=[[38,100],[25,100]]
    find_samples("/home/jacquem/workspace/data/gamma_20deg_0deg_run31964___cta-prod2_desert-1640m-Aar.simtel.gz",wanted,xls=result)
    close_file()
    
    for line_id, row in enumerate(result):
        for col_id, data in enumerate(row):
            ws.write(line_id, col_id, data)
    wb.save("DL0Testbed.xls")