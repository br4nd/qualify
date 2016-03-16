#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
>>> python qualify.py [-f inputfile] [-c]
where:
  inputfile is log filename to process (leave logfile blank to ask for selection)

uses qualify-table.csv in the same folder
creates <inputfile>.pkl and <inputfile>.pdf

Originally created Feb 2016
@author: B. Dewberry
Feb 21 2016: changed name to qualify.py, added qualify-info.csv
Version 2, Mar 5 2016 :
- use qualify-table.csv from same folder as data
- print every 100th line processed in logfile (faster)
- Alan's enhancements: snr biases, DUT TX SNR plot
- FigSize specified in qualify-table.csv
Version 3, Mar 14 2016:
- prints control file parms in pdf
- added TimeLimit (minutes) support in qualify-table.csv (see example in TestData subfolder)
- fixed DUT RX SNR label
- removed save to pickle (turns out csv read is just as fast, and just as compact)
- removed call to lib.read_log and lib.query_file (now self-contained - doesn't require lib)
"""

import argparse
import sys, os
import pdb
import pickle
import pprint as pp
import numpy as np
import matplotlib.pyplot as plt
#from matplotlib.patches import patches
from matplotlib.backends.backend_pdf import PdfPages
from pprint import pprint as pp

#sys.path.append('..')
#import lib

parser = argparse.ArgumentParser(description='Radio Qualification logfile analysis')
parser.add_argument('-f','--ffn_in',help='input file')
parser.add_argument('-c','--compress',action='store_true',default=False)
myargs = parser.parse_args()

ffn_in = myargs.ffn_in
compress_flag = myargs.compress

# temporary override
#ffn_in = '/media/brandon/C0E5-8BEE/Data/Qualify items from Alan/Enhancements/Dry run (with resp snr)006.pkl'
#ffn_in = './TestData/Dry run - rsp snr - short.csv'

#------- Query logfile name
if not ffn_in :
    import Tkinter, tkFileDialog
    prompt = 'Choose an input file'
    types = [('All files','*'),('csv','*.csv'),('pkl','*.pkl')]
    defaultextension = '*'
    root = Tkinter.Tk()
    root.withdraw() # don't want a full GUI
    root.update()
    ffn_in = tkFileDialog.askopenfilename(parent=root,title=prompt,filetypes=types)
#    ffn_in = lib.query_file()

path,fn_in = os.path.split(ffn_in)
fn_main,fn_ext = os.path.splitext(fn_in)
fn_pkl = fn_main + '.pkl'
ffn_pkl = os.path.join(path,fn_pkl)

fn_pdf = fn_main + '.pdf'
ffn_pdf = os.path.join(path,fn_pdf)
pdf = PdfPages(ffn_pdf)

#------------- read qualify parameter table
import csv
pii_table = []
snr_bias_table = []
qualify_table_ffn = os.path.join(path,'qualify-table.csv')
with open(qualify_table_ffn,'rb') as csvfile :
    #    stuff = csv.reader(csvfile,delimiter=' ',quotechar='|')
    plt.ion()
    fig,ax = plt.subplots()
    stuff = csv.reader(csvfile)
    fig_y = 0.95
    fig_y_snrbias = 0.95
    fontsize = 12
    for row in stuff :
        print ', '.join(row)
        if row[0] == '' :
            continue
        if 'FigSize' == row[0] :
            fig_size = (int(row[1]),int(row[2]))
            plt.text(0.05,fig_y,'%s: %s, %s' % (row[0],row[1],row[2]),fontsize=fontsize)
        elif 'Pii' == row[0][:3] :
            pii_row = (row[0], row[1], row[2], row[3].lstrip(' '))
            pii_table.append(pii_row)
            plt.text(0.05,fig_y,'%s: %s, %s, %s' % (row[0],row[1],row[2],row[3]),fontsize=fontsize)
        elif 'Range Limit' == row[0] :
            range_limits = ( float(row[1]), float(row[2]) )
            plt.text(0.05,fig_y,'%s: %s, %s' % (row[0],row[1],row[2]),fontsize=fontsize)
        elif 'SNR Limit' == row[0] :
            snr_limits = ( float(row[1]), float(row[2]) )
            plt.text(0.05,fig_y,'%s: %s, %s' % (row[0],row[1],row[2]),fontsize=fontsize)
        elif 'Pass/Fail SNR' == row[0] :
            pass_fail_snr = float(row[1])
            plt.text(0.05,fig_y,'%s: %s' % (row[0],row[1]),fontsize=fontsize)
            fig_height = 1.0
        elif 'TimeLimit' == row[0][:9] :
            time_limit_minutes = int(row[1])
            time_limit_seconds = time_limit_minutes * 60
            plt.text(0.05,fig_y,'%s: %s' % (row[0],row[1]),fontsize=fontsize)
        elif 'SNR Bias' == row[0] :
            snr_bias_row = (int(row[1]),float(row[2]))
            snr_bias_table.append(snr_bias_row)
            plt.text(0.5,fig_y_snrbias,'%s: %s, %s' % (row[0],row[1],row[2]),fontsize=fontsize)
            fig_y_snrbias -= 0.05
        fig_y -= 0.05
#pdb.set_trace()

plt.tick_params(
    axis='both',          # changes apply to the x-axis
    which='both',      # both major and minor ticks are affected
    bottom='off',      # ticks along the bottom edge are off
    top='off',         # ticks along the top edge are off
    labelbottom='off') # labels along the bottom edge are off
fig.patch.set_visible(False)
ax.axis('off')
plt.draw()
pdf.savefig()

pii_array = np.array(pii_table,dtype=[('label','S10'),('low','f4'),('high','f4'),('color','S10')])
snr_bias_array = np.array(snr_bias_table,dtype=[('rspID',int),('snr_bias',float)])


#----- Read logfile into range_array
range_array = np.empty(1,
            dtype = [('timestamp',float),('rspID',int),('stopwatch',int),
                ('rmeas',float),('noise',int),('vpeak',int),('reqSNR',int)])
t0 = []
irow = 0
with open(ffn_in,'rb') as csvfile :
    stuff = csv.reader(csvfile)
    for row in stuff :

        irow += 1
        if not irow % 1000 : # print a line once in a while
           print '%d: %s' % (irow,row)

        if row[0] == 'Timestamp' :
            continue

        if row[1] == ' RcmRangeInfo' :
            timestamp = float(row[0])
            if not t0 :
                t0 = timestamp
            if timestamp > t0 + time_limit_seconds :
                break

            rspID = int(row[3])
            stopwatch = int(row[7])
            rmeas = float(row[8])/1000.
            noise = int(row[19])
            vpeak = int(row[20])
            reqSNR = int(row[23])
            range_row = np.array([(timestamp,rspID,stopwatch,rmeas,noise,vpeak,reqSNR)],
                dtype = [('timestamp',float),('rspID',int),('stopwatch',int),('rmeas',float),
                ('noise',int),('vpeak',int),('reqSNR',int)])
            #pdb.set_trace()
            range_array = np.vstack((range_array,range_row))

# First entry was empty.  Trim it out.
range_array = range_array[1:]

rsp_list = np.unique(range_array['rspID'])
stopwatch_list = np.unique(range_array['stopwatch'])

plt.ion()
#rsp_list = [101,102]
for rspID in rsp_list :

    #RA = D['RcmRanges'].ravel()

    if 'fig_size' in locals() :
        fig = plt.figure(figsize=fig_size)
    else :
        fig = plt.figure()
    #figsize_pix = fig.get_size_inches()*fig.dpi


    #-------------- Plot Ranges for this rspID ---------------------------------
    ax0 = plt.subplot(311)

    rspID_mask = range_array['rspID'] == rspID
    t_vec = range_array[rspID_mask]['timestamp']
    t_vec = t_vec - t_vec[0]
    r_vec = range_array[rspID_mask]['rmeas']
    plt.plot(t_vec,r_vec,'b.')
    plt.grid(True)
    plt.suptitle(fn_main,fontsize=14)
    plt.title('Responder: %d' % (rspID),fontsize=14)
    plt.ylabel('Distance (m)',fontsize=14)
    if 'range_limits' in locals() :
        ax0.set_ylim(range_limits)


    #-------------- Plot TX SNR for this rspID -------------------------------
    ax1 = plt.subplot(312)

    lineH = []
    for iPii in range(1,len(pii_array)) :

        rspID_mask = range_array['rspID'] == rspID
        pii_hi_mask = range_array[rspID_mask]['stopwatch'] >= pii_array[iPii]['low']
        pii_low_mask = range_array[rspID_mask]['stopwatch'] <= pii_array[iPii]['high']
        pii_mask = pii_hi_mask & pii_low_mask

#        t_vec = RA[nodeID_mask][mask_pii]['t_host'] - RA['t_host'][0]
        t_vec = range_array[rspID_mask][pii_mask]['timestamp'] - range_array['timestamp'][0]
        vpk_vec = range_array[rspID_mask][pii_mask]['vpeak']
        noise_vec = range_array[rspID_mask][pii_mask]['noise']
        snr_vec = 20.*np.log10(np.divide(vpk_vec,noise_vec))

        snr_bias_index = np.where(snr_bias_array['rspID']==rspID)
        snr_bias = snr_bias_array[snr_bias_index]['snr_bias']
        if snr_bias :
            snr_vec = snr_vec + snr_bias

        color = pii_array[iPii]['color']
        label = pii_array[iPii]['label']
        lineH.append(plt.plot(t_vec,snr_vec, color,
                hold=True, linestyle='None', marker='o', markersize=6,
                markerfacecolor=color, markeredgecolor=color, label=label))

        if t_vec.size > 0 :
            plt.plot([min(t_vec),max(t_vec)],[pass_fail_snr,pass_fail_snr],'k-')
    plt.grid(True)

    plt.ylabel('DUT TX SNR (dB)',fontsize=14)
    plt.xlabel('Time (s)')
    plt.legend(bbox_to_anchor=(0.,1.03,1.,.102),
                mode='expand',ncol=len(lineH),fancybox=True,shadow=True)
    if 'snr_limits' in locals() :
        ax1.set_ylim(snr_limits)


    #-------------- Plot RX SNR for this rspID ---------------------------------
    ax2 = plt.subplot(313)

    lineH = []
    for iPii in range(1,len(pii_array)) :

        rspID_mask = range_array['rspID'] == rspID
        #nodeID_mask = RA['rspID'] == nodeID
        pii_hi_mask = range_array[rspID_mask]['stopwatch'] >= pii_array[iPii]['low']
        #mask_pii_hi = mask_pii_hi.ravel()
        pii_low_mask = range_array[rspID_mask]['stopwatch'] <= pii_array[iPii]['high']
        #mask_pii_low = mask_pii_low.ravel()
        #mask_pii = np.logical_and(mask_pii_hi,mask_pii_low)
        pii_mask = pii_hi_mask & pii_low_mask

        t_vec = range_array[rspID_mask][pii_mask]['timestamp'] - range_array['timestamp'][0]
        snr_vec = range_array[rspID_mask][pii_mask]['reqSNR']

        snr_bias_index = np.where(snr_bias_array['rspID'] == rspID)
        snr_bias = snr_bias_array[snr_bias_index]['snr_bias']
        if snr_bias :
            snr_vec = snr_vec + snr_bias

#        pdb.set_trace()

        color = pii_array[iPii]['color']
        label = pii_array[iPii]['label']
        lineH.append(plt.plot(t_vec,snr_vec, color,
                hold=True, linestyle='None', marker='o', markersize=6,
                markerfacecolor=color, markeredgecolor=color, label=label))

        if t_vec.size > 0 :
            plt.plot([min(t_vec),max(t_vec)],[pass_fail_snr,pass_fail_snr],'k-')
    plt.grid(True)

    plt.ylabel('DUT TX SNR (dB)',fontsize=14)
    plt.xlabel('Time (s)')
    plt.legend(bbox_to_anchor=(0.,1.03,1.,.102),
                mode='expand',ncol=len(lineH),fancybox=True,shadow=True)
    if 'snr_limits' in locals() :
        ax2.set_ylim(snr_limits)


    plt.draw()

    pdf.savefig()

pdf.close()

pdb.set_trace()
#raw_input('press any key to quit:')
