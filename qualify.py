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
Mar 2016 :
- use qualify-table.csv from same folder as data
- print every 100th line processed in logfile (faster)
- Alan's enhancements: snr biases, DUT TX SNR plot
- FigSize specified in qualify-table.csv
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

sys.path.append('..')
import lib

parser = argparse.ArgumentParser(description='Radio Qualification logfile analysis')
parser.add_argument('-f','--ffn_in',help='input file')
parser.add_argument('-c','--compress',action='store_true',default=False)
myargs = parser.parse_args()

ffn_in = myargs.ffn_in
compress_flag = myargs.compress

#ffn_in = 'test-data/test run = 10 pii 975 864002.pkl'

# temporary override
#ffn_in = '/Volumes/Transcend/Data/IRAP/test run = 10 pii 975 864002.pkl'
#ffn_in = '/media/brandon/C0E5-8BEE/Data/Qualify items from Alan/Enhancements/Dry run (with resp snr)006.csv'
#ffn_in = '/media/brandon/C0E5-8BEE/Data/Qualify items from Alan/Enhancements/Dry run (with resp snr)006.pkl'


#------- Read logfile and pickle it
#ffn_in = './test-data/test run = 10 pii 975 864002.pkl'
if not ffn_in :
    ffn_in = lib.query_file()

path,fn_in = os.path.split(ffn_in)
fn_main,fn_ext = os.path.splitext(fn_in)
fn_pkl = fn_main + '.pkl'
ffn_pkl = os.path.join(path,fn_pkl)

if fn_ext == '.csv' :
    #if not os.path.isfile(ffn_pkl) or compress_flag :
    D = lib.read_log(ffn_in)
    fh_pkl = open(ffn_pkl,'wb')
    pickle.dump(D,fh_pkl)
    fh_pkl.close()
    print 'Compressed data saved to ', ffn_pkl
else :
    D = pickle.load(open(ffn_pkl,'rb'))

#------------- read qualify table
import csv
pii_table = []
snr_bias_table = []
qualify_table_ffn = os.path.join(path,'qualify-table.csv')
with open(qualify_table_ffn,'rb') as csvfile :
    #    stuff = csv.reader(csvfile,delimiter=' ',quotechar='|')
    stuff = csv.reader(csvfile)
    for row in stuff :
        print ', '.join(row)
        if 'FigSize' == row[0] :
            fig_size = (int(row[1]),int(row[2]))
        elif 'Pii' == row[0][:3] :
            pii_row = (row[0], row[1], row[2], row[3].lstrip(' '))
            pii_table.append(pii_row)
        elif 'Range Limit' == row[0] :
            range_limits = ( float(row[1]), float(row[2]) )
        elif 'SNR Limit' == row[0] :
            snr_limits = ( float(row[1]), float(row[2]) )
        elif 'Pass/Fail SNR' == row[0] :
            pass_fail_snr = float(row[1])
        elif 'SNR Bias' == row[0] :
            snr_bias_row = (int(row[1]),float(row[2]))
            #snr_bias_row = [int(row[1]),float(row[2])]
            snr_bias_table.append(snr_bias_row)

pii_array = np.array(pii_table,dtype=[('label','S10'),('low','f4'),('high','f4'),('color','S10')])
snr_bias_array = np.array(snr_bias_table,dtype=[('nodeID',int),('snr_bias',float)])
#pp(pii_array)
#pp(range_limits)
#pp(snr_limits)
#pdb.set_trace()

#------------------------- plot_ranges ----------------------------------------
# def plot_ranges(RA,nodeID) :
#
#     nodeID_mask = RA['rspID'] == nodeID
#
#     t_vec = RA[nodeID_mask]['t_host']
#     t0 = RA['t_host'][0]
#     t_vec = t_vec - t0
#
#     r_vec = RA[nodeID_mask]['rmeas']
#
#     plt.plot(t_vec,r_vec,'b.')
#     plt.grid(True)

#------------------------- plot_snr ----------------------------------------
# def plot_snr(RA,nodeID,color,low,high,label,pass_fail) :
#
#     nodeID_mask = RA['rspID'] == nodeID
#
#     mask_pii_hi = RA[nodeID_mask]['t_stopwatch'] >= low
#     mask_pii_hi = mask_pii_hi.ravel()
#
#     mask_pii_low = RA[nodeID_mask]['t_stopwatch'] <= high
#     mask_pii_low = mask_pii_low.ravel()
#
#     mask_pii = np.logical_and(mask_pii_hi,mask_pii_low)
#
#     t0 = RA['t_host'][0]
#     t_vec = RA[nodeID_mask][mask_pii]['t_host'] - t0
#     vpk_vec = RA[nodeID_mask][mask_pii]['vpeak']
#     noise_vec = RA[nodeID_mask][mask_pii]['noise']
#     snr_vec = 20.*np.log10(np.divide(vpk_vec,noise_vec))
#
#     lineH, = plt.plot(t_vec,snr_vec,color,
#             hold=True, linestyle='None', marker='o', markersize=6,
#             markerfacecolor=color, markeredgecolor=color, label=label)
#     if t_vec.size > 0 :
#         plt.plot([min(t_vec),max(t_vec)],[pass_fail,pass_fail],'k-')
#     plt.grid(True)
#
#     return lineH

