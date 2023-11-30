# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 09:24:01 2023

@author: thobson
"""
from __future__ import print_function
import io
from os import path

import numpy as np

import pandas as pd #   Needed for file output

import csv
import requests
import PySimpleGUI as sg
import pyautogui as pag

from datetime import date
from datetime import datetime

from datetime import date

from time import sleep



print('SOL-GEL Input Application Local v4.3, BIGMAP WP4, University of Liverpool\n')


#------------------------------------------------------------------------------
#-------------------------- File Input ----------------------------------------
#------------------------------------------------------------------------------


mat_file_path = "Materials Information.csv"
print("Materials information source file: "+mat_file_path)  # States the source file for the materials info table


var_file_path = "Default Fixed Variables.csv"
print("Default fixed variables source file: "+var_file_path)    # States the source file for the 'fixed' variables info table


Mat_Vals_In = []   # Inititalises an array to contain the material values

mat_file = open(mat_file_path, encoding='utf-8-sig')

with mat_file as csvfile:       # Reads the materials info file row by row and adds the data to the array
    reader = csv.reader(csvfile, delimiter =',')
    for row in reader:
        Mat_Vals_In.append(row)    # Instead of a single value, it nests each row as a list of values within the larger list
        
mat_file.close()    # Close the input file to allow the others to be read

Var_Vals_In = []

var_file = open(var_file_path, encoding='utf-8-sig')

with var_file as csvfile:       # Reads the input file row by row and adds the data to the array
    reader = csv.reader(csvfile, delimiter =',')
    for row in reader:
        Var_Vals_In.append(row)    # Also nests each row as a list of values within the larger list
        
var_file.close()    # Close the input file, we should now have all the info we need to calculate weights


#------------------------------------------------------------------------------
#---------------------- Super-User Global Input Values-------------------------
#------------------------------------------------------------------------------

# Note, if you intend to input values manually, put them in as strings

tol = '1'   # Default tolerance in %
nmc_mass = Var_Vals_In[0][1]  # Default NMC Mass in g
al_sol_ratio = 1 # Default Al sol gel precursor to NMC ratio in mol%

liq_vol = Var_Vals_In[1][1] # Default total liquid volume in ml
mol_etacac_solid = Var_Vals_In[2][1]    # Default mol ratio EtAcAc:Solid
conc_al_trisec = Var_Vals_In[3][1]   # Default concentration of Al-triSec in mol/L
conc_etacac_al = Var_Vals_In[4][1]   # Default concentration of EtAcAc in Al/IPA
conc_tot = Var_Vals_In[5][1]     # Default total concentration in mol/kg
conc_mol_etacac = Var_Vals_In[6][1]  # Default concentration in mols EtAcAc/kg

max_samps = 30  # Max number of samples that can fit on the balance

default_stirr = ""  # The current standard stirrer to be used, with "" meaning no stirrer

Method_ID = "M78"   # ID of the method being used

send_file_path = "C:/Data/XPR_In_Files/"

ext_file_path = "C:/Data/XPR_Out_Files/"

sg.theme('SystemDefault')   # Defines the theme of the dialog boxes

# print("Solid mass = "+str(nmc_mass)+" g, Tolerance = "+str(tol)+" %\n")

#------------------------------------------------------------------------------
#-------------------------- Function Definitions ------------------------------
#------------------------------------------------------------------------------


def Calc_Weights_Al_Sol(NMC_m,Mat_Vals,Var_Vals,Tar_Vals):       # Defines a function that takes the arrays from the input files and calculates weights (note that maths is done on whole columns at a time)

    nNMC = float(NMC_m)/float(Mat_Vals[1][1])  # Value from mat_vals[1][1] is 2nd value of 2nd row, as counting starts from 0
    # print('nNMC Value: '+str(nNMC))
    
    nAltriSec = np.multiply((np.multiply(Tar_Vals,2)),np.divide(nNMC,np.subtract(100,Tar_Vals)))   # Makes new list by applying maths operations to input list
    
    # print('nAl-triSec: '+str(nAltriSec))
    
    nEtAcAc_total = nNMC*float(Var_Vals[1])
    # print('nEtAcAc Total: '+str(nEtAcAc_total))
    
    mass_g_NMC = [float(NMC_m)]*len(Tar_Vals) # Since this value is fixed a list of the value is made with the same length as the targets list

    mass_g_Al_sol = np.multiply(np.divide(nAltriSec,float(Var_Vals[4])),1000)    # This is a list of the calculated Al sol weights in g
    # print('Mass g Al sol: '+str(mass_g_Al_sol))
    
    nEtAcAc_from_solution = np.multiply(np.divide(mass_g_Al_sol,1000),float(Var_Vals[3]))
    # print('nEtAcAc from Solution: '+str(nEtAcAc_from_solution))
    
    mass_EtAcAc_pure = np.multiply((np.subtract(nEtAcAc_total,nEtAcAc_from_solution)),float(Mat_Vals[3][1]))    # This is a list of the calculated pure EtAcAc weights in g
    # print('Mass EtAcAc Pure: '+str(mass_EtAcAc_pure))
    
    vol_EtAcAc = np.divide(mass_EtAcAc_pure,float(Mat_Vals[3][2]))
    # print('Vol EtAcAc: '+str(vol_EtAcAc))
    
    vol_IPA = np.subtract(float(Var_Vals[0]),(np.add((np.divide(vol_EtAcAc,1.2)),mass_g_Al_sol)))
    # print('Vol IPA: '+str(vol_IPA))
    
    mass_IPA = np.multiply(vol_IPA,float(Mat_Vals[4][2]))   # This is a list of the calculated IPA weights in g
    # print('Mass IPA: '+str(mass_IPA))
    
    return (mass_g_NMC,mass_g_Al_sol,mass_EtAcAc_pure,mass_IPA)    # Returns lists with the 3 relevant weights

def Calc_Weights_NMC(al_sol,Mat_Vals,Var_Vals,NMC_Vals):       # Defines a function that takes the arrays from the input files and calculates weights (note that maths is done on whole columns at a time)

    nNMC = np.divide(NMC_Vals,float(Mat_Vals[1][1]))  # Value from mat_vals[1][1] is 2nd value of 2nd row, as counting starts from 0
    # print('nNMC Value: '+str(nNMC))
    
    nAltriSec = np.multiply((float(al_sol)*2),np.divide(nNMC,(100-float(al_sol))))   # Makes new list by applying maths operations to input list
    
    # print('nAl-triSec: '+str(nAltriSec))
    
    nEtAcAc_total = np.multiply(nNMC,float(Var_Vals[1]))
    # print('nEtAcAc Total: '+str(nEtAcAc_total))
    
    mass_g_NMC = NMC_Vals # Since this value is fixed a list of the value is made with the same length as the targets list

    mass_g_Al_sol = np.multiply(np.divide(nAltriSec,float(Var_Vals[4])),1000)    # This is a list of the calculated Al sol weights in g
    # print('Mass g Al sol: '+str(mass_g_Al_sol))
    
    nEtAcAc_from_solution = np.multiply(np.divide(mass_g_Al_sol,1000),float(Var_Vals[3]))
    # print('nEtAcAc from Solution: '+str(nEtAcAc_from_solution))
    
    mass_EtAcAc_pure = np.multiply((np.subtract(nEtAcAc_total,nEtAcAc_from_solution)),float(Mat_Vals[3][1]))    # This is a list of the calculated pure EtAcAc weights in g
    # print('Mass EtAcAc Pure: '+str(mass_EtAcAc_pure))
    
    vol_EtAcAc = np.divide(mass_EtAcAc_pure,float(Mat_Vals[3][2]))
    # print('Vol EtAcAc: '+str(vol_EtAcAc))
    
    vol_IPA = np.subtract(float(Var_Vals[0]),(np.add((np.divide(vol_EtAcAc,1.2)),mass_g_Al_sol)))
    # print('Vol IPA: '+str(vol_IPA))
    
    mass_IPA = np.multiply(vol_IPA,float(Mat_Vals[4][2]))   # This is a list of the calculated IPA weights in g
    # print('Mass IPA: '+str(mass_IPA))
    
    return (mass_g_NMC,mass_g_Al_sol,mass_EtAcAc_pure,mass_IPA)    # Returns lists with the 3 relevant weights

def Calc_Weights_All(al_sol,Mat_Vals,Var_Vals,NMC_Vals):       # Defines a function that takes the arrays from the input files and calculates weights (note that maths is done on whole columns at a time)

    nNMC = np.divide(NMC_Vals,float(Mat_Vals[1][1]))  # Value from mat_vals[1][1] is 2nd value of 2nd row, as counting starts from 0
    # print('nNMC Value: '+str(nNMC))
    
    nAltriSec = np.multiply((float(al_sol)*2),np.divide(nNMC,(100-float(al_sol))))   # Makes new list by applying maths operations to input list
    
    # print('nAl-triSec: '+str(nAltriSec))
    
    nEtAcAc_total = np.multiply(nNMC,float(Var_Vals[1]))
    # print('nEtAcAc Total: '+str(nEtAcAc_total))
    
    mass_g_NMC = NMC_Vals # Since this value is fixed a list of the value is made with the same length as the targets list

    mass_g_Al_sol = np.multiply(np.divide(nAltriSec,float(Var_Vals[4])),1000)    # This is a list of the calculated Al sol weights in g
    # print('Mass g Al sol: '+str(mass_g_Al_sol))
    
    nEtAcAc_from_solution = np.multiply(np.divide(mass_g_Al_sol,1000),float(Var_Vals[3]))
    # print('nEtAcAc from Solution: '+str(nEtAcAc_from_solution))
    
    mass_EtAcAc_pure = np.multiply((np.subtract(nEtAcAc_total,nEtAcAc_from_solution)),float(Mat_Vals[3][1]))    # This is a list of the calculated pure EtAcAc weights in g
    # print('Mass EtAcAc Pure: '+str(mass_EtAcAc_pure))
    
    vol_EtAcAc = np.divide(mass_EtAcAc_pure,float(Mat_Vals[3][2]))
    # print('Vol EtAcAc: '+str(vol_EtAcAc))
    
    vol_IPA = np.subtract(float(Var_Vals[0]),(np.add((np.divide(vol_EtAcAc,1.2)),mass_g_Al_sol)))
    # print('Vol IPA: '+str(vol_IPA))
    
    mass_IPA = np.multiply(vol_IPA,float(Mat_Vals[4][2]))   # This is a list of the calculated IPA weights in g
    # print('Mass IPA: '+str(mass_IPA))
    
    return (mass_g_NMC,mass_g_Al_sol,mass_EtAcAc_pure,mass_IPA)    # Returns lists with the 3 relevant weights

def SampNum_Dialog():
    
    l1 = sg.Text("Enter number of samples",font=('Arial',12))
    box1 = sg.Input('11', enable_events=True,key='-INPUT1-', expand_x=False, justification='left')
    l2 = sg.Text("Min 1, Max 30, Default 11")
    b1 = sg.Button("OK", key='-OK-')
    b2 = sg.Button("Quit", key='-QUIT-')
    
    l3 = sg.Text('Parameter to vary:')
    
    variables = ['Al sol gel precursor mol%','NMC mass g', 'Tolerances in %',\
                 'Total liquid vol ml','Mol ratio EtAcAc to solid mol%','Concentration Al-triSec mol/L',\
                     'Conc EtAcAc in Al/IPA','Concentration mol/kg tot','Concentration molEtACAC/kg tot']
        
    vars_list = sg.Combo(variables, default_value=variables[0], font=('Arial', 12),  expand_x=True, enable_events=True,  readonly=True, key='-VARS-')
    
    to_vary = variables[0]
    
    layout = [[l1],[box1],[l2],[l3],[vars_list],[b1,b2]]
    
    window_samps = sg.Window("Sample Number", layout, size=(350,250)) # Start a dialog box with the layout defined above
    
    I_Vals = []
    d_out = []    
    s_name = ''
    appr = False
    samp_num = 11
    param_num = 9   # Number of independent parameters (including one tolerance)
    
    while True:
        event, values = window_samps.read()
        
        if (event == '-VARS-'):
            to_vary = values['-VARS-']
            print('Parameter to vary: '+str(to_vary))
        
        if (event == '-OK-'):
            if (values['-INPUT1-'] != ''):
                samp_num = int(values['-INPUT1-'])
                if ((samp_num < 1) or (samp_num > max_samps)):
                    sg.popup("Please enter a value between 1 and "+str(max_samps))
                else:
                    I_Vals, d_out, r_dat, s_name, appr = Input_Dialog(samp_num,param_num,variables,to_vary)
                    if (appr == True):
                        break
            else:
                sg.popup("Please enter a value between 1 and 30")
        
        if (event == "-QUIT-" or event == sg.WIN_CLOSED):
            break
    
    window_samps.close()
    
    return(samp_num, I_Vals, d_out, r_dat, s_name, appr)


def Input_Dialog(s_num,p_num,vrbls,var_param):     # Creates a dialog box for a user to upload target mol% values or enter manually
    
    box_width = 25
    
    
    l0_0 = sg.Text("Name of sample series (will default to series ID if left blank)",font=('Arial',12))
    box0_0 = sg.Input('', size=((box_width*2),None), enable_events=True,key='-INPUT0_0-')
    
    if (var_param == 'NMC mass g'):
        l0_1 = sg.Text("Al sol gel mol% of NMC       ",font=('Arial',12))
        box0_1 = sg.Input(al_sol_ratio, size=(box_width,None), enable_events=True,key='-INPUT0_1-')
    else:
        l0_1 = sg.Text("Weight of NMC Powder in g       ",font=('Arial',12))
        box0_1 = sg.Input(nmc_mass, size=(box_width,None), enable_events=True,key='-INPUT0_1-')
    
    l0_2 = sg.Text("Tolerances (all substances) in %",font=('Arial',12))
    box0_2 = sg.Input(tol, size=(box_width,None), enable_events=True,key='-INPUT0_2-')
    
    l0_3 = sg.Text("Total liquid volume in mL             ",font=('Arial',12))
    box0_3 = sg.Input(liq_vol, size=(box_width,None), enable_events=True,key='-INPUT0_3-')
    
    l0_4 = sg.Text("Mol ratio EtAcAc:Solid                ",font=('Arial',12))
    box0_4 = sg.Input(mol_etacac_solid, size=(box_width,None), enable_events=True,key='-INPUT0_4-')
    
    l0_5 = sg.Text("Concentration Al-trisec in mol/L ",font=('Arial',12))
    box0_5 = sg.Input(conc_al_trisec, size=(box_width,None), enable_events=True,key='-INPUT0_5-')
    
    l0_6 = sg.Text("Conc EtAcAc in Al/IPA                ",font=('Arial',12))
    box0_6 = sg.Input(conc_etacac_al, size=(box_width,None), enable_events=True,key='-INPUT0_6-')
    
    l0_7 = sg.Text("Concentration in mol/kg tot         ",font=('Arial',12))
    box0_7 = sg.Input(conc_tot, size=(box_width,None), enable_events=True,key='-INPUT0_7-')
    
    l0_8 = sg.Text("Concentration molEtAcAc/kg tot",font=('Arial',12))
    box0_8 = sg.Input(conc_mol_etacac, size=(box_width,None), enable_events=True,key='-INPUT0_8-')
    
    
    
    l1 = sg.Text("Select csv file to upload values from col 1: ",font=('Arial',12)) # The test that will appear in the dialog box
    
    if (var_param == 'NMC mass g'):
        l2 = sg.Text("Weight of NMC Powder in g",font=('Arial',12))
    else:
        l2 = sg.Text("Al sol gel mol% of NMC",font=('Arial',12))
    
    
    l3_1 = sg.Text("Rack reaction temp in C",font=('Arial',12))
    l3_2 = sg.Text("Rack stirring speed in RPM",font=('Arial',12))
    l3_3 = sg.Text("Rack stirring time in mins",font=('Arial',12))
    l3_4 = sg.Text("Calcination temp in C",font=('Arial',12))
    
    box3_1 = sg.Input("80", size=(box_width,None), enable_events=True,key='-INPUT0_9-')
    box3_2 = sg.Input("450", size=(box_width,None), enable_events=True,key='-INPUT0_10-')
    box3_3 = sg.Input("30", size=(box_width,None), enable_events=True,key='-INPUT0_11-')
    box3_4 = sg.Input("400", size=(box_width,None), enable_events=True,key='-INPUT0_12-')
    
    f3 = sg.Frame("Reaction Stage Parameters",[\
        [l3_1,box3_1],\
            [l3_2,box3_2],\
                [l3_3,box3_3],\
                    [l3_4,box3_4]],\
                      title_color='black')
    
    samp_boxes = [[l2]]
    
    for i in range (1,(s_num+1)):   # Makes a number of input boxes equal to the number of samples
        samp_boxes.append([sg.Input('0', size=(box_width,None), enable_events=True,key='-INPUT'+str(i)+'-')])
        
    
    box12 = sg.Input(key = '-FINPUT-')  # Input box for file path to get data from
    
    b1 = sg.Button("Calculate", key='-SUBMIT-')
    b2 = sg.Button("Back", key='-QUIT-')
    b3 = sg.FileBrowse('Browse', key='-BROWSE-')
    b4 = sg.Button("Fill", key = '-FILL-')  # Clickable buttons and their events

    
    layout = [
              [sg.Column([\
              [l1],\
              [box12,b3],\
              [b4],\
              [l0_0],\
              [box0_0],\
              [l0_1,box0_1],\
                  [l0_2,box0_2],\
                    [l0_3,box0_3],\
                        [l0_4,box0_4],\
                            [l0_5,box0_5],\
                                [l0_6,box0_6],\
                                    [l0_7,box0_7],\
                                        [l0_8,box0_8],\
              ]),\
              sg.Column(samp_boxes),f3,\
                  ],\
                  [b1,b2],\
              ]     # Define the layout of the dialog box, using the elements above (cannot be used more than once)
        
    if (s_num <= 14):
        win_height = 455
    else:
        win_height = 455 + (25*(s_num-14))  # Scales the size of the dialog box to match the number of samples
        
    window_in = sg.Window("Sol-Gel Process Input", layout, size=(1100,win_height),resizable=True) # Start a dialog box with the layout defined above
    
    Out_Values = []     # Initialise the array which will contain the target values
    data_Check = []
    data_new = []
    rack_data = []
    series_name = ''
    approval = False
    
    while True:
        event, values = window_in.read()
    
        if (event == '-FILL-'):     # Once the user has selected an input file with the 'Browse' button, this will fill the input boxes
            if ((path.exists(values['-FINPUT-']) == True) and (values['-FINPUT-'][-4:]=='.csv')):   # Action will only happen if a valid file path is selected
                choose_file_path = values['-FINPUT-']
                choose_file = open(choose_file_path, encoding = 'utf-8-sig')    # Opens the selected file
                
                with choose_file as csvfile:
                    reader=csv.reader(csvfile, delimiter = ',')
                    
                    i = 0
                    
                    for row in reader:
                        if (i<=(s_num+1)):
                            if (i>0):
                                if (var_param == 'NMC mass g'):
                                    window_in['-INPUT'+str(i)+'-'].update(row[1])
                                else:
                                    window_in['-INPUT'+str(i)+'-'].update(row[0])   # Fills the input boxes with the contents of the source file
                                if (i == 1):
                                    if (len(row)<13):
                                        sg.popup("Input file does not match the expected import format. Check the correct values have been read in.")
                                    for j in range (1,len(row)):   # Reads in the 'fixed' values and reaction parameters from the template file
                                        if (row[j] != ''):      # Values are only read in if the parameter field is not left blank
                                            window_in['-INPUT0_'+str(j)+'-'].update(row[j]) # Fills the input boxes with these values
                                    if (var_param == 'NMC mass g'):
                                        window_in['-INPUT0_1-'].update(row[0])

                            i = i + 1
                
                # print(choose_file_path)
                
                choose_file.close()
    
            else:
                sg.popup('Please select a csv file in a valid path') # If file path is not vaild, this pop-up appears
            
        if event == '-SUBMIT-':
            if len(Out_Values) == 0:
                for i in range(1,(s_num+1)):
                    try:
                        Out_Values.append(float(values['-INPUT'+str(i)+'-']))  # Adds the input values to the list if it is empty
                    except:
                        Out_Values.append(0.0)  # If float conversion fails (e.g. if user inputs text, 0 will be input instead)
                        
            elif len(Out_Values) > 0:
                for j in range (1,(s_num+1)):
                    try:
                        Out_Values[j-1] = float(values['-INPUT'+str(j)+'-'])   # Updates the list with current input values if it is not empty
                    except:
                        Out_Values[j-1] = 0.0   # If float conversion fails (e.g. if user inputs text, 0 will be input instead)
                        
            Fixed_Vals = ['']*8
            for k in range (1,9):
                if (values['-INPUT0_'+str(k)+'-'] == ''):   # If the user deletes the values in the box, '0' is read instead
                    Fixed_Vals[k-1] = '0'
                else:
                    Fixed_Vals[k-1] = values['-INPUT0_'+str(k)+'-'] # Reads the fixed values put in the input boxes
            
            Tol_Vals = [float(Fixed_Vals[1])]*len(Out_Values)    # Makes a list containing the single tolerance value
            
            if (var_param == 'NMC mass g'):
                data_Check = Calc_Weights_NMC(Fixed_Vals[0],Mat_Vals_In,Fixed_Vals[2:],Out_Values)
            else:
                data_Check = Calc_Weights_Al_Sol(Fixed_Vals[0],Mat_Vals_In,Fixed_Vals[2:],Out_Values) # Calls the function to calculate the weights needed for the target values
            
            
            nmc_vals = [float(Fixed_Vals[0])]*len(Out_Values)
            al_sol_vals = [float(Fixed_Vals[1])]*len(Out_Values)
            tot_liq_vals = [float(Fixed_Vals[2])]*len(Out_Values)
            mol_etacac_vals = [float(Fixed_Vals[3])]*len(Out_Values)
            conc_altri_vals = [float(Fixed_Vals[4])]*len(Out_Values)
            etacac_in_IPA_vals = [float(Fixed_Vals[5])]*len(Out_Values)
            conc_molkg_vals = [float(Fixed_Vals[6])]*len(Out_Values)
            conc_moletacac_tot_vals = [float(Fixed_Vals[7])]*len(Out_Values)
            
            series_name=values['-INPUT0_0-']
            
            approval, data_new = Scan_Dialog(s_num,series_name,Out_Values,data_Check,Tol_Vals,var_param)     # Opens a second dialog box so users can check the calculated values before submitting
                
            # print("Scanned Data:")
            # print(data_new)
            
            if (len(rack_data) == 0):   # Makes a series with the input reaction parameters to send to orbit shaker input file
                for l in range(9,13):
                    try:
                        rack_data.append(values['-INPUT0_'+str(l)+'-'])
                    except:
                        rack_data.append('0')
                        
            elif (len(rack_data) > 0):
                for l in range(9,13):
                    try:
                        rack_data[l-9] = values['-INPUT0_'+str(l)+'-']
                    except:
                        rack_data[l-9] = '0'
            
            if approval == True:    # If the user clicked 'Submit' on the output window, this window will also close
                break
           
        if (event == "-QUIT-" or event == sg.WIN_CLOSED):
            break
        
    window_in.close()

    return(Out_Values,data_new,rack_data,series_name,approval)  # Returns the array of target values (note, these will be strings, no floats)

def Scan_Dialog(samp_no,s_name,Inp_Vals,data_out,Perc_Tol_Out,vrbl): # Dialog box where user can edit calculated values and scan sample IDs
    
    is_complete = False
    box_width = 22  # Width of the input boxes
    dec_places = 3  # This is the precision weights need to be in to be usable by the balance
    
    l1 = sg.Text("Process Parameters are shown below, please check/edit values, scan vials and place in positions", font=('Arial',12))
    
    col_list_0=[[sg.Text("No.")]]
    col_list_1=[[sg.Text("SampleID")]]
    col_list_2=[[sg.Text("Mass NMC / g")]]
    col_list_3=[[sg.Text("Tol NMC / % (min 1%)")]]
    col_list_4=[[sg.Text("Mass IPA / g")]]
    col_list_5=[[sg.Text("Tol IPA / % (min 1%)")]]
    col_list_6=[[sg.Text("Mass EtAcAc / g")]]
    col_list_7=[[sg.Text("Tol EtAcAc / % (min 1%)")]]
    col_list_8=[[sg.Text("Mass Al Sol / g")]]
    col_list_9=[[sg.Text("Tol Al Sol / % (min 1%)")]]
    col_list_10=[[sg.Text("Stirrer")]]    # Makes a series of lists (which will form columns) with the the first item the header for each column
    
    for i_0 in range (1,(samp_no+1)): # Makes lists containing input boxes for each column, populated with default values from calculation
        box_0 = sg.Text(str(i_0))
        col_list_0.append([box_0])
        
        box_1 = sg.Input(default_text = "", size=(None,box_width), key="-INPUT_1_"+str(i_0)+"-")
        col_list_1.append([box_1])
        
        box_2 = sg.Input(default_text = str(round(data_out[0][i_0-1],dec_places)), size=(box_width,None), key="-INPUT_2_"+str(i_0)+"-")
        col_list_2.append([box_2])
        
        box_3 = sg.Input(default_text = str(Perc_Tol_Out[i_0-1]), size=(box_width,None), key="-INPUT_3_"+str(i_0)+"-")
        col_list_3.append([box_3])
        
        box_4 = sg.Input(default_text = str(round(data_out[3][i_0-1],dec_places)), size=(box_width,None), key="-INPUT_4_"+str(i_0)+"-")
        col_list_4.append([box_4])
        
        box_5 = sg.Input(default_text = str(Perc_Tol_Out[i_0-1]), size=(box_width,None), key="-INPUT_5_"+str(i_0)+"-")
        col_list_5.append([box_5])
        
        box_6 = sg.Input(default_text = str(round(data_out[2][i_0-1],dec_places)), size=(box_width,None), key="-INPUT_6_"+str(i_0)+"-")
        col_list_6.append([box_6])
        
        box_7 = sg.Input(default_text = str(Perc_Tol_Out[i_0-1]), size=(box_width,None), key="-INPUT_7_"+str(i_0)+"-")
        col_list_7.append([box_7])
        
        box_8 = sg.Input(default_text = str(round(data_out[1][i_0-1],dec_places)), size=(box_width,None), key="-INPUT_8_"+str(i_0)+"-")
        col_list_8.append([box_8])
        
        box_9 = sg.Input(default_text = str(Perc_Tol_Out[i_0-1]), size=(box_width,None), key="-INPUT_9_"+str(i_0)+"-")
        col_list_9.append([box_9])
        
        box_10 = sg.Input(default_text = default_stirr, size=(box_width,None), enable_events = True, key="-INPUT_10_"+str(i_0)+"-")
        col_list_10.append([box_10])
        
    b1 = sg.Button('Go Back', key = '-BACK-')
    b2 = sg.Button('Complete', key = '-COMP-')    
        
    layout_scan = [[l1],[sg.Column(col_list_0),sg.Column(col_list_1),sg.Column(col_list_2),\
                         sg.Column(col_list_3),sg.Column(col_list_4),sg.Column(col_list_5),\
                             sg.Column(col_list_6),sg.Column(col_list_7),sg.Column(col_list_8),\
                                 sg.Column(col_list_9),sg.Column(col_list_10)],[b1,b2]]    # Defines the layout of the dialog with each list converted into a column
    
   
    window_scan = sg.Window(s_name, layout_scan, size = (1750,(100+(30*samp_no))),resizable = True) # Defines dialog box with size scaled to the number of samples
    
    new_dat=[]  # A list containing the modified data columns
    
    i_scan = 1  # Used to check whether a sampleID box has been filled
    
    while True:
        
        event, values = window_scan.read(timeout=500)   # The dialog window is opened here, timeout defines how long before cursor moves on form a filled sampleID box
        
        if (event != sg.WIN_CLOSED):    # This is so we don't get an error if the dialog box is closed with the 'X' button
            if ((len(values["-INPUT_1_"+str(i_scan)+"-"]) >= 3) and (i_scan<samp_no)):    # This loop advances the cursor when sampleid is input
                    sleep(0.25)
                    pag.press('tab')
                    i_scan = i_scan + 1

        
        if event == '-COMP-':     # Once values are approved, this window will close
            
            
            nums, sampids, m_NMCs, t_NMCs, m_ipas, t_ipas, m_etacacs, t_etacacs, m_sol_als, t_sol_als, stirrs = [],[],[],[],[],[],[],[],[],[],[]

            
            for i_1 in range(1,(samp_no+1)):
                nums.append(str(i_1))
                if (values["-INPUT_1_"+str(i_1)+"-"] == ""):
                    sampids.append(str(i_1))
                else:
                    sampids.append(values["-INPUT_1_"+str(i_1)+"-"])
                m_NMCs.append(str(int(round((float(values["-INPUT_2_"+str(i_1)+"-"])*1000),0))))  # User inputs in g but balance reads in mg, with 0 decimal places (rounded otherwise)
                if (float(values["-INPUT_3_"+str(i_1)+"-"])<1.0):   # Min tol% is 1, so this is used if values input below this
                    t_NMCs.append('1')
                else:
                    t_NMCs.append(str(int(round(float(values["-INPUT_3_"+str(i_1)+"-"]),0))))    # Rounded to 0 decimal places
                m_ipas.append(str(int(round((float(values["-INPUT_4_"+str(i_1)+"-"])*1000),0))))
                if (float(values["-INPUT_5_"+str(i_1)+"-"])<1.0):
                    t_ipas.append('1')
                else:
                    t_ipas.append(str(int(round(float(values["-INPUT_5_"+str(i_1)+"-"]),0))))
                m_etacacs.append(str(int(round((float(values["-INPUT_6_"+str(i_1)+"-"])*1000),0))))
                if (float(values["-INPUT_7_"+str(i_1)+"-"])<1.0):
                    t_etacacs.append('1')
                else:
                    t_etacacs.append(str(int(round(float(values["-INPUT_7_"+str(i_1)+"-"]),0))))
                m_sol_als.append(str(int(round((float(values["-INPUT_8_"+str(i_1)+"-"])*1000),0))))
                if (float(values["-INPUT_9_"+str(i_1)+"-"])<1.0):
                    t_sol_als.append('1')
                else:
                    t_sol_als.append(str(int(round(float(values["-INPUT_9_"+str(i_1)+"-"]),0))))
                if (values["-INPUT_10_"+str(i_1)+"-"] == ""):
                    stirrs.append("None")
                else:
                    stirrs.append(values["-INPUT_10_"+str(i_1)+"-"])
            
            new_dat = [nums, sampids, m_NMCs, t_NMCs, m_ipas, t_ipas, m_etacacs, t_etacacs, m_sol_als, t_sol_als, stirrs]
            
            approval = Check_Dialog(samp_no,Inp_Vals,new_dat,vrbl)
            
            if (approval == True):
                is_complete = True   # Updates approval value to send to other dialog, and closes this window if user submits values
                break
        
        if (event == sg.WIN_CLOSED or event == '-BACK-'):   # If the 'Go Back' button is clicked, this dialog closes and returns to input
            break
            
    window_scan.close()
    
    return(is_complete,new_dat) # Sends whether the values have been approved


def Check_Dialog(samp_n,Inp_Vals,data_Out,vari_pa):
    
    is_accepted = False   # Will update at the end of function if user approves the values
    
    Num_Out = data_Out[0]
    Samp_ID_Out = data_Out[1]
    Mass_NMC_Out = data_Out[2]
    Tol_NMC_Out = data_Out[3]
    Mass_IPA_Out = data_Out[4]
    Tol_IPA_Out = data_Out[5]
    Mass_EtAcAc_Out = data_Out[6]
    Tol_EtAcAc_Out = data_Out[7]
    Mass_Al_Out = data_Out[8]
    Tol_Al_Out = data_Out[9]
    Stirr_Out = data_Out[10]        # Seperates out the columns provided by the input dialog
    

    Full_Rows = []


    for i in range (0,samp_n):      # Places the column elements into rows of an arry which will display as a table table
        Full_Rows.append([Num_Out[i],Inp_Vals[i],\
                          Samp_ID_Out[i],\
                              Mass_NMC_Out[i],Tol_NMC_Out[i],\
                                  Mass_IPA_Out[i],Tol_IPA_Out[i],\
                                      Mass_EtAcAc_Out[i],Tol_EtAcAc_Out[i],\
                                          Mass_Al_Out[i],Tol_Al_Out[i],\
                                              Stirr_Out[i]])

    l1 = sg.Text("Process Parameters for balance input shown below (note g changed to mg), please check and accept or go back", font=('Arial',12))

    header = ['No.',vari_pa,'SampleID','Mass NMC / mg','Tol NMC / %','Mass IPA / mg','Tol IPA / %','Mass EtAcAc / mg','Tol EtAcAc / %', 'Mass Al Sol / mg','Tol Al Sol / %','Stirrer'] # Column headers

    b1 = sg.Button('Go Back', key = '-BACK-')
    b2 = sg.Button('Submit', key = '-SUBMIT-')


    tbl1 = sg.Table(values = Full_Rows,headings = header, auto_size_columns=True, num_rows = len(Inp_Vals), justification='center',key='-TABLE-') # Table to display data
    # Makes a table containing all of the relevant values, to be displayed in the dialog box

    layout = [[l1],[tbl1],[b1,b2]]
    
    if (samp_n<=14):
        win_height = 400
    else:
        win_height = 400 + (11*(samp_n-14))

    window_out = sg.Window('Series Check', layout, size = (1720,win_height),resizable = True)

    while True:
        
        event, values = window_out.read()   # The dialog window is opened here
        
        if event == '-SUBMIT-':     # Once values are approved, this window will close
            is_accepted = True   # Updates approval value to send to other dialog
            break
        
        if (event == sg.WIN_CLOSED or event == '-BACK-'):   # If the 'Go Back' button is clicked, this dialog closes and returns to input
            break
        
    
            
            
            
    window_out.close()

    return(is_accepted) # Sends whether the values have been approved




#------------------------------------------------------------------------------
#------------------------- Main Loop and File Output --------------------------
#------------------------------------------------------------------------------

approval = False

samp_num, Inp_Vals, data_out, r_dat_out, ser_name, approval = SampNum_Dialog() # Runs the first dialog box, where user inputs sample number, which in turn calls other dialog box functions

if approval == True:    # Values will only be sent over the network if the user has confirmed the calculated values

    if(ser_name==''):
        ser_name = str(date.today())+'_'+str(datetime.now().strftime('%H%M%S'))
        send_file_name = 'Sample_Series_'+Method_ID+'_'+ser_name+'.csv'
    else:
        send_file_name = 'Sample_Series_'+Method_ID+'_'+ser_name+'_'+str(date.today())+'.csv'
    
    print('File Created: '+send_file_name+' saved at: '+send_file_path)   # File path includes the date and time so they are easy to tell apart
    sg.popup('File Created: '+send_file_name+', saved at: '+send_file_path)
    
    print("Sample Series Name: "+ser_name)
    
    out_df ={}
    out_df_ext = {} # Second dictionary to contain the data that won't be fed into LabX, at this time, stirrers, (if used)
    
    headings = ['MethodInternalId','SampleSerieName','NumberOfSubstances','SampleSerieId','SampleId1',\
                'Substance1','TargetSubstance1','ToleranceSubstance1',\
                    'Substance2','TargetSubstance2','ToleranceSubstance2',\
                        'Substance3','TargetSubstance3','ToleranceSubstance3',\
                            'Substance4','TargetSubstance4','ToleranceSubstance4',]
        
    substances =["NMC622","IPA Neat","EtAcAc neat","Al Sol"]
        
    
    out_df[headings[0]] = [Method_ID]*samp_num
    out_df[headings[1]] = [ser_name]*samp_num
    out_df[headings[2]] = [str(len(substances))]*samp_num
    out_df[headings[3]] = [Method_ID+"_"+str(date.today())+'_'+str(datetime.now().strftime('%H%M%S'))]*samp_num
    out_df[headings[4]] = data_out[1]
    out_df[headings[5]] = [substances[0]]*samp_num
    out_df[headings[6]] = data_out[2]
    out_df[headings[7]] = data_out[3]
    out_df[headings[8]] = [substances[1]]*samp_num
    out_df[headings[9]] = data_out[4]
    out_df[headings[10]] = data_out[5]
    out_df[headings[11]] = [substances[2]]*samp_num
    out_df[headings[12]] = data_out[6]
    out_df[headings[13]] = data_out[7]
    out_df[headings[14]] = [substances[3]]*samp_num
    out_df[headings[15]] = data_out[8]
    out_df[headings[16]] = data_out[9]
    
    headings_ext = ['SampleID','Stirrer','Temp Setpoint','Stirring Speed','Stirring Time','Calcination temp']

    out_df_ext[headings_ext[0]] = data_out[1]   # Sample IDs
    out_df_ext[headings_ext[1]] = data_out[10]  # Stirrers (if used)
    out_df_ext[headings_ext[2]] = r_dat_out[0]  # Temp setpoint
    out_df_ext[headings_ext[3]] = r_dat_out[1]  # Stirring speed
    out_df_ext[headings_ext[4]] = r_dat_out[2]  # Stirring time
    out_df_ext[headings_ext[5]] = r_dat_out[3]  # Calcination temp

    
    
    df=pd.DataFrame(out_df,columns=headings)
    
    print("Dataframe:")
    print(df)
    
    send_file = df.to_csv((send_file_path+send_file_name),index=False,sep=';',columns=headings) # Makes a new file in the path selected, containing the process parameters
    
    df_ext = pd.DataFrame(out_df_ext,columns=headings_ext)

    print("Dataframe Extra:")
    print(df_ext)

    send_ext_file = df_ext.to_csv((ext_file_path+'Stirr_'+send_file_name),index=True,sep=',',columns=headings_ext) # Makes a new file in the path selected, containing the process parameters


   
    




