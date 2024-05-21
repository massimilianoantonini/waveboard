import tkinter as tk
import numpy as np
import tkinter.ttk as ttk
import os
import datetime
import time
import random
import matplotlib.pyplot as plt 
import subprocess
import json
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename
import subprocess
import threading
from paramiko import SSHClient
import paramiko
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')
from config_ultra import *
from matplotlib.widgets import Button
import re
import argparse
import gc
import platform
from queue import Queue
from matplotlib.colors import Normalize

parser = argparse.ArgumentParser(description="Waveboard controller - wirtten by Lorenzo Campana", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-d", "--dry", action="store_true", help="Dry run to run the program without connection to the waveboard")
parser.add_argument("-m", "--monkey", action="store_true", help="Start the waveboard controller in monkey mode @('_')@")
parser.add_argument("-p", "--parameter", action="store", default="startup_parameter.json",type=str, help="Spcify the startup parameter json file to load at startup")
parser.add_argument("-tcc", "--tcc", action="store_true", help="Start the waveboard controller in tcc mode @('_')@")



args = parser.parse_args()

print(args)

date = datetime.datetime.now()

if date.month < 10:
    month = "0"+str(date.month)
else:
    month = str(date.month)

if date.day < 10:
    day = "0"+str(date.day)
else:
    day = str(date.day)

if date.hour < 10:
    hour = "0"+str(date.hour)
else:
    hour = str(date.hour)

if date.minute < 10:
    minute = "0"+str(date.minute)
else:
    minute = str(date.minute)
    
date_format = month+day+hour+minute+str(date.year-2000)

client = SSHClient()
client.load_system_host_keys()

if getattr(args, 'dry')==False:
    client.connect(ip_address, username=username, password=password)


e_monitor=threading.Event()
e_timer=threading.Event()
e_log = threading.Event()
e_acquisition = threading.Event()
e_plot = threading.Event()



def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()

def abortable_sleep(secs, abort_event):
    abort_event.wait(timeout=secs)
    abort_event.clear()

#CONVERSIONE V BIAS CON CORREZIONE DELLA TEMPERATURA PER WVB I
# def v_adc(v_bias, t_board,ch):
#     m_slope=(m_hot-m_cold)/(temp_hot-temp_cold)
#     m_inter=(m_cold*temp_hot- temp_cold*m_hot)/(temp_hot-temp_cold)
#    
#     q_slope = (q_hot-q_cold)/(temp_hot-temp_cold)
#     q_inter = (q_cold*temp_hot - temp_cold*q_hot)/(temp_hot-temp_cold)
#     
#     v_adc=(v_bias-(t_board*q_slope+q_inter))/((t_board*m_slope)+m_inter)
#     
#     return v_adc[ch]

wvb_active="1n"
polarity="negative"

def convert_adc_to_v(element,ch):
    return ((adc_to_v_all[wvb_active][ch][1]+element*adc_to_v_all[wvb_active][ch][0])*1000)

def convert_v_to_adc(element,ch):
    return (v_to_adc_all[wvb_active][ch][1]+element*v_to_adc_all[wvb_active][ch][0])

#CONVERSIONE VBIAS SENZA CORREZIONE PER TEMPERATURA
def v_adc(v_bias,ch):
    return (v_bias-v_bias_conv_all[wvb_active][ch][1])/v_bias_conv_all[wvb_active][ch][0]


#da usare con waveboard 1.0 con tempertura funzionante 
#t_board = float(subprocess.check_output("""ssh """ + username + """@""" + ip_address + """ 'bash get_param.sh' """, shell=True)[16:21]) 

def t_daq_read_tcp():
    print("Starting DaqReadTcp...")
    stdin, stdout, stderr = client.exec_command("./DaqReadTcp")
    print(stdout.readlines())


class WbControllerUltraApp(tk.Frame):

    def __init__(self):
        super().__init__()
        self.initUI()

    def activate_wvb1(self):
        global wvb_active
        
        wvb_active="1n"
        
        self.adc_to_v=adc_to_v_all[wvb_active]
        self.v_to_adc=v_to_adc_all[wvb_active]
        self.v_bias_conv=v_bias_conv_all[wvb_active]
        print("WaveBoard 1 selezionata")
        self.lbl_wvb.configure(text='WVB'+str(wvb_active))
        
    def activate_wvb2(self):
        global wvb_active
        
        wvb_active=2
        
        self.adc_to_v=adc_to_v_all[wvb_active]
        self.v_to_adc=v_to_adc_all[wvb_active]
        self.v_bias_conv=v_bias_conv_all[wvb_active]
        print("WaveBoard 2 selezionata")
        self.lbl_wvb.configure(text='WVB 2')   

    def activate_wvb3(self):
        global wvb_active
        
        wvb_active=3
        
        self.adc_to_v=adc_to_v_all[wvb_active]
        self.v_to_adc=v_to_adc_all[wvb_active]
        self.v_bias_conv=v_bias_conv_all[wvb_active]
        print("WaveBoard 3 selezionata")
        self.lbl_wvb.configure(text='WVB 3')      
    
    def positive_polarity(self):
        global polarity
        global wvb_active
        
        polarity="positive"
        if polarity =="positive":
            wvb_active="1p"
        if polarity=="negative":
            wvb_active="1n"

        command_1 = """ cat WaveBrd_OsciMode_Positive.bit > /dev/xdevcfg """
        
        if wvb_active==2:
            command_2 = """ bash daq_set_pedestal.sh -N "0 1 2 3 4 5 6 7 8 9 10 11" -P "0x100 0x115 0x130 0x150 0x105 0x105 0x110 0x100 0x105 0x115 0x110 0x110" """
        
        if wvb_active=="1p":
            command_2 = """ bash daq_set_pedestal.sh -N "0 1 2 3 4 5 6 7 8 9 10 11" -P "350 330 325 338 345 322 352 320 333 332 340 330" """

        

        print("Changing Pedestal Values...")

        stdin, stdout, stderr = client.exec_command(command_2)
       

        time.sleep(1)

        print("Changing Board configuration...")
        #stdin, stdout, stderr = client.exec_command(command_1)

        
        self.initialize_board()
        print("Board configuration changed")
        self.lbl_wvb.configure(text='WVB '+str(wvb_active))

    def initUI(self):
        
        architecture = platform.machine()
        print(architecture)
        if "x86" in architecture:
            self.arch="x86"

        elif "aarch64" in architecture:
            self.arch="arm"

        elif "arm64" in architecture:
            self.arch="arm"

        print(self.arch)

        # build ui
        
        menubar=tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        fileMenu=tk.Menu(menubar)
        acquisitionMenu=tk.Menu(menubar)
        
        
        polarity_menu=tk.Menu(fileMenu)
        polarity_menu.add_command(label="Positive", command=self.positive_polarity)
        fileMenu.add_cascade(label="Select polarity", menu=polarity_menu, underline=0)
        
        select_board_menu=tk.Menu(fileMenu)
        select_board_menu.add_command(label="WaveBoard 1", command=self.activate_wvb1)
        select_board_menu.add_command(label="WaveBoard 2", command=self.activate_wvb2)
        select_board_menu.add_command(label="WaveBoard 3", command=self.activate_wvb3)
        select_board_menu.add_command(label="WaveBoard 4")
        
        fileMenu.add_cascade(label="Select Board", menu=select_board_menu, underline=0)

        menubar.add_cascade(label="File", underline=0, menu=fileMenu)
        
        save_parameter_menu=tk.Menu(acquisitionMenu)

        menubar.add_cascade(label="Acquisition", underline=0, menu=acquisitionMenu)
        acquisitionMenu.add_command(label="Save Parameter",command=self.save_parameter_clicked ,underline=0)
        acquisitionMenu.add_command(label="Load Parameter",command=self.load_parameter_clicked ,underline=0)

     
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True)
        self.frm_data_acquisition = ttk.Frame(self.notebook, height=500)
        self.frm_plot = ttk.Frame(self.notebook)
        self.frm_rate = ttk.Frame(self.notebook)
        self.frm_calibration = ttk.Frame(self.notebook)
        

        self.frm_data_acquisition.pack(fill='both', expand=True)
        self.frm_plot.pack(fill='both', expand=True)
        self.frm_rate.pack(fill='both', expand=True)
        self.frm_calibration.pack(fill='both', expand=True)

        self.notebook.add(self.frm_data_acquisition, text='Data acquisition')
        self.notebook.add(self.frm_plot, text='Plot and analysis')
        self.notebook.add(self.frm_rate, text='Rate Monitor')
        self.notebook.add(self.frm_calibration, text='Sensor Calibration')
    
        

        #calibration tab
        
        self.frm_cal_ch = ttk.Labelframe(self.frm_calibration)
        self.frm_cal_ch.configure(text="Sensor configuration")
        self.frm_cal_ch.grid(row='0',pady="3",column='0', columnspan='1') 
        
        self.cal_lbl_ch={}
        
        self.cal_channel_variable = {}
        self.cal_channel_option={}
        self.btn_cal_ch={}
        
        self.cal_mode_variable={}
        self.cal_mode_option={}
        self.btn_cal_mode={}

        
        self.lbl_cal_mode=tk.Label(self.frm_cal_ch)
        self.lbl_cal_mode.configure(text="Mode")
        self.lbl_cal_mode.grid(row="2",column="0")
        
        
        self.lbl_cal_sensor=tk.Label(self.frm_cal_ch)
        self.lbl_cal_sensor.configure(text="Sensor")
        self.lbl_cal_sensor.grid(row="1",column="0")
        
        
        for col in range(12):
            for row in range(3):
                if row ==0:
                    self.cal_lbl_ch[col]=tk.Label(self.frm_cal_ch)
                    self.cal_lbl_ch[col].configure(text='CH '+str(col))
                    self.cal_lbl_ch[col].grid(column=str(col+1), row=row)
                    
                if row==1:
                    self.cal_channel_variable[col]=tk.StringVar(root)
                    self.cal_channel_option[col]= ["0","1","2","3","4","5","6","7","8","9","10","11","//"]
                    self.cal_channel_variable[col].set("//")
                    
                    self.btn_cal_ch = tk.OptionMenu(self.frm_cal_ch, self.cal_channel_variable[col],*self.cal_channel_option[col])
                    self.btn_cal_ch.grid(row=str(row), column=str(col+1), padx='1', pady='1')
                
                if row==2:
                    self.cal_mode_variable[col]=tk.StringVar(root)
                    self.cal_mode_option[col]= ["V", "S"]
                    self.cal_mode_variable[col].set("S")
                    
                    self.btn_cal_mode = tk.OptionMenu(self.frm_cal_ch, self.cal_mode_variable[col],*self.cal_mode_option[col])
                    self.btn_cal_mode.grid(row=str(row), column=str(col+1), padx='1', pady='1')
        
        self.lbl_cal_ref_sensor = tk.Label(self.frm_cal_ch)
        self.lbl_cal_ref_sensor.configure(text='Reference sensor')
        self.lbl_cal_ref_sensor.grid(column=0, row=3, columnspan=3, pady="5")
        
        
        self.cal_ref_sensor_variable=tk.StringVar(root)
        self.cal_ref_sensor_option= ["0","1","2","3","4","5","6","7","8","9","10","11","//"]
        self.cal_ref_sensor_variable.set("//")
        
        self.btn_cal_ref_sensor= tk.OptionMenu(self.frm_cal_ch, self.cal_ref_sensor_variable,*self.cal_ref_sensor_option)
        self.btn_cal_ref_sensor.grid(row=str(3), column=str(3), padx='1', pady='1')

      
        self.btn_cal_start = ttk.Button(self.frm_calibration)
        self.btn_cal_start.configure(text="Start Calibration")
        self.btn_cal_start.grid(column="0", row="1", pady="3")
        self.btn_cal_start.bind('<Button-1>', self.start_calibration_clicked, add='')
        
        
        
        
        #Data acquisition tab
        
        self.btn_ch = {}
        self.ent_start = {}
        self.ent_stop = {}
        self.ent_vbias = {}
        self.ent_lead = {}
        self.ent_tail = {}

        self.ch_status = {}
        for ch in range(12):
            self.ch_status[ch] = tk.IntVar()

        self.frm_param = tk.Frame(self.frm_data_acquisition)

        self.lbl_start_th = tk.Label(self.frm_param)
        self.lbl_start_th.configure(text='Start Th')
        self.lbl_start_th.grid(column='0', row='1')
        self.lbl_stop_th = tk.Label(self.frm_param)
        self.lbl_stop_th.configure(text='Stop Th')
        self.lbl_stop_th.grid(column='0',row='2')
        self.lbl_tail = tk.Label(self.frm_param)
        self.lbl_tail.configure(text='Tail')
        self.lbl_tail.grid(column='0', row='3')
        self.lbl_lead = tk.Label(self.frm_param)
        self.lbl_lead.configure(anchor='e', text='Lead')
        self.lbl_lead.grid(column='0', padx='1', pady='1', row='4')
        self.lbl_vbias = tk.Label(self.frm_param)
        self.lbl_vbias.configure(text='V bias (V)')
        self.lbl_vbias.grid(column='0',row='5')

        for col in range(12):
            for row in range(6):
                if row == 0:  #check button
                    self.btn_ch[col]=tk.Checkbutton(self.frm_param, variable=self.ch_status[col])
                    #self.btn_ch[col]=tk.Checkbutton(self.frm_param)
                    self.btn_ch[col].configure(relief='raised', text='CH '+ str(col))
                    self.btn_ch[col].grid(column=str(col+1), row=row)
                if row == 1:
                    self.ent_start[col]=tk.Entry(self.frm_param)
                    self.ent_start[col].configure(width='6')
                    self.ent_start[col].grid(column=str(col+1), row=row)


                if row == 2:
                    self.ent_stop[col]=tk.Entry(self.frm_param)
                    self.ent_stop[col].configure(width='6')
                    self.ent_stop[col].grid(column=str(col+1), row=row)
                
                if row == 3:
                    self.ent_tail[col]=tk.Entry(self.frm_param)
                    self.ent_tail[col].configure(width='6')
                    self.ent_tail[col].grid(column=str(col+1), row=row)

                if row == 4:
                    self.ent_lead[col]=tk.Entry(self.frm_param)
                    self.ent_lead[col].configure(width='6')
                    self.ent_lead[col].grid(column=str(col+1), row=row)

                if row == 5:
                    self.ent_vbias[col]=tk.Entry(self.frm_param)
                    self.ent_vbias[col].configure(width='6')
                    self.ent_vbias[col].grid(column=str(col+1), row=row)


        
        #self.frm_param.configure(height='200', width='400')
        self.frm_param.grid(row='0', column='0', columnspan='3')

        #PARAMETER ACTION BUTTON
        self.frm_param_action = ttk.Labelframe(self.frm_data_acquisition)
        self.frm_param_action.configure(height='200', text='Parameters', width='200')
        self.frm_param_action.grid(row='1', column='0', rowspan="2")

        self.btn_load_param = ttk.Button(self.frm_param_action)
        self.btn_load_param.configure(text='Load')
        self.btn_load_param.grid(column='0', row='0',padx='10', pady='10')
        self.btn_load_param.bind('<Button-1>', self.load_parameter_clicked, add='')
        
        self.btn_set_param = ttk.Button(self.frm_param_action)
        self.btn_set_param.configure(text='Set')
        self.btn_set_param.grid(column='1', row='0',padx='10', pady='10')
        self.btn_set_param.bind('<Button-1>', self.set_parameter_clicked, add='')

        self.btn_save_param = ttk.Button(self.frm_param_action)
        self.btn_save_param.configure(text='Save')
        self.btn_save_param.grid(column='3', row='0',padx='10', pady='10')
        self.btn_save_param.bind('<Button-1>', self.save_parameter_clicked, add='')
        
        self.ent_size=tk.Entry(self.frm_param_action)
        self.ent_size.configure(width='5')
        self.ent_size.grid(column='3', row='1',padx='10', pady='10')



        #MISC BUTTONS

        self.btn_initialize = ttk.Button(self.frm_param_action)
        self.btn_initialize.configure(text='Initialize\n  board')
        self.btn_initialize.grid(column='0', row='1',padx='10', pady='10')
        self.btn_initialize.bind('<Button-1>', self.initialize_clicked, add='')

        self.btn_vbias_off = ttk.Button(self.frm_param_action)
        self.btn_vbias_off.configure(text='V bias\n  OFF')
        self.btn_vbias_off.grid(column='1', row='1',padx='10', pady='10')
        self.btn_vbias_off.bind('<Button-1>', self.vbias_off_clicked, add='')



        #DAQ CONTROLS
        self.frm_daq_control = ttk.Labelframe(self.frm_data_acquisition)
        self.frm_daq_control.configure(height='200', text='Waveform acquisition', width='200')
        self.frm_daq_control.grid(row='1', column='1', pady='10')

        self.btn_start_daq = ttk.Button(self.frm_daq_control)
        self.btn_start_daq.configure(text='Start')
        self.btn_start_daq.pack(side='left',padx='5', pady='5')
        self.btn_start_daq.bind('<Button-1>', self.start_daq_clicked, add='')

        self.btn_stop_daq = ttk.Button(self.frm_daq_control)
        self.btn_stop_daq.configure(text='Stop')
        self.btn_stop_daq.pack(side='left',padx='5', pady='5')
        self.btn_stop_daq.bind('<Button-1>', self.stop_daq_clicked, add='')     


        self.frm_daq_binary = ttk.Labelframe(self.frm_daq_control)
        self.frm_daq_binary.configure(height='200', text='Binary file', width='200')
        self.frm_daq_binary.pack(side='left', padx='5', pady='5')

        self.btn_save_binary = ttk.Button(self.frm_daq_binary)
        self.btn_save_binary.configure(text='Save as')
        self.btn_save_binary.pack(padx='5', pady='5', side='left')
        self.btn_save_binary.bind('<Button-1>', self.save_binary_clicked, add='')

        self.ent_name_binary=tk.Entry(self.frm_daq_binary)
        self.ent_name_binary.configure(width='20')
        self.ent_name_binary.pack(side='right', padx='10')


        #MONITOR STUFF
        self.frm_daq_status = ttk.Labelframe(self.frm_data_acquisition)
        self.frm_daq_status.configure(text='Status')
        self.frm_daq_status.grid(row='2',pady="3",column='1', columnspan='2')


        self.lbl_temperature = tk.Label(self.frm_daq_status)
        self.lbl_temperature.configure(text='Temperature = 27 C')
        self.lbl_temperature.pack(side='left', padx='5', pady='5')

        self.lbl_daq_status = tk.Label(self.frm_daq_status, width=30)
        self.lbl_daq_status.configure(text='Board initialized!')
        self.lbl_daq_status.pack(side='left',padx='5', pady='5')

        self.lbl_wvb = tk.Label(self.frm_daq_status, width=6)
        self.lbl_wvb.configure(text='WVB 1')
        self.lbl_wvb.pack(side='left',padx='5', pady='5')
        self.activate_wvb1()

        #RATE monitor

        self.frm_rate_acquisition = ttk.Labelframe(self.frm_rate)
        self.frm_rate_acquisition.configure(text="Rate monitor")
        self.frm_rate_acquisition.grid(row='3', column='1', padx='10', pady='10', columnspan=3)        

        self.frm_rate_option = ttk.Labelframe(self.frm_rate_acquisition)
        self.frm_rate_option.configure(text="Monitor options")
        self.frm_rate_option.grid(row='0', column='0', padx='10', pady='10')

        self.lbl_delay = tk.Label(self.frm_rate_acquisition)
        self.lbl_delay.configure(text="Delay (s)")
        self.lbl_delay.grid(row='0', column='0', padx='5', pady='5')

        self.ent_delay = tk.Entry(self.frm_rate_acquisition)
        self.ent_delay.configure(width=3)
        self.ent_delay.grid(row='0', column='1', padx='5', pady='5')

        self.lbl_interval = tk.Label(self.frm_rate_acquisition)
        self.lbl_interval.configure(text="Interval (s)")
        self.lbl_interval.grid(row='1', column='0', padx='5', pady='5')

        self.ent_interval = tk.Entry(self.frm_rate_acquisition)
        self.ent_interval.configure(width=3)
        self.ent_interval.grid(row='1', column='1', padx='5', pady='5')

        self.print_screen_status = tk.IntVar()
        self.btn_print_screen = tk.Checkbutton(self.frm_rate_acquisition, variable=self.print_screen_status)
        self.btn_print_screen.configure(text = 'Print to screen')
        self.btn_print_screen.grid(row='2', column='0', padx='5', pady='5', columnspan='2')

        self.frm_rate_logfile = ttk.Labelframe(self.frm_rate_acquisition)
        self.frm_rate_logfile.configure(text="Logfile")
        self.frm_rate_logfile.grid(row='0', column='2', padx='10', pady='10', rowspan="2", columnspan='2')

        self.btn_open_logfile = tk.Button(self.frm_rate_logfile)
        self.btn_open_logfile.configure(text="Open Logfile")
        self.btn_open_logfile.pack(side='left', padx='5', pady='5')
        self.btn_open_logfile.bind('<Button-1>', self.open_logfile_clicked, add='')


        self.ent_logfile = tk.Entry(self.frm_rate_logfile)
        self.ent_logfile.configure(width=20)
        self.ent_logfile.pack(side='left', padx='5', pady='5')

        self.btn_start_monitor = tk.Button(self.frm_rate_acquisition)
        self.btn_start_monitor.configure(text="Start monitor")
        self.btn_start_monitor.grid(row='2', column='2', padx='5', pady='5')
        self.btn_start_monitor.bind('<Button-1>', self.start_monitor_clicked, add='')        
        
        self.btn_stop_monitor = tk.Button(self.frm_rate_acquisition)
        self.btn_stop_monitor.configure(text="Stop monitor")
        self.btn_stop_monitor.grid(row='2', column='3', padx='5', pady='5')
        self.btn_stop_monitor.bind('<Button-1>', self.stop_monitor_clicked, add='')



        #INPUT SETTING
        self.frm_analysis_setting = ttk.Labelframe(self.frm_plot)
        self.frm_analysis_setting.configure(text="Input setting")
        self.frm_analysis_setting.grid(row='0', column='0', padx='5', pady='5', rowspan="2")

        self.lbl_select_channel = tk.Label(self.frm_analysis_setting)
        self.lbl_select_channel.configure(text="Select channel to analyze")
        self.lbl_select_channel.grid(row='0', column='0', padx='5', pady='5', columnspan="2")

        self.channel_variable = tk.StringVar(root)
        self.channel_option = ["0","1","2","3","4","5","6","7","8","9","10","11","ALL"]
        self.channel_variable.set("ALL")

        self.btn_select_channel = tk.OptionMenu(self.frm_analysis_setting, self.channel_variable,*self.channel_option)
        self.btn_select_channel.grid(row='0', column='2', padx='5', pady='5')

        self.btn_open_analysis = ttk.Button(self.frm_analysis_setting)
        self.btn_open_analysis.configure(text='Open file')
        self.btn_open_analysis.grid(row='1', column='0', padx='5', pady='5')
        self.btn_open_analysis.bind('<Button-1>', self.open_analysis_clicked, add='')

        self.ent_analysis=tk.Entry(self.frm_analysis_setting)
        self.ent_analysis.configure(width="30")
        self.ent_analysis.grid(row='1', column='1', padx='5', pady='5', columnspan="3")

        self.ent_wf_skip=tk.Entry(self.frm_analysis_setting)
        self.ent_wf_skip.configure(width='4')
        self.ent_wf_skip.grid(row='2', column='1', padx='1', pady='5', columnspan="1")

        self.ent_wf_plot=tk.Entry(self.frm_analysis_setting)
        self.ent_wf_plot.configure(width='4')
        self.ent_wf_plot.grid(row='2', column='3', padx='1', pady='5', columnspan="1")

        self.lbl_wf_skip = tk.Label(self.frm_analysis_setting)
        self.lbl_wf_skip.configure(text="Waveform\n  to skip")
        self.lbl_wf_skip.grid(row='2', column='0', padx='5', pady='5', columnspan="1")

        self.lbl_wf_plot = tk.Label(self.frm_analysis_setting)
        self.lbl_wf_plot.configure(text="Waveform\n  to plot")
        self.lbl_wf_plot.grid(row='2', column='2', padx='5', pady='5', columnspan="1")

        self.trigger_variable=tk.IntVar()
        self.btn_trigger=tk.Checkbutton(self.frm_analysis_setting, variable=self.trigger_variable)
        self.btn_trigger.configure(relief='raised', text="Analyze waveform\n with maximum\n amplitude above (V)")
        self.btn_trigger.grid(row='3', column='0', padx='2', pady='5', columnspan="2")

        self.ent_trigger=tk.Entry(self.frm_analysis_setting)
        self.ent_trigger.configure(width='4')
        self.ent_trigger.grid(row='3', column='2', padx='2', pady='5', columnspan="1")



        #PLOT SETTING
        self.frm_plot_setting = ttk.Labelframe(self.frm_plot)
        self.frm_plot_setting.configure(text="Plot options")
        self.frm_plot_setting.grid(row='0', column='1', padx='5', pady='5')

        self.overlap_variable=tk.IntVar()
        self.btn_overlap=tk.Checkbutton(self.frm_plot_setting, variable=self.overlap_variable)
        self.btn_overlap.configure(relief='raised', text="Overlap")
        self.btn_overlap.grid(row='0', column='2', padx='5', pady='5')


        self.btn_plot = tk.Button(self.frm_plot_setting)
        self.btn_plot.configure(text="Plot")
        self.btn_plot.grid(row='1', column='2', padx='5', pady='5')
        self.btn_plot.bind('<Button-1>', self.plot_clicked, add='')        

        #HISTO SETTING
        self.frm_histo_setting = ttk.Labelframe(self.frm_plot)
        self.frm_histo_setting.configure(text="Histogram options")
        self.frm_histo_setting.grid(row='1', column='1', padx='5', pady='5')


        self.lbl_bin = tk.Label(self.frm_histo_setting)
        self.lbl_bin.configure(text="Bins")
        self.lbl_bin.grid(row='1', column='0', padx='5', pady='5', columnspan="1")

        self.ent_bin=tk.Entry(self.frm_histo_setting)
        self.ent_bin.configure(width='4')
        self.ent_bin.grid(row='1', column='1', padx='2', pady='2', columnspan="1")




        self.histo_type_variable = tk.StringVar(root)
        self.histo_type = ["Maximum", "Duration"]
        self.histo_type_variable.set("Maximum")

        self.btn_histo_type = tk.OptionMenu(self.frm_histo_setting, self.histo_type_variable,*self.histo_type)
        self.btn_histo_type.grid(row='2', column='0', padx='5', pady='5')


        self.btn_histo = tk.Button(self.frm_histo_setting)
        self.btn_histo.configure(text="Histogram")
        self.btn_histo.grid(row='2', column='1', padx='5', pady='5')
        self.btn_histo.bind('<Button-1>', self.histo_clicked, add='')   

        if getattr(args, 'tcc')==True:
            self.frm_tcc = ttk.Frame(self.notebook)
            self.frm_tcc.pack(fill='both', expand=True)
            self.notebook.add(self.frm_tcc, text='TCC mode')
            self.notebook.select(4)


            self.btn_tcc_start = ttk.Button(self.frm_tcc)
            self.btn_tcc_start.configure(text="Start TCC acquisition")
            self.btn_tcc_start.grid(column="0", row="3", pady="1", padx="1")
            self.btn_tcc_start.bind('<Button-1>', self.start_tcc_clicked, add='')


            self.btn_tcc_stop = ttk.Button(self.frm_tcc)
            self.btn_tcc_stop.configure(text="Stop M acquisition")
            self.btn_tcc_stop.grid(column="1", row="3", pady="1", padx="1")
            self.btn_tcc_stop.bind('<Button-1>', self.stop_tcc_clicked, add='')

            self.lbl_tcc_near_bkg=tk.Label(self.frm_tcc)
            self.lbl_tcc_near_bkg.configure(text="Near Background")
            self.lbl_tcc_near_bkg.grid(row="0",column="0",pady="1", padx="1")


            self.ent_tcc_near_bkg=tk.Entry(self.frm_tcc)
            self.ent_tcc_near_bkg.configure(width='3')
            self.ent_tcc_near_bkg.grid(column="1", row="0",pady="1", padx="1" )

            self.tcc_mode_var=tk.StringVar(root)
            self.tcc_mode_option= ["Dynamic", "Fixed"]
            self.tcc_mode_var.set("Dynamic")
            
            self.btn_tcc_mode= tk.OptionMenu(self.frm_tcc, self.tcc_mode_var,*self.tcc_mode_option)
            self.btn_tcc_mode.grid(row="1", column="1", padx='1', pady='1')
           
            self.lbl_tcc_mode=tk.Label(self.frm_tcc)
            self.lbl_tcc_mode.configure(text="Visual Mode")
            self.lbl_tcc_mode.grid(row="1",column="0",pady="1", padx="1")


            self.tcc_fig = Figure(figsize=(5, 3), dpi=100)
            self.tcc_ax = self.tcc_fig.add_subplot(111)
    
            #self.monkey_fig,self.monkey_ax= plt.subplots(figsize=(5, 3), dpi=100)
            
            #self.tcc_ax.bar(["0","1","2","3","4","5","6","7","8","9","10","11"],[0,0,0,0,0,0,0,0,0,0,0,0])
            #self.tcc_ax.plot([[0,0,0,0,0,0,0,0,0,0,0,0],[1,2,3,4,5,6,7,8,9,10,11,12]])

            self.btn_m_bkg = ttk.Button(self.frm_tcc)
            self.btn_m_bkg.configure(text="Background")
            self.btn_m_bkg.grid(column="0", row="2", pady="1", padx="1")
            self.btn_m_bkg.bind('<Button-1>', self.bkg_monkey_clicked, add='')
            
            self.lbl_m_bkg=tk.Label(self.frm_tcc)
            self.lbl_m_bkg.configure(text=" ")
            self.lbl_m_bkg.grid(row="2",column="1",pady="1", padx="1")

            
            self.canvasTcc = FigureCanvasTkAgg(self.tcc_fig, master=self.frm_tcc)
            self.canvasTcc.draw()
            self.canvasTcc.get_tk_widget().grid(row="0",column="3", rowspan="4")
            
            self.wvb_active=3
            
            print(v_to_adc_all[3])

        if getattr(args, 'monkey')==True:
            self.frm_monkey = ttk.Frame(self.notebook)
            self.frm_monkey.pack(fill='both', expand=True)
            self.notebook.add(self.frm_monkey, text='M mode')
            self.notebook.select(4)


            self.btn_m_start = ttk.Button(self.frm_monkey)
            self.btn_m_start.configure(text="Start M acquisition")
            self.btn_m_start.grid(column="0", row="3", pady="1", padx="1")
            self.btn_m_start.bind('<Button-1>', self.start_monkey_clicked, add='')


            self.btn_m_stop = ttk.Button(self.frm_monkey)
            self.btn_m_stop.configure(text="Stop M acquisition")
            self.btn_m_stop.grid(column="1", row="3", pady="1", padx="1")
            self.btn_m_stop.bind('<Button-1>', self.stop_monkey_clicked, add='')

            self.lbl_m_near_bkg=tk.Label(self.frm_monkey)
            self.lbl_m_near_bkg.configure(text="Near Background")
            self.lbl_m_near_bkg.grid(row="0",column="0",pady="1", padx="1")


            self.ent_m_near_bkg=tk.Entry(self.frm_monkey)
            self.ent_m_near_bkg.configure(width='3')
            self.ent_m_near_bkg.grid(column="1", row="0",pady="1", padx="1" )

            self.m_mode_var=tk.StringVar(root)
            self.m_mode_option= ["Dynamic", "Fixed"]
            self.m_mode_var.set("Dynamic")
            
            self.btn_m_mode= tk.OptionMenu(self.frm_monkey, self.m_mode_var,*self.m_mode_option)
            self.btn_m_mode.grid(row="1", column="1", padx='1', pady='1')
           
            self.lbl_m_mode=tk.Label(self.frm_monkey)
            self.lbl_m_mode.configure(text="Visual Mode")
            self.lbl_m_mode.grid(row="1",column="0",pady="1", padx="1")


            self.monkey_fig = Figure(figsize=(5, 3), dpi=100)
            self.monkey_ax = self.monkey_fig.add_subplot(111)
    
            #self.monkey_fig,self.monkey_ax= plt.subplots(figsize=(5, 3), dpi=100)
            
            self.monkey_ax.bar(["0","1","2","3","4","5","6","7","8","9","10","11"],[0,0,0,0,0,0,0,0,0,0,0,0])

            self.btn_m_bkg = ttk.Button(self.frm_monkey)
            self.btn_m_bkg.configure(text="Background")
            self.btn_m_bkg.grid(column="0", row="2", pady="1", padx="1")
            self.btn_m_bkg.bind('<Button-1>', self.bkg_monkey_clicked, add='')
            
            self.lbl_m_bkg=tk.Label(self.frm_monkey)
            self.lbl_m_bkg.configure(text=" ")
            self.lbl_m_bkg.grid(row="2",column="1",pady="1", padx="1")

            
            self.canvas = FigureCanvasTkAgg(self.monkey_fig, master=self.frm_monkey)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row="0",column="3", rowspan="4")
            
            self.wvb_active=3
            
            print(v_to_adc_all[3])

        def t_monitor():
            global t_board
        
            interval=120
            time.sleep(2)
            e_monitor.set()


            while(e_monitor.is_set()):
                e_timer.clear()
                stdin, stdout, stderr = client.exec_command("""bash get_param.sh -N 2 """)
                parameter=stdout.read()
                print("DEBUGT: ",parameter,parameter[16:18])