req_list = np.unique(D['RcmRanges']['reqID'])
rsp_list = np.unique(D['RcmRanges']['rspID'])
pii_list = np.unique(D['RcmRanges']['t_stopwatch'])

fn_pdf = fn_main + '.pdf'
ffn_pdf = os.path.join(path,fn_pdf)
pdf = PdfPages(ffn_pdf)

plt.ion()
#rsp_list = [101,102]
for nodeID in rsp_list :

    RA = D['RcmRanges'].ravel()

    if 'fig_size' in locals() :
        fig = plt.figure(figsize=fig_size)
    else :
        fig = plt.figure()
    #figsize_pix = fig.get_size_inches()*fig.dpi

    #-------------- Plot Ranges ------------------------------------------------
    ax0 = plt.subplot(311)
    #plot_ranges(RA,nodeID)
    nodeID_mask = RA['rspID'] == nodeID
    t_vec = RA[nodeID_mask]['t_host']
    t0 = RA['t_host'][0]
    t_vec = t_vec - t0
    r_vec = RA[nodeID_mask]['rmeas']
    plt.plot(t_vec,r_vec,'b.')
    plt.grid(True)
    plt.suptitle(fn_main,fontsize=14)
    plt.title('Responder: %d' % (nodeID),fontsize=14)
    plt.ylabel('Distance (m)',fontsize=14)
    if 'range_limits' in locals() :
        ax0.set_ylim(range_limits)

    #-------------- Plot TX SNR ------------------------------------------------
    ax1 = plt.subplot(312)

    lineH = []
    for iPii in range(1,len(pii_array)) :
        nodeID_mask = RA['rspID'] == nodeID
        mask_pii_hi = RA[nodeID_mask]['t_stopwatch'] >= pii_array[iPii]['low']
        mask_pii_hi = mask_pii_hi.ravel()
        mask_pii_low = RA[nodeID_mask]['t_stopwatch'] <= pii_array[iPii]['high']
        mask_pii_low = mask_pii_low.ravel()
        #mask_pii = np.logical_and(mask_pii_hi,mask_pii_low)
        mask_pii = mask_pii_hi & mask_pii_low

        t_vec = RA[nodeID_mask][mask_pii]['t_host'] - RA['t_host'][0]
        vpk_vec = RA[nodeID_mask][mask_pii]['vpeak']
        noise_vec = RA[nodeID_mask][mask_pii]['noise']
        snr_vec = 20.*np.log10(np.divide(vpk_vec,noise_vec))

        snr_bias_index = np.where(snr_bias_array['nodeID']==nodeID)
        snr_bias = snr_bias_array[snr_bias_index]['snr_bias']
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

    #lineH =     [plot_snr(RA, nodeID, pii_array[0]['color'], pii_array[0]['low'], pii_array[0]['high'], pii_array[0]['label'], pass_fail_snr)]
    #for iPii in range(1,len(pii_array)) :
    #    lineH.append(plot_snr(RA, nodeID, pii_array[iPii]['color'], pii_array[iPii]['low'], pii_array[iPii]['high'], pii_array[iPii]['label'], pass_fail_snr))
    plt.ylabel('DUT TX SNR (dB)',fontsize=14)
    plt.xlabel('Time (s)')
    plt.legend(bbox_to_anchor=(0.,1.03,1.,.102),
                mode='expand',ncol=len(lineH),fancybox=True,shadow=True)
    if 'snr_limits' in locals() :
        ax1.set_ylim(snr_limits)



    # lineH =     [plot_snr(RA, nodeID, pii_array[0]['color'], pii_array[0]['low'], pii_array[0]['high'], pii_array[0]['label'], pass_fail_snr)]
    # for iPii in range(1,len(pii_array)) :
    #     lineH.append(plot_snr(RA, nodeID, pii_array[iPii]['color'], pii_array[iPii]['low'], pii_array[iPii]['high'], pii_array[iPii]['label'], pass_fail_snr))
    # plt.ylabel('DUT TX SNR (dB)',fontsize=14)
    # plt.xlabel('Time (s)')
    # plt.legend(bbox_to_anchor=(0.,1.03,1.,.102),
    #             mode='expand',ncol=len(lineH),fancybox=True,shadow=True)
    # if 'snr_limits' in locals() :
    #     ax1.set_ylim(snr_limits)


    #-------------- Plot RX SNR ------------------------------------------------
    ax2 = plt.subplot(313)

    lineH = []
    for iPii in range(1,len(pii_array)) :
        nodeID_mask = RA['rspID'] == nodeID
        mask_pii_hi = RA[nodeID_mask]['t_stopwatch'] >= pii_array[iPii]['low']
        mask_pii_hi = mask_pii_hi.ravel()
        mask_pii_low = RA[nodeID_mask]['t_stopwatch'] <= pii_array[iPii]['high']
        mask_pii_low = mask_pii_low.ravel()
        #mask_pii = np.logical_and(mask_pii_hi,mask_pii_low)
        mask_pii = mask_pii_hi & mask_pii_low

        t_vec = RA[nodeID_mask][mask_pii]['t_host'] - RA['t_host'][0]
        snr_vec = RA[nodeID_mask][mask_pii]['reqSNR']

        snr_bias_index = np.where(snr_bias_array['nodeID']==nodeID)
        snr_bias = snr_bias_array[snr_bias_index]['snr_bias']
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