#                t_board=float(parameter[16:18])
                t_board=25.2
                #da usare con waveboard con temperatura funzionante
                #_board=float(parameter[16:21])
            
                if e_log.is_set():
                    with open("logfile_tmp.txt", "a") as f:
                        f.write(str(parameter)+"\n")
                    print("Parameter saved to logfile")
                

                if e_acquisition.is_set():

                    channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

                    #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_set_hv.sh -N """+ channel_string+ """ -V """+v_bias_string+""" ' """)
                    #print("V bias updated")

                self.lbl_temperature.configure(text="Temperature = "+ str(t_board) +" C")
                #print("Temperature field updated")
                abortable_sleep(interval,e_timer)

        #INITIALIZE STARTUP PARAMETERS
        if getattr(args, 'dry')==False:

            self.initialize_board()
            thread_monitor = threading.Thread(target=t_monitor)
            thread_monitor.deamon = True
            thread_monitor.start()


    def start_tcc_clicked(self,event=None):
        print("tcc start")
        
        #for ax in self.monkey_fig.axes:
        #    ax.clear()
         #   if ax != self.monkey_ax:
        #        ax.remove()
        
        self.ent_delay.delete(0,'end')
        self.ent_delay.insert(0,"0")
        self.ent_interval.delete(0,'end')
        self.ent_interval.insert(0,"1")

        data_queue = Queue()  # Queue to pass data from the file-reading thread to the main thread

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        self.daq_type="rate"

        ch_list=re.findall(r'\d+', channel_string)

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        date_str = current_datetime.strftime("%Y-%m-%d")
        time_str = current_datetime.strftime("%H-%M-%S")

        # Create the logfile name with date and time
        self.tcc_filename = f"logfile_{date_str}_{time_str}.txt"
                
        with open(self.tcc_filename, "w") as f:
            f.write(str(datetime.datetime.now())+"\n")

        self.ent_logfile.delete(0,'end')
        self.ent_logfile.insert(0,self.tcc_filename)

        if getattr(args, 'dry')==False:

            self.thread_start = threading.Thread(target=self.t_start_daq)
            self.thread_start.deamon = True
            self.thread_start.start()

        e_timer.set()
        e_acquisition.set()

        def write_to_file_thread(logfile):
            while e_acquisition.is_set():
                # Generate Nchan random numbers
                random_numbers = [random.randint(1, 400) for _ in range(len(ch_list))]
                print(random_numbers)

                with open(self.tcc_filename, "a") as file:
                    # Write the random numbers to the logfile with timestamp and label
                    current_datetime = datetime.datetime.now()
                    timestamp = current_datetime.second + current_datetime.minute * 60 + current_datetime.hour *60*60+ current_datetime.day*60*60*24
                    for i, num in enumerate(random_numbers):
                        file.write(f"ch {ch_list[i]}:\t {num}Hz {timestamp*10}\n")

                time.sleep(3)  # Wait for 3 seconds


        def read_file_and_update_queue_thread(logfile):
            old_data=[0,0,0,0,0,0,0,0,0,0,0,0]

            while e_acquisition.is_set():
                with open(logfile, "r") as file:
                    lines = file.readlines()[1:]

                # Parse the numbers from the logfile
                new_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                print("New Data PREE\n", new_data)
                for line in lines:
                        channel = int(re.findall(r'([\d.]+)\D+', line)[0])
                        value = float(re.findall(r'([\d.]+)\D+', line)[1])
                        #timestamp = float(re.findall(r'([\d.]+)\D+', line)[2])
                        new_data[channel] = value
                print("New Data POST\n", new_data)

                if new_data!=old_data:
                    # Put the new data in the queue
                    data_queue.put(new_data)
                    old_data=new_data


                else:
                    data_queue.put( [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                print("CODA\n",data_queue.qsize())
                time.sleep(1)  # Wait for a short interval

        def update_graph():
            t=0
            stripLength=20
            megaVector=[]
            channelLabels=["0","1","2","3","4","5","6","7","8","9","10","11"]
            data_chx12 = np.zeros((12, 12))
            #image=self.tcc_ax.imshow(data_chx12, cmap='viridis', origin='lower', aspect='auto', extent=(0, 1, 0, 6))
            image=self.tcc_ax.plot(megaVector[-stripLength:])
            #image=self.tcc_ax.plot([[0,0,0,0,0,0,0,0,0,0,0,0],[5,5,5,5,5,5,5,5,5,5,5,5]])
            #cbar=plt.colorbar(image,ax=self.monkey_ax)
            while e_acquisition.is_set():

                # Check if there is new data in the queue
                if not data_queue.empty():
                    data = data_queue.get()
                    print("Presi Dati ", data)
                    #megaVector.append(data)
                    megaVector.insert(t,data)
                    print("MegaVector:\t",megaVector)
                    self.tcc_ax.clear()  # Clear the previous plot
                    channels = ch_list
                    if self.tcc_mode_var.get() == "Dynamic":

                        #self.monkey_ax.bar(["0","1","2","3","4","5","6","7","8","9","10","11"],data)
                        print("Dyn:\t",data)
                        data_chx12[:, t%12] = data
                        
#                        image=self.tcc_ax.imshow(data_chx12,cmap="viridis"    , origin='lower', aspect='auto', extent=(0, 11, 0, 11))
                        image=self.tcc_ax.plot(megaVector[-stripLength:], label=channelLabels)
                        self.tcc_ax.legend(loc="upper left", fontsize="x-small",ncol=2)
                        self.tcc_ax.set_title("WIDMApp Real Time TCC")
                        #image=self.tcc_ax.plot([[0,0,0,0,0,0,0,0,0,0,0,0],[12,11,10,9,8,7,6,5,4,3,2,1]])
                        #cbar.mappable.set_clim(vmin=0,vmax=data_chx12.max()) #this works
                        #cbar.draw_all()
                        #self.tcc_ax.text(0.5,11.2,"max="+str(data_chx12.max()), bbox={'facecolor':'white', 'pad':2})
                        self.tcc_ax.text(0.5,100,"WIDMApp0")
                        if t%12==11:
                            data_chx12 = np.zeros((12, 12))


                        t=t+1
                    elif self.tcc_mode_var.get() == "Fixed":
                        near_bkg=int(self.ent_m_near_bkg.get())
                        data_chx12[:, -t%12] = data
                        image=self.tcc_ax.imshow(np.array(data_chx12)/(near_bkg*4), cmap='viridis', origin='lower', aspect='auto', extent=(0, 1, 0, 6))
                        t=t+1

                    self.canvasTcc.draw()
                    print("empty")

            time.sleep(0.2)

        if getattr(args, 'dry')==True:
            write_thread = threading.Thread(target=write_to_file_thread, args=(self.ent_logfile.get(),))
            write_thread.start()

        read_thread = threading.Thread(target=read_file_and_update_queue_thread, args=(self.ent_logfile.get(),))
        read_thread.start()

        graph_thread = threading.Thread(target=update_graph)
        graph_thread.start()


    def stop_tcc_clicked(self,event=None):

        print("tcc stop")

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

        e_log.clear()
        e_acquisition.clear()

        if getattr(args, 'dry')==False:

            print("Stopping acquisition...")
            stdin, stdout, stderr = client.exec_command("""bash daq_run_stop.sh -N """+channel_string)
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_stop.sh -N """+channel_string+"'")
            time.sleep(1)
            
            stdin, stdout, stderr = client.exec_command("""killall DaqReadTcp""")
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'killall DaqReadTcp'""")
            time.sleep(1)
            if self.arch=="arm":
                os.system("killall RateParser_arm")     
            elif self.arch=="x86":
                os.system("killall RateParser_x86") 
  
   
    def start_monkey_clicked(self,event=None):
        print("simia start")
        
        #for ax in self.monkey_fig.axes:
        #    ax.clear()
         #   if ax != self.monkey_ax:
        #        ax.remove()
        
        self.ent_delay.delete(0,'end')
        self.ent_delay.insert(0,"0")
        self.ent_interval.delete(0,'end')
        self.ent_interval.insert(0,"1")

        data_queue = Queue()  # Queue to pass data from the file-reading thread to the main thread

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        self.daq_type="rate"

        ch_list=re.findall(r'\d+', channel_string)

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        date_str = current_datetime.strftime("%Y-%m-%d")
        time_str = current_datetime.strftime("%H-%M-%S")

        # Create the logfile name with date and time
        self.monkey_filename = f"logfile_{date_str}_{time_str}.txt"
                
        with open(self.monkey_filename, "w") as f:
            f.write(str(datetime.datetime.now())+"\n")

        self.ent_logfile.delete(0,'end')
        self.ent_logfile.insert(0,self.monkey_filename)

        if getattr(args, 'dry')==False:

            self.thread_start = threading.Thread(target=self.t_start_daq)
            self.thread_start.deamon = True
            self.thread_start.start()

        e_timer.set()
        e_acquisition.set()

        def write_to_file_thread(logfile):
            while e_acquisition.is_set():
                # Generate six random numbers
                random_numbers = [random.randint(1, 400) for _ in range(len(ch_list))]
                print(random_numbers)

                with open(self.monkey_filename, "a") as file:
                    # Write the random numbers to the logfile with timestamp and label
                    current_datetime = datetime.datetime.now()
                    timestamp = current_datetime.second + current_datetime.minute * 60 + current_datetime.hour *60*60+ current_datetime.day*60*60*24
                    for i, num in enumerate(random_numbers):
                        file.write(f"ch {ch_list[i]}:\t {num}Hz {timestamp*10}\n")

                time.sleep(3)  # Wait for one second


        def read_file_and_update_queue_thread(logfile):
            old_data=[0,0,0,0,0,0,0,0,0,0,0,0]

            while e_acquisition.is_set():
                with open(logfile, "r") as file:
                    lines = file.readlines()[1:]

                # Parse the numbers from the logfile
                new_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                for line in lines:
                        channel = int(re.findall(r'([\d.]+)\D+', line)[0])
                        value = float(re.findall(r'([\d.]+)\D+', line)[1])
                        #timestamp = float(re.findall(r'([\d.]+)\D+', line)[2])
                        new_data[channel] = value

                if new_data!=old_data:
                    # Put the new data in the queue
                    data_queue.put(new_data)
                    old_data=new_data

                else:
                    data_queue.put( [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                time.sleep(1)  # Wait for a short interval

        def update_graph():
            t=0
            data_chx12 = np.zeros((12, 12))
            image=self.monkey_ax.imshow(data_chx12, cmap='viridis', origin='lower', aspect='auto', extent=(0, 1, 0, 6))
            #cbar=plt.colorbar(image,ax=self.monkey_ax)
                
            while e_acquisition.is_set():

                # Check if there is new data in the queue
                if not data_queue.empty():
                    data = data_queue.get()
                    
                    self.monkey_ax.clear()  # Clear the previous plot
                    channels = ch_list
                    if self.m_mode_var.get() == "Dynamic":

                        #self.monkey_ax.bar(["0","1","2","3","4","5","6","7","8","9","10","11"],data)
                        print(data)
                        data_chx12[:, t%12] = data
                        image=self.monkey_ax.imshow(data_chx12,cmap="viridis"    , origin='lower', aspect='auto', extent=(0, 11, 0, 11))
                        #cbar.mappable.set_clim(vmin=0,vmax=data_chx12.max()) #this works
                        #cbar.draw_all()
                        self.monkey_ax.text(0.5,11.2,"max="+str(data_chx12.max()), bbox={'facecolor':'white', 'pad':2})
                        if t%12==11:
                            data_chx12 = np.zeros((12, 12))


                        t=t+1
                    elif self.m_mode_var.get() == "Fixed":
                        near_bkg=int(self.ent_m_near_bkg.get())
                        data_chx12[:, -t%12] = data
                        image=self.monkey_ax.imshow(np.array(data_chx12)/(near_bkg*4), cmap='viridis', origin='lower', aspect='auto', extent=(0, 1, 0, 6))
                        t=t+1

                    self.canvas.draw()
                    print("empty")

            time.sleep(0.2)

        if getattr(args, 'dry')==True:
            write_thread = threading.Thread(target=write_to_file_thread, args=(self.ent_logfile.get(),))
            write_thread.start()

        read_thread = threading.Thread(target=read_file_and_update_queue_thread, args=(self.ent_logfile.get(),))
        read_thread.start()

        graph_thread = threading.Thread(target=update_graph)
        graph_thread.start()


    def bkg_monkey_clicked(self, event=None):
        print("Initializing background measurement")

        self.ent_delay.delete(0,'end')
        self.ent_delay.insert(0,"0")
        self.ent_interval.delete(0,'end')
        self.ent_interval.insert(0,"10")
        
        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        self.daq_type="rate"
        
        # Get the current date and time
        current_datetime = datetime.datetime.now()
        date_str = current_datetime.strftime("%Y-%m-%d")
        time_str = current_datetime.strftime("%H-%M-%S")

        # Create the logfile name with date and time
        self.monkey_bkg_filename = f"bkg_{date_str}_{time_str}.txt"
                
        with open(self.monkey_bkg_filename, "w") as f:
            f.write("background "+str(datetime.datetime.now())+"\n")

        self.ent_logfile.delete(0,'end')
        self.ent_logfile.insert(0,self.monkey_bkg_filename)
        

        self.thread_start = threading.Thread(target=self.t_start_daq)
        self.thread_start.deamon = True
        self.thread_start.start()

        e_timer.set()
        e_acquisition.set()

        def read_background_thread(bkg_file):
            
            with open(bkg_file, "r") as f:
                l=len(f.readlines())
                
            while l==1:
                time.sleep(1)
                with open(bkg_file, "r") as f:
                    l=len(f.readlines())
                
            
            channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

            e_log.clear()
            e_acquisition.clear()

            print("Stopping acquisition...")
            stdin, stdout, stderr = client.exec_command("""bash daq_run_stop.sh -N """+channel_string)
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_stop.sh -N """+channel_string+"'")
            time.sleep(1)
            
            stdin, stdout, stderr = client.exec_command("""killall DaqReadTcp""")
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'killall DaqReadTcp'""")
            time.sleep(1)
            if self.arch=="arm":
                os.system("killall RateParser_arm")     
            elif self.arch=="x86":
                os.system("killall RateParser_x86")        
 
            with open(bkg_file, "r") as file:
                lines = file.readlines()[1:]

            # Parse the numbers from the logfile
            new_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            for line in lines:
                channel = int(re.findall(r'([\d.]+)\D+', line)[0])
                value = float(re.findall(r'([\d.]+)\D+', line)[1])
                new_data[channel] = value            
            
            channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
            ch_list=re.findall(r'\d+', channel_string)
            print(new_data)
            bkg_string=""
            print(ch_list)
            for ch in sorted([int(i) for i in ch_list]):
                bkg_string= bkg_string+str(new_data[int(ch)])+" "
                print(new_data[int(ch)])
                
            self.lbl_m_bkg.configure(text=bkg_string)

        bkg_thread = threading.Thread(target=read_background_thread, args=(self.ent_logfile.get(),))
        bkg_thread.start()
            



    def stop_monkey_clicked(self,event=None):

        print("simia stop")

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

        e_log.clear()
        e_acquisition.clear()

        if getattr(args, 'dry')==False:

            print("Stopping acquisition...")
            stdin, stdout, stderr = client.exec_command("""bash daq_run_stop.sh -N """+channel_string)
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_stop.sh -N """+channel_string+"'")
            time.sleep(1)
            
            stdin, stdout, stderr = client.exec_command("""killall DaqReadTcp""")
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ 'killall DaqReadTcp'""")
            time.sleep(1)
            if self.arch=="arm":
                os.system("killall RateParser_arm")     
            elif self.arch=="x86":
                os.system("killall RateParser_x86") 
    
    def start_calibration_clicked(self, event=None):
        
        print("ciaoooo")
        
        self.cal_ch = np.array([])
                
        for ch in range(12):
            print(ch)
            if self.cal_channel_variable[ch].get() != "//" and self.cal_mode_variable[ch].get() != "V":
                np.append(self.cal_ch, self.cal_channel_variable[ch].get())
                
                print(self.cal_ch)

    def open_logfile_clicked(self, event=None):
        name = tk.filedialog.asksaveasfilename(filetypes=(("Rate Logfile", "*.txt"),),title="Choose a file")
        self.ent_logfile.delete(0,'end')
        self.ent_logfile.insert(0,name)

    def initialize_board(self):
        global wvb_active
        
        if getattr(args, 'monkey')==True:
            with open(getattr(args, 'parameter')) as f:
                param=json.load(f)
            wvb_active=3

        else:
            with open("startup_parameter.json") as f:
                param=json.load(f)

        for ch in np.arange(0,12):
            
            self.ent_start[ch].delete(0,'end')
            self.ent_stop[ch].delete(0,'end')
            self.ent_lead[ch].delete(0,'end')
            self.ent_tail[ch].delete(0,'end')
            self.ent_vbias[ch].delete(0,'end')
            
            self.ent_start[ch].insert(0,str(param["start_th"][ch]))
            self.ent_stop[ch].insert(0,str(param["stop_th"][ch]))
            self.ent_lead[ch].insert(0,str(param["lead"][ch]))
            self.ent_tail[ch].insert(0,str(param["tail"][ch]))
            self.ent_vbias[ch].insert(0,str(param["v_bias"][ch]))

            if str(ch) in param["active_ch"]:
                self.btn_ch[ch].select()



        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        
        
        if param["gain"]=="high":
            print("Setting gain to 20...")
            stdin, stdout, stderr = client.exec_command("""./M4Comm -s "\$gsha#" &""")
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ './M4Comm -s "\$gsha#" ' &""")

        if param["gain"]=="low":
            print("Setting gain to 2...")
            stdin, stdout, stderr = client.exec_command("""./M4Comm -s "\$gsla#" & """)
            print(stdout.readlines())
            #os.system("""ssh """ + username + """@""" + ip_address + """ './M4Comm -s "\$gsla#" ' &""")

        print("Initializing board...")
        stdin, stdout, stderr = client.exec_command("date " + date_format)
        print(stdout.readlines())
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'date """ + date_format  + "'")
        
        stdin, stdout, stderr = client.exec_command("./SetTimeReg -t l")
        print(stdout.readlines())
        
        #os.system("""ssh """ + username + """@""" + ip_address + """ './SetTimeReg -t l'""")
        
        stdin, stdout, stderr = client.exec_command("""bash daq_set_iob_delay.sh -N "{0..11}" -F """+ iob_delay)
        print(stdout.readlines())
        
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_set_iob_delay.sh -N "{0..11}" -F """ + iob_delay+ """' """)
        
        print("Board initialized")
        
        print("Setting channels parametes...")

        stdin, stdout, stderr = client.exec_command("""bash daq_run_launch.sh -j -N """+channel_string+""" -S """+start_th_string+""" -P """+stop_th_string+ """ -L """ + lead_string + """ -T """+ tail_string)
        print(stdout.readlines())
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_launch.sh -j -N """+channel_string+""" -S """+start_th_string+""" -P """+stop_th_string+ """ -L """ + lead_string + """ -T """+ tail_string +""" ' """)

    def save_binary_clicked(self, event=None):

        bin_filename=asksaveasfilename(filetypes=(("Binary file", "*.bin"),),title="Open binary file")
        
        if bin_filename!="()":
            self.ent_name_binary.delete(0,'end')
            self.ent_name_binary.insert(0,str(bin_filename))
        else:
            pass

    def initialize_clicked(self, event=None):
        self.initialize_board()
    
    def load_parameter_clicked(self, event=None):
        name = tk.filedialog.askopenfilename(filetypes=(("Json File", "*.json"),),title="Choose a file")
        if name!=() and name != '':
            with open(name) as f:
                param = json.load(f)


            for ch in np.arange(0,12):
                self.ent_start[ch].delete(0,'end')
                self.ent_stop[ch].delete(0,'end')
                self.ent_lead[ch].delete(0,'end')
                self.ent_tail[ch].delete(0,'end')
                self.ent_vbias[ch].delete(0,'end')

                self.ent_start[ch].insert(0,str(param["start_th"][ch]))
                self.ent_stop[ch].insert(0,str(param["stop_th"][ch]))
                self.ent_lead[ch].insert(0,str(param["lead"][ch]))
                self.ent_tail[ch].insert(0,str(param["tail"][ch]))
                self.ent_vbias[ch].insert(0,str(param["v_bias"][ch]))

                self.btn_ch[ch].deselect()
                if str(ch) in param["active_ch"]:
                    self.btn_ch[ch].select()

    def t_start_daq(self):  
        daq_read_tcp_thread = threading.Thread(target=t_daq_read_tcp)
        daq_read_tcp_thread.deamon = True
        daq_read_tcp_thread.start()

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

        print(self.daq_type)
        time.sleep(1)

        if self.daq_type == "waveform" :
            os.system("nc 192.168.137.30 5000 > " + str(self.ent_name_binary.get()) + " &")


            time.sleep(1)
            
                
            stdin, stdout, stderr = client.exec_command("bash daq_run_launch.sh -N "+channel_string+" -S "+start_th_string+" -P "+stop_th_string+" -L " + lead_string + " -T "+ tail_string)
            print ( stdout.readlines())
            
            
            #print("setting window lenght")
            #for ch in re.findall(r'\d+',channel_string):
                #stdin, stdout, stderr = client.exec_command("./SendCmd -s 0x03 -c " +str(ch)+" -a "+ str(hex(int(self.ent_tail[int(ch)].get()))))
                #stdin, stdout, stderr = client.exec_command("./SendCmd -s 0x06 -c " +str(ch)+" -a "+ str(hex(int(self.ent_lead[int(ch)].get()))))

                #print("SendCmd -s 0x03 -c " +str(ch)+" -a "+ str(hex(int(self.ent_tail[int(ch)].get())))) 
                #print("SendCmd -s 0x06 -c " +str(ch)+" -a "+ str(hex(int(self.ent_lead[int(ch)].get())))) 
          


        if self.daq_type == "rate":

            name=self.ent_logfile.get()
            print(self.print_screen_status)

            if self.print_screen_status.get():
                if self.arch=="arm":
                    os.system("nc 192.168.137.30 5000 | ./RateParser_arm -a -t "+str(self.ent_interval.get())+" -d " +self.ent_delay.get()+ " -c 13 &")
                elif self.arch=="x86":
                    os.system("nc 192.168.137.30 5000 | ./RateParser_x86 -a -t "+str(self.ent_interval.get())+" -d " +self.ent_delay.get()+ " -c 13 &")

            if not self.print_screen_status.get():
                if self.arch=="arm":
                    os.system("nc 192.168.137.30 5000 | ./RateParser_arm -a -t "+str(self.ent_interval.get())+" -d " +self.ent_delay.get()+ " >> "+name +"&")

                if self.arch=="x86":
                    os.system("nc 192.168.137.30 5000 | ./RateParser_x86 -a -t "+str(self.ent_interval.get())+" -d " +self.ent_delay.get()+ " >> "+name +"&")



            time.sleep(1)
            
            
                
            stdin, stdout, stderr = client.exec_command("bash daq_run_launch.sh -N "+channel_string+" -S "+start_th_string+" -P "+stop_th_string+" -L " + lead_string + " -T "+ tail_string)
            print ( stdout.readlines())
            
            print("setting window lenght")
            for ch in re.findall(r'\d+',channel_string):
                stdin, stdout, stderr = client.exec_command("./SendCmd -s 0x03 -c " +str(ch)+" -a "+ str(hex(int(self.ent_tail[int(ch)].get()))))
                print(stdout.readlines())
                #print("SendCmd -s 0x03 -c " +str(ch)+" -a "+ str(hex(int(self.ent_tail[int(ch)].get())))) 

    def start_daq_clicked(self, event=None):
        
        name = self.ent_name_binary.get()
        
        os.system("touch "+ str(self.ent_name_binary.get()))

        if name != "":
            self.lbl_daq_status.configure(text='Starting waveform acquisition')

            channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()


            self.daq_type="waveform"
            
            #stdin, stdout, stderr = client.exec_command("cat WaveBrd_OsciMode_FixedWindow.bit > /dev/xdevcfg")

        
            self.thread_start = threading.Thread(target=self.t_start_daq)
            self.thread_start.deamon = True
            self.thread_start.start()

            e_timer.set()
            e_acquisition.set()
            

            def t_size():

                while(e_acquisition.is_set()):
                    
                    filesize = subprocess.check_output("du -h "+ str(name), shell=True)[:-len(name)+1]
                    self.lbl_daq_status.configure(text=str(filesize))
                    
                    if self.ent_size.get() != "":
                        
                        if "K" in str(filesize):
                            f=1
                        elif "M" in str(filesize):
                            f=1000
                            
                        filesize_true=f*float(re.findall(r"[-+]?(?:\d*\.*\d+)",str(filesize))[0])
                        
                        size_t=self.ent_size.get()
                        
                        if "K" in str(size_t):
                            f=1
                        elif "M" in str(size_t):
                            f=1000
                            
                        size_t=f*float(re.findall(r"[-+]?(?:\d*\.*\d+)",str(size_t) )[0])
                        
                        
                        if filesize_true >= size_t:
                            self.stop_daq_clicked()
                        
                    time.sleep(0.2) 

            self.thread_size = threading.Thread(target=t_size)
            self.thread_size.deamon = True
            self.thread_size.start()
        
        else: 
            print("Error: insert file name")
            self.lbl_daq_status.configure(text='Error: insert file name')

    def vbias_off_clicked(self, event=None):

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_disable_hv.sh -N """+channel_string+""" ' &""")
        stdin, stdout, stderr = client.exec_command("""bash daq_disable_hv.sh -N """+channel_string)
       # print(stdout.readlines())

    def stop_daq_clicked(self, event=None):

        e_acquisition.clear()

        name= self.ent_name_binary.get()
        
        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()


        time.sleep(2)

        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_stop.sh -N """+channel_string+" '")
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'killall DaqReadTcp'""")
        stdin, stdout, stderr = client.exec_command("""bash daq_run_stop.sh -N """+channel_string)
        print(stdout.readlines())

        stdin, stdout, stderr = client.exec_command("""killall DaqReadTcp""")
        print(stdout.readlines())


        self.lbl_daq_status.configure(text="Board ready!")

    def set_parameter_clicked(self, event=None):
        print("DBG1")

        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        print("DBG2")


        stdin, stdout, stderr = client.exec_command("""bash daq_run_launch.sh -j -N """+channel_string+""" -S """+start_th_string+""" -P """+stop_th_string+ """ -L """ + lead_string + """ -T """+ tail_string )
        print("DBG3")
        print(stdout.readlines())
        print("DBG4")
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_launch.sh -j -N """+channel_string+""" -S """+start_th_string+""" -P """+stop_th_string+ """ -L """ + lead_string + """ -T """+ tail_string +""" ' """)
        print("Setting HV values...")
        stdin, stdout, stderr = client.exec_command("""bash daq_set_hv.sh -N """+channel_string+""" -V """+v_bias_string)
        print("DBG5")
#        print(stdout.readlines())
        print("DBG6")
        #print("""bash daq_set_hv.sh -N """+channel_string+""" -V """+v_bias_string)
        print("Finito di settare HV")
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_set_hv.sh -N """+channel_string+""" -V """+v_bias_string+""" ' """)

    def save_parameter_clicked(self, event=None):
        param={"start_th":[],"stop_th":[],"v_bias":[],"lead":[],"tail":[], "active_ch":[]}
        
        for ch in np.arange(0,12):
            param["start_th"].append(self.ent_start[ch].get())
            param["stop_th"].append(self.ent_stop[ch].get())
            param["lead"].append(self.ent_lead[ch].get())
            param["tail"].append(self.ent_tail[ch].get())
            param["v_bias"].append(self.ent_vbias[ch].get())

            if self.ch_status[ch].get():
                param["active_ch"].append(str(ch))

        name = tk.filedialog.asksaveasfilename(filetypes=(("Json File", "*.json"),),title="Choose a file")

        if name!=() and name != '' :
            with open(name, 'w') as f:
                json.dump(param, f)    

    def get_parameter_string(self):
        
        global polarity
        
        start_th_mv={}
        start_th={}
        v_bias = {} 

        stop_th_mv={}
        stop_th={}

        lead={}
        tail={}

        channel = {}

        v_bias_string = '"'
        channel_string = '"'
        lead_string = '"'
        tail_string = '"'
        start_th_string = '"'
        stop_th_string = '"'

        for ch in np.arange(0,12):

            if self.ch_status[ch].get():

                start_th_mv[ch] = self.ent_start[ch].get()
                if start_th_mv[ch] != '':
                    #start_th[ch] = str(int(0x3fff) - int(self.v_to_adc[ch][0] * float(start_th_mv[ch])*0.001 + self.v_to_adc[ch][1]))
                    
                    if polarity=="negative":
                        start_th[ch]= str(int(0x3fff) - int(convert_v_to_adc(float(start_th_mv[ch])*0.001,ch)))
                    
                    if polarity=="positive":
                        start_th[ch]= str(convert_v_to_adc(float(start_th_mv[ch])*0.001,ch))
                else:
                    print("Insert value of starth th on ch "+str(ch)+". Value set to zero")
                    start_th[ch] = '0x3fff'

                stop_th_mv[ch] = self.ent_stop[ch].get()
                if stop_th_mv[ch] != '':
                    #stop_th[ch] = str(int(0x3fff) - int(self.v_to_adc[ch][0] * float(stop_th_mv[ch])*0.001 + self.v_to_adc[ch][1]))
                   
                    if polarity=="negative":
                       stop_th[ch]= str(int(0x3fff) - int(convert_v_to_adc(float(stop_th_mv[ch])*0.001,ch)))
                    
                    if polarity=="positive":
                       stop_th[ch]= str(convert_v_to_adc(float(stop_th_mv[ch])*0.001,ch))
                
                else :
                    print("Insert value of stop th on ch "+str(ch)+". Value set to zero")
                    stop_th[ch] = '0x3fff'

                lead[ch] = self.ent_lead[ch].get()
                if lead[ch] == '':
                    print("Insert value of lead sample on ch "+str(ch)+". Value set to zero")
                    lead[ch]='0'

                tail[ch] = self.ent_tail[ch].get()
                if tail[ch] == '':
                    print("Insert value of tail sample on ch "+str(ch)+". Value set to zero")
                    tail[ch]='0'

                v_bias[ch] = self.ent_vbias[ch].get()
                if v_bias[ch] != '':
                    #v_bias[ch] = (float(v_bias[ch])-self.v_bias_conv[ch][1])/self.v_bias_conv[ch][0]
                    v_bias[ch]=v_adc(float(v_bias[ch]),ch)
                else:
                    print("Insert value of v bias on ch "+str(ch)+". Value set to zero")
                    v_bias[ch] = 0

                v_bias_string = v_bias_string + str(int(v_bias[ch])) + " "
                channel_string = channel_string + str(ch) + " "
                lead_string = lead_string + lead[ch] + " "
                tail_string = tail_string + tail[ch] + " "
                start_th_string = start_th_string + start_th[ch] + " "
                stop_th_string = stop_th_string + stop_th[ch] + " "

            if ch == 11:
                channel_string = channel_string  + '"'
                lead_string = lead_string  + '"'
                tail_string = tail_string  + '"'
                start_th_string = start_th_string + '"'
                stop_th_string = stop_th_string + '"'
                v_bias_string = v_bias_string  + '"'


            else:
                pass        

        option_string=[channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string]
        return option_string 

    def start_monitor_clicked(self, event=None):
        
        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()
        name=str(self.ent_logfile.get())
        self.daq_type="rate"
        
        if not self.print_screen_status.get():
            os.system("touch "+ str(self.ent_logfile.get()))
        
            with open(name, "w") as f:
                f.write(str(datetime.datetime.now())+"\n")
                # f.write("Temperature="+str(subprocess.check_output("""ssh """ + username + """@""" + ip_address + """ 'bash get_param.sh' """, shell=True)[16:18])+"\n") 
                # f.write("Channel\tStart Th\tStop Th\tLead\tTail\n")

                # for ch in re.findall(r'\d+',channel_string):
                #     tail_cmd="./SendCmd -s 0x83 -c " + str(ch)
                #     tail=re.findall(r'\d+',str(subprocess.check_output("""ssh """ + username + """@""" + ip_address + " \' " +tail_cmd+ " \'" ,shell=True)[-5:]))
                    
                #     lead_cmd="./SendCmd -s 0x86 -c " + str(ch)
                #     lead=re.findall(r'\d+',str(subprocess.check_output("""ssh """ + username + """@""" + ip_address + " \' " +lead_cmd+ " \'" ,shell=True)[-5:]))

                #     start_cmd="./SendCmd -s 0x81 -c " + str(ch)
                #     start=str(subprocess.check_output("""ssh """ + username + """@""" + ip_address + " \' " +start_cmd+ " \'" ,shell=True)[-5:])

                #     stop_cmd="./SendCmd -s 0x82 -c " + str(ch)
                #     stop=str(subprocess.check_output("""ssh """ + username + """@""" + ip_address + " \' " +stop_cmd+ " \'" ,shell=True)[-5:])


                #     f.write(str(ch)+"\t"+str(start)+"\t"+str(stop)+"\t"+str(lead)+"\t"+str(tail)+"\n")

                f.write("Integration interval :" +str(self.ent_interval.get()) +" sec - Delay: "+str(self.ent_delay.get()) +" sec\n")
        self.thread_start = threading.Thread(target=self.t_start_daq)
        self.thread_start.deamon = True
        self.thread_start.start()

        e_timer.set()
        e_acquisition.set()

    def stop_monitor_clicked(self, event=None):
        channel_string, start_th_string, stop_th_string, lead_string, tail_string, v_bias_string = self.get_parameter_string()

        e_log.clear()
        e_acquisition.clear()

        print("Stopping acquisition...")
        stdin, stdout, stderr = client.exec_command("""bash daq_run_stop.sh -N """+channel_string)
        print(stdout.readlines())
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'bash daq_run_stop.sh -N """+channel_string+"'")
        time.sleep(1)
        
        stdin, stdout, stderr = client.exec_command("""killall DaqReadTcp""")
        print(stdout.readlines())
        #os.system("""ssh """ + username + """@""" + ip_address + """ 'killall DaqReadTcp'""")
        time.sleep(1)
        if self.arch=="arm":
            os.system("killall RateParser_arm")     
        elif self.arch=="x86":
            os.system("killall RateParser_x86") 

    def open_analysis_clicked(self, event=None):
        name = tk.filedialog.askopenfilename(filetypes=(("Binary file", "*.bin"),),title="Choose a file")
        if name!=() and name != '':
            self.ent_analysis.delete(0,'end')
            self.ent_analysis.insert(0, name)

    def plot_clicked(self, event=None):
        
        filename=self.ent_analysis.get()
        print(filename)

        #filename_txt= filename.split(sep="/")[-1][:-4]+".txt"

        hit_to_plot = self.ent_wf_plot.get()
        hit_to_skip = self.ent_wf_skip.get()
        
        if hit_to_plot == '':
            hit_to_plot=0
        if hit_to_skip == '':
            hit_to_skip =0  
        

        if self.channel_variable.get() == "ALL":
            filename_txt= filename.replace(".bin", "_chall.txt")
            print(filename_txt)
            
            if self.arch == "arm":
                os.system("./HitViewer_arm -p -c -1 -z -r -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)

            elif self.arch=="x86":
                os.system("./HitViewer_x86 -p -c -1 -z -r -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)


            self.count=0
            
            with open(filename_txt) as data:
                ch_acquired=np.unique(np.array([re.findall(r'\d+',x.split("\t")[0])[-1] for x in data.read().splitlines() ]).astype(int))
                try:
                    print("Channel acquired: ",ch_acquired)
                except:
                    print("error")
            
            
            if len(ch_acquired)<=4:
                row=1
                column=len(ch_acquired)

            elif len(ch_acquired)>4 and len(ch_acquired) <=8:
                row=2
                column=4

            else:
                row=3
                column=4

                    
            def onclick_beginning(event):

                index=[(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(2,3)]
                
                plot_index=0
                
                
                if event.button == 1:
                    self.count = self.count + 1 
                    
                    for ch in ch_acquired:
                        with open(filename_txt) as data:
                            try:
                                waveform=np.array([x for x in data.read().splitlines() if x.split("\t")[0]=="0:0:"+str(ch)][self.count].split("\t")[1:-1]).astype(int)
                            except:
                                waveform=""
                        
                        if len(waveform)!=0:
                            
                            y=np.array([convert_adc_to_v(element,int(ch))  for element in waveform])
                            x=np.arange(0,y.size*4,4)

                            if len(ch_acquired)<=4:
                                if not self.overlap_variable.get():
                                    ax[plot_index].clear()
                                    
                                ax[plot_index].plot(x,y)
                                ax[plot_index].grid(True)
                                ax[plot_index].set_title("Wf # "+str(self.count)+" ch "+str(ch))
                                plot_index+=1

                            else:
                                if not self.overlap_variable.get():
                                    ax[index[plot_index]].clear()
                                    
                                ax[index[plot_index]].plot(x,y)
                                ax[index[plot_index]].grid(True)
                                ax[index[plot_index]].set_title("Wf # "+str(self.count)+" ch "+str(ch))
                                plot_index+=1

                    plt.draw() #redraw
                

                if event.button == 3:

                    self.count = self.count - 1            
                    plot_index=0
                    for ch in ch_acquired:
                        
                        with open(filename_txt) as data:
                            try:
                                waveform=np.array([x for x in data.read().splitlines() if x.split("\t")[0]=="0:0:"+str(ch)][self.count].split("\t")[1:-1]).astype(int)
                            except:
                                waveform=""
                        
                        if len(waveform)!=0:
                            
                            y=np.array([convert_adc_to_v(element,int(ch))  for element in waveform])
                            x=np.arange(0,y.size*4,4)

                            if len(ch_acquired)<=4:
                                if not self.overlap_variable.get():
                                    ax[plot_index].clear()

                                ax[plot_index].plot(x,y)
                                ax[plot_index].grid(True)
                                ax[plot_index].set_title("Wf # "+str(self.count)+" ch "+str(ch))
                                plot_index+=1

                            else:
                                if not self.overlap_variable.get():
                                    ax[index[plot_index]].clear()

                                ax[index[plot_index]].plot(x,y)
                                ax[index[plot_index]].grid(True)
                                ax[index[plot_index]].set_title("Wf # "+str(self.count)+" ch "+str(ch))
                                plot_index+=1

                    plt.draw() #redraw
                

            fig,ax=plt.subplots(row,column)
            plt.tight_layout(pad=2, w_pad=1, h_pad=1)
            fig.canvas.mpl_connect('button_press_event',onclick_beginning)
            plt.show()



        else:
            ch=self.channel_variable.get()
            print(ch)
            #filename_txt= filename.split(sep="/")[-1][:-4]+"_ch"+str(ch)+".txt"

            filename_txt= filename.replace(".bin","_ch"+str(ch)+".txt" )
            print(filename_txt)

            if self.arch == "arm":
                os.system("./HitViewer_arm -p -c " + str(ch) + " -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)
            elif self.arch=="x86":
                os.system("./HitViewer_x86 -p -c " + str(ch) + " -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)



            with open(filename_txt) as data:
                self.lenght=len(data.read().splitlines())

            self.count=0
            def on_close(event):
                pass
                
            def onclick_beginning(event):

                if event.button == 1:
                    self.count = self.count + 1 

                    with open(filename_txt) as data:
                        waveform=data.read().splitlines()[self.count]
                        
                        
                    y=np.array(waveform.split("\t")[:-1]).astype(int)
                    y= np.array([convert_adc_to_v(element,int(ch))  for element in y])
                    x=np.arange(0,y.size*4,4)
                #clear frame
                    if not self.overlap_variable.get():
                        plt.clf()
                        
                    
                  

                if event.button == 3:
                    self.count = self.count - 1 

                    with open(filename_txt) as data:
                        waveform=data.read().splitlines()[self.count]   

                    y=np.array(waveform.split("\t")[:-1]).astype(int)
                    y= np.array([convert_adc_to_v(element,int(ch))  for element in y])
                    x=np.arange(0,y.size*4,4)
                #clear frame
                    if not self.overlap_variable.get():
                        plt.clf()
                        
                    
                    
                        
                ax1 = plt.gca()
                ax1.set_title("waveform # "+ str(self.count)+"/"+str(self.lenght))
                ax1.set_ylabel("Amplitude (mV)")
                ax1.set_xlabel("Time (ns)")
                plt.grid(True)
                ax1.plot(x,y)
                plt.draw() #redraw
                
            


            fig,ax1=plt.subplots()
            ax1.set_title("waveform # "+ str(self.count))
            ax1.set_ylabel("Amplitude (V)")
            ax1.set_xlabel("Time")
            fig.canvas.mpl_connect('button_press_event',onclick_beginning)
            fig.canvas.mpl_connect('close_event',on_close)            
            plt.show()
  
    def histo_clicked(self, event=None):
        
        bins=int(self.ent_bin.get())
        
        filename=self.ent_analysis.get()
        print(filename)

        filename_txt= filename.split(sep="/")[-1][:-4]+".txt"

        hit_to_plot = self.ent_wf_plot.get()
        hit_to_skip = self.ent_wf_skip.get()
        
        if hit_to_plot == '':
            hit_to_plot=0
        if hit_to_skip == '':
            hit_to_skip =0  
        

        if self.channel_variable.get() == "ALL":
            filename_txt= filename.split(sep="/")[-1][:-4]+"_chall"+".txt"
            
            if self.arch=="arm":
                os.system("./HitViewer_arm -p -c -1 -z -r -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)
            elif self.arch=="x86":
                os.system("./HitViewer_x86 -p -c -1 -z -r -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)

            with open(filename_txt) as data:
                waveform=data.read().splitlines()

            waveform=np.array(waveform)

            waveform_sorted={}
            for ch in np.arange(0,12):
                waveform_sorted[ch]=[]

            for wave in waveform:
                wave_split=wave.split("\t")[:-1]
                waveform_sorted[int(wave_split[0].split(":")[-1])].append(np.array(wave_split[1:]).astype(int))


            maximum={}
            charge={}
            duration={}

            n_ch=[]

            for ch in waveform_sorted.keys():
                if len(waveform_sorted[ch])!=0:
                    n_ch.append(ch)

            print(n_ch) 

            if len(n_ch)<=4:
                row=1
                column=len(n_ch)

            elif len(n_ch)>4 and len(n_ch) <=8:
                row=2
                column=4

            else:
                row=3
                column=4

            fig,ax = plt.subplots(row,column)
            plt.tight_layout()
            #plt.tight_layout(pad=2, w_pad=1, h_pad=1)


            count=0
            for ch in waveform_sorted.keys():

                if len(waveform_sorted[ch])!=0:
                    maximum[ch]=[]
                    duration[ch]=[]
                    charge[ch]=[]

                    for wave in waveform_sorted[ch]:
                        if len(wave) != 0:
                            if self.histo_type_variable.get()=="Maximum":
                                maximum[ch].append(wave.max())

                            if self.histo_type_variable.get()=="Duration":
                                duration[ch].append(wave.size*4)

                            if self.histo_type_variable.get()=="Charge":
                                if self.pedestal_variable.get():
                                    pedestal=int(self.ent_pedestal.get())
                                    wave=convert_adc_to_v(wave, int(ch))
                                    charge[ch].append((wave*(4/50)).sum()-(wave[:pedestal].mean()*wave.size))

                                else:
                                    wave=convert_adc_to_v(wave, int(ch))
                                    charge[ch].append((wave*(4/50)).sum())
                    
                    #ax[count].set_xlabel("Max amplitude (mV)")
                    #ax[count].set_ylabel("Counts")
                    ax[count].set_title("ch "+str(ch)) 
                    if self.histo_type_variable.get()=="Maximum":
                        ax[count].hist(convert_adc_to_v(np.array(maximum[ch]).astype(int), int(ch)))
                    
                    if self.histo_type_variable.get()=="Duration":
                        ax[count].hist(duration[ch])

                    if self.histo_type_variable.get()=="Charge":
                        ax[count].hist(charge[ch])

                    count=count+1

            plt.show()


        else:
            ch=self.channel_variable.get()
            filename_txt= filename.split(sep="/")[-1][:-4]+"_ch"+str(ch)+".txt"

            if self.arch=="arm":
                os.system("./HitViewer_arm -p -c " + str(ch) + " -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)
            elif self.arch=="x86":
                os.system("./HitViewer_x86 -p -c " + str(ch) + " -f "+str(filename)+" -n "+str(hit_to_plot) +" -o "+str(hit_to_skip)+" > " + filename_txt)

            if self.histo_type_variable.get()=="Maximum":
                with open(filename_txt) as data:
                    maximum=[(np.array(x.split("\t"))[:-1].astype(int)).max() for x in progressBar(data.read().splitlines()) if x != ""]   

                maximum=[convert_adc_to_v(x, int(ch)) for x in maximum]
               
                if self.trigger_variable.get():
                    maximum=[x for x in maximum if x>=float(self.ent_trigger.get())]
                print(self.trigger_variable.get())

                fig,ax = plt.subplots()
                ax.set_xlabel("Max amplitude (mV)")
                ax.set_ylabel("Counts")
                ax.set_title("Max amplitude histogram") 
                ax.hist(maximum, bins=bins)
                plt.show()

                 # if self.histo_type_variable.get()=="Charge":
                 #     charge=[]
                 #     with open(filename_txt) as data:
                 #         for x in progressBar(data.read().splitlines()):
                 #             x_int=np.array([convert_adc_to_v(y,int(ch)) for y in np.array(x.split("\t"))[:-1].astype(int) if y!=""])
                             
                 #             if self.trigger_variable.get():
                 #                 if np.max(x_int)>=float(self.ent_trigger.get()):
                 #                     if self.pedestal_variable.get():
                 #                         pedestal=int(self.ent_pedestal.get())
                 #                         charge.append((x_int*(4/50)).sum()-(x_int[:pedestal].mean()*x_int.size))
                 #                     else:
                 #                         charge.append((x_int*(4/50)).sum())
                 #             else:
                 #                 if self.pedestal_variable.get():
                 #                     pedestal=int(self.ent_pedestal.get())
                 #                     charge.append((x_int*(4/50)).sum()-(x_int[:pedestal].mean()*x_int.size))
                 #                 else:
                 #                     charge.append((x_int*(4/50)).sum())
              
                 #     fig,ax = plt.subplots()
                 #     ax.set_xlabel("Charge (pC)")
                 #     ax.set_ylabel("Counts")
                 #     ax.set_title("Charge histogram") 
                 #     ax.hist(charge,bins=bins)
                 #     plt.show()
 
            if self.histo_type_variable.get()=="Duration":
                
                if self.trigger_variable.get():
                    with open(filename_txt) as data:
                        duration=[len(np.array(x.split("\t"))[:-1])*4 for x in progressBar(data.read().splitlines()) if x != "" and np.max([convert_adc_to_v(y,int(ch)) for y in (np.array(x.split("\t"))[:-1].astype(int))])>=float(self.ent_trigger.get())]   
                else:
                    with open(filename_txt) as data:
                        duration=[len(np.array(x.split("\t"))[:-1])*4 for x in progressBar(data.read().splitlines()) if x != ""]   


                fig,ax = plt.subplots()
                ax.set_xlabel("Duration (ns)")
                ax.set_ylabel("Counts")
                ax.set_title("Duration histogram") 
                ax.hist(duration,bins=bins)
                plt.show()

    def run(self):
        self.mainwindow.mainloop()


def on_exit():
    e_monitor.clear()
    e_timer.set()
    root.destroy()

if __name__ == '__main__':
    import tkinter as tk
    root = tk.Tk()
    root.title("WaveBoard Controller Ultra")
    root.protocol("WM_DELETE_WINDOW", on_exit)
    app = WbControllerUltraApp()
#     app.run()
    root.mainloop()

