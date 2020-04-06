#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2018 5GTANGO, Weidmüller, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Weidmüller, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

"""
    File name: IMMS_APP.py
    Description: Injection Molding Machine Simulator (IMMS)
    Version: 2018-12-28
    Python Version: 3.6.7
    Editor: Spyder, Atom (indentation characters: 4 spaces)
    Maintainer: Marcel Müller <Marcel.Mueller@weidmueller.com>
    Copyright: 2018, Marcel Müller, Weidmüller Group, Detmold, Germany
"""

import math
import re
import os
import sys
import time
import datetime
import threading
#import argparse
from statemachine import StateMachine, State
from flask import Flask, render_template, request
from em63 import rmFile
#import plotly
#import plotly.graph_objs as go
import numpy as np
from opcua import ua, Client, Server
from samba_access import SambaAccess
#import socket # finding ip address used for websocket, get_ip_address
import netifaces as iface # finding ip address used for iface see get_ip_iface
from getnetworks import get_ip_address, get_ip_iface, get_netmask_iface, get_gateway_iface
from manualargs import parse_args
from pi3rgbled import setuppi3rgbled, statusled #setupled, finishedled, alarmled, runled, pauseled, offled

pi3IsEnabled_ini = 1
if pi3IsEnabled_ini == 1:
    setuppi3rgbled_ini = setuppi3rgbled(pi3IsEnabled_ini) # error: -1
    if setuppi3rgbled_ini < 0:
        pi3IsEnabled_ini = 0 # disable
    else:
        pi3IsEnabled_ini = 1 # enable
    print("setup pi3 rgb led ini " + str(setuppi3rgbled_ini))

# if pi3IsEnabled_ini:
#     # sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
#     # sudo python3 neopixeltest1.py
#     # Wiring for Raspberry Pi 3B+ and NeoPixelRing12
#     # PWR to 5V Pin
#     # GND to GND Pin
#     # IN to GPIO21
#     import board
#     import neopixel
#     # import time
#     # The number of NeoPixels
#     pi_num_pixels = 12
#     # Pin for NeoPixels
#     pi_pixels_gpio = board.D21
#     pixels = neopixel.NeoPixel(pi_pixels_gpio, pi_num_pixels)
#     # Define brightness (1,2,..,10)
#     brightled = 1
#     if (brightled<0):
#         brightled = 0
#     if (brightled>10):
#         brightled = 10
#
#     def setupled(wait_periodtime):
#         pauseled(wait_periodtime)
#         return 0
#
#     def finishedled(wait_periodtime):
#         pixels.fill((25*brightled, 25*brightled, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime/2)
#         else:
#             time.sleep(0.5)
#         pixels.fill((0, 0, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime/2)
#         else:
#             time.sleep(0.5)
#         return 0
#
#     def alarmled(wait_periodtime):
#         pixels.fill((25*brightled, 0, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime/2)
#         else:
#             time.sleep(0.5)
#         pixels.fill((0, 0, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime/2)
#         else:
#             time.sleep(0.5)
#         return 0
#
#     def runled(wait_periodtime):
#         pixels.fill((0, 25*brightled, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime)
#         return 0
#
#     def pauseled(wait_periodtime):
#         pixels.fill((25*brightled, 25*brightled, 0))
#         pixels.show()
#         if(wait_periodtime>0):
#             time.sleep(wait_periodtime)
#         return 0
#
#     def offled():
#         pixels.fill((0, 0, 0))
#         pixels.show()
#         return 0

app = Flask(__name__)

# User inputs
# User inputs: variable values
varSetCntMld = 0  # Number of moulds per tool, e.g., 12
varSetCntPrt = 0  # Number of parts to be produced, e.g. 50000 parts
varSetTimCyc = 0  # Cycle time set
# User inputs: variable names
txtSetCntMld = 'SetCntMld'
txtSetCntPrt = 'SetCntPrt'
txtSetTimCyc = 'SetTimCyc'
# User inputs: variable description
desSetCntMld = ',N,5,0,1,"-","Number of Cavities Run";'
desSetCntPrt = ',N,10,0,1,"-","Piece Counter Setpoint";'
desSetTimCyc = ',N,3,2,1,"s","Overall Cycle Time Setpoint.";'

# Only Outputs
# Only Outputs: variable values
varDATE = 0  # HH:MM:SS
varTIME = 0  # YYYYMMDD
varATActSimPara1 = 0  # Constant value from formATActSimPara1
varATActSimPara2 = 0
varActStsMach = '0U000'  # Machine state
varLastActStsMach = '0'
varActCntCyc = 0  # Actual number of cycles already done
varActCntPrt = 0  # Actual number of parts already produced
varActTimCyc = 0  # Actual cycle time
# Only Outputs: variable names
txtDATE = 'DATE'
txtTIME = 'TIME'
txtATActSimPara1 = '@ActSimPara1'
txtATActSimPara2 = '@ActSimPara2'
txtActCntCyc = 'ActCntCyc'
txtActCntPrt = 'ActCntPrt'
txtActStsMach = 'ActStsMach'
txtActTimCyc = 'ActTimCyc'
# Only Outputs: variable desc
desDATE = 'xxx'
desTIME = 'xxx'
desATActSimPara1 = ',N,5,0,0,"-","Actual Simulated Parameter 1";'
desATActSimPara2 = ',N,8,4,0,"-","Actual Simulated Parameter 2";'
desActCntCyc = ',N,10,0,0,"Cycles","Actual Cycle Count";'
desActCntPrt = ',N,10,0,0,"Part","Piece Counter";'
desActStsMach = ',A,5,0,0,"-","Actual Machine Status";'
desActTimCyc = ',N,8,4,0,"s","Actual Cycle Time";'

# Parameters used for creating varATActSimPara2
varATActSimPara2period = 0  # Sine periodic time from formATActSimPara2period
varATActSimPara2amplitude = 0  # Sine amplitude from formATActSimPara2amplitude
varATActSimPara2phase = 0  # Sine phase shift from formATActSimPara2phase
varATActSimPara2offset = 0  # Sine offset from formATActSimPara2offset

varPlotATActSimPara = 0
varFormState = 'none'

varFormEM63path = ''
varFormEM63user = ''
varFormEM63pass = ''
varFormEM63host = ''
varFormEM63hostname = ''

varFormNetworkInterface = ''

session = 0  # Increment session for further em63 sessions

# Get configuration from environment varialbe (or use the old default)
filepathEM63 = os.environ.get("DT_EM63_SHARE", "../em63_share/")

# get and set EM63 connection
#smb_host = os.environ.get("DT_EM63_SHARE_HOST", "10.200.16.17")
smb_host = os.environ.get("DT_EM63_SHARE_HOST", "10.220.0.131")
smb_username = os.environ.get("DT_EM63_USERNAME", "Alice")
smb_hostname = os.environ.get("DT_EM63_HOSTNAME", "IMMS")
smb_password = os.environ.get("DT_EM63_PASSWORD", "") # unused
smb = SambaAccess(smb_host, username=smb_username, hostname=smb_hostname)
smbConnectSuccessful = False # default value

valEM63 = [
        [txtDATE, varDATE, desDATE],
        [txtTIME, varTIME, desTIME],
        [txtATActSimPara1, varATActSimPara1, desATActSimPara1],
        [txtATActSimPara2, varATActSimPara2, desATActSimPara2],
        [txtActCntCyc, varActCntCyc, desActCntCyc],
        [txtActCntPrt, varActCntPrt, desActCntPrt],
        [txtActStsMach, varActStsMach, desActStsMach],
        [txtActTimCyc, varActTimCyc, desActTimCyc],
        [txtSetCntMld, varSetCntMld, desSetCntMld],
        [txtSetCntPrt, varSetCntPrt, desSetCntPrt],
        [txtSetTimCyc, varSetTimCyc, desSetTimCyc]
        ]


# Create static content for GETID
txtGETID = ''
for index in range(2, len(valEM63)):
    txtGETID = txtGETID + valEM63[index][0] + valEM63[index][2] + '\n'

# Static Content for GETINFO
txtGETINFO = """MachVendor,	"Weidmueller";
MachNbr,	        "00001";
MachDesc,	        "Weidmueller IMM Simulator";
ContrType,	        "WIMMS";
ContrVersion,	    "1.0";
Version,	        "2020-02-07";
MaxJobs,	        3;
MaxEvents,
	CHANGES	        0
	CURRENT_ALARMS	0
	ALARMS	        0;
MaxReports,	        3;
MaxArchives,	    0;
InjUnitNbr,	        ;
MaterialNbr,	    ;
CharDef,	        "850";
MaxSessions,	    3;
ActiveJobs,	        ;
ActiveReports,	    ;
ActiveEvents,	    ;
"""

OPCUA_HOST = os.environ.get("OPCUA_HOST", "0.0.0.0")
OPCUA_PORT = os.environ.get("OPCUA_PORT", "4840")

opcuaIsEnabled = False # default value; is enabled by argument --enableOPCUA
sambaIsEnabled = True # default value; enable euromap 63 via samba
playbackIsEnabled = False # Playback  mode
tocuh5inchIsEnabled = False # default value; no 5 inch touch is used
pi3IsEnabled = False # default value; no raspberry pi 3 is used with RGB LED

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    return render_template('setup.html', varActStsMach=varActStsMach,
    varSetCntPrt=varSetCntPrt, varSetCntMld=varSetCntMld,
    varSetTimCyc=varSetTimCyc, playbackIsEnabled=playbackIsEnabled)

@app.route('/configuration', methods=['GET', 'POST'])
def configuration():
    # Check IP for ext. network
    my_ip_1 = get_ip_address("www.weidmueller.com")
    #if (my_ip_1 == -1):
    #    print("No DNS or no network or no route.")
    #    my_ip_1 = "localhost"
    # Check IP for int. network
    my_ip_2 = get_ip_address("10.220.0.2")
    #if (my_ip_2 == -1):
    #    print("No network or no route.")
    #    my_ip_2 = "localhost"

    # List the network interfaces that are available
    try:
        my_interfaces = iface.interfaces()
        print("Interfaces: " + str(my_interfaces))
    except:
        my_interfaces = -1
    # Check if the network list is filled and use one entry
    # Use which is defined by web gui; default: the first in the list
    # e.g. ['lo', 'enp0s31f6', 'wwp0s20f0u6', 'wlp61s0', 'docker0']
    if ((my_interfaces != -1) and (my_interfaces != '')):
        if ((varFormNetworkInterface != '') and (varFormNetworkInterface in my_interfaces)):
            my_interface_0 = varFormNetworkInterface
        else:
            my_interface_0 = my_interfaces[0]
        # Request IP, Subnetmask and def. gateway of interface selected
        if (my_interface_0 in my_interfaces):
            my_ip_0 = get_ip_iface(my_interface_0)
            my_netmask_0 = get_netmask_iface(my_interface_0)
            my_gateway_0 = get_gateway_iface(my_interface_0)
            print("Interface: " + str(my_interface_0))
            print("IP: " + str(my_ip_0))
            print("Subnet mask: " + str(my_netmask_0))
            print("Default gateway: " + str(my_gateway_0))
    # default if no list of network interfaces is available
    else:
        my_interface_0 = -1
        my_ip_0 = -1
        my_netmask_0 = -1
        my_gateway_0 = -1
        print("Interface: " + str(my_interface_0))
        print("IP: " + str(my_ip_0))
        print("Subnet mask: " + str(my_netmask_0))
        print("Default gateway: " + str(my_gateway_0))

    return render_template('configuration.html', varActStsMach=varActStsMach,
    opcuaIsEnabled=opcuaIsEnabled, smbConnectSuccessful=smbConnectSuccessful,
    sambaIsEnabled=sambaIsEnabled,
    my_interface_0=my_interface_0, my_ip_0=my_ip_0, my_netmask_0=my_netmask_0,
    my_gateway_0=my_gateway_0, my_ip_1=my_ip_1, my_ip_2=my_ip_2,
    filepathEM63=filepathEM63, smb_host=smb_host, smb_username=smb_username,
    smb_hostname=smb_hostname, smb_password=smb_password,
    txtGETID=txtGETID, txtGETINFO=txtGETINFO, my_interfaces=my_interfaces)


@app.route('/monitoring')
def monitoring():
    return render_template('monitoring.html',varSetCntPrt=varSetCntPrt,
    varSetCntMld=varSetCntMld, varSetTimCyc=varSetTimCyc,
    varATActSimPara1=varATActSimPara1, varATActSimPara2=varATActSimPara2,
    varActStsMach=varActStsMach, varActCntCyc=varActCntCyc,
    varActCntPrt=varActCntPrt, varActTimCyc=varActTimCyc,
    varDATE=varDATE, varTIME=varTIME)


#@app.route('/plotActSimPara')
#def plotActSimPara():
#    return render_template('plotActSimPara.html')


#@app.route('/plotActCntCyc')
#def plotActCntCyc():
#    return render_template('plotActCntCyc.html')


@app.route('/resultSimPara', methods=['GET', 'POST'])
def resultSimPara():
    global varATActSimPara1
    global varATActSimPara2period, varATActSimPara2amplitude
    global varATActSimPara2phase, varATActSimPara2offset, varPlotATActSimPara
    #if request.form['formPlotATActSimPara'] == '1':
    #    varPlotATActSimPara = 1
    #else:
    varPlotATActSimPara = 0
    varATActSimPara1 = int(request.form['formATActSimPara1'])
    varATActSimPara2period = float(request.form['formATActSimPara2period'])
    varATActSimPara2amplitude = \
        float(request.form['formATActSimPara2amplitude'])
    varATActSimPara2phaseStr = request.form['formATActSimPara2phase']
    if varATActSimPara2phaseStr == '-pi':
        varATActSimPara2phase = -1*math.pi
    elif varATActSimPara2phaseStr == '-pi/2':
        varATActSimPara2phase = -1*math.pi/2
    elif varATActSimPara2phaseStr == '-pi/4':
        varATActSimPara2phase = -1*math.pi/4
    elif varATActSimPara2phaseStr == '0':
        varATActSimPara2phase = 0.0
    elif varATActSimPara2phaseStr == 'pi/2':
        varATActSimPara2phase = math.pi/2
    elif varATActSimPara2phaseStr == 'pi/4':
        varATActSimPara2phase = math.pi/4
    elif varATActSimPara2phaseStr == 'pi':
        varATActSimPara2phase = math.pi
    else:
        varATActSimPara2phase = 0

    varATActSimPara2offset = float(request.form['formATActSimPara2offset'])
    print("@ActSimPara1 = ", varATActSimPara1)
    print("@ActSimPara2_period = ", varATActSimPara2period)
    print("@ActSimPara2_amplitude = ", varATActSimPara2amplitude)
    print("@ActSimPara2_phase = ", varATActSimPara2phaseStr)
    print("@ActSimPara2_phase (DEZ) = ", varATActSimPara2phase)
    print("@ActSimPara2_offset = ", varATActSimPara2offset)
    return render_template("result.html", result=result)


@app.route('/resultSetup', methods=['GET', 'POST'])
def result():
    global varActStsMach, varSetCntMld, varSetCntPrt, varSetTimCyc
    varSetCntMld = int(request.form['formSetCntMld'])
    varSetCntPrt = int(request.form['formSetCntPrt'])
    varSetTimCyc = float(request.form['formSetTimCyc'])
    print("SetCntMld = ", varSetCntMld)
    print("SetCntPrt = ", varSetCntPrt)
    print("SetTimCyc = ", varSetTimCyc)
    return render_template("result.html", result=result)


@app.route('/resultState', methods=['GET', 'POST'])
def resultState():
    global varFormState
    varFormState = request.form['formState']
    print("varFormState = ", varFormState)
    return render_template("result.html", result=result)


@app.route('/resultNetwork', methods=['GET', 'POST'])
def resultNetwork():
    print("Currently not supported. Please use /etc/network/interfaces")
    return render_template("result.html", result=result)

@app.route('/resultNetworkInterface', methods=['GET', 'POST'])
def resultNetworkInterface():
    global varFormNetworkInterface
    varFormNetworkInterface = request.form['formNetworkInterace']
    print("Interface selected: " + str(varFormNetworkInterface))
    return render_template("resultConfig.html", result=result)

@app.route('/resultEM63', methods=['GET', 'POST'])
def resultEM63():
    global varFormEM63path, varFormEM63user, varFormEM63pass, filepathEM63, varFormEM63host, varFormEM63hostname
    varFormEM63path = request.form['formEM63path']
    print("EM63 Path = ", varFormEM63path)
    if sambaIsEnabled:
        varFormEM63user = request.form['formEM63user']
        varFormEM63pass = request.form['formEM63pass']
        varFormEM63host = request.form['formEM63host']
        varFormEM63hostname = request.form['formEM63hostname']
        print("EM63 Host = ", varFormEM63host)
        print("EM63 Hostname = ", varFormEM63hostname)
        print("EM63 User = ", varFormEM63user)
        print("EM63 Pass = ", varFormEM63pass)
    return render_template("result.html", result=result)


def _start_flask():
    # Make the server configurable through environment variables
    # Default localhost: http://127.0.0.1:5000
    listen_host = os.environ.get("DT_WEB_LISTEN", "127.0.0.1")
    listen_port = os.environ.get("DT_WEB_PORT", 5000)
    app.run(host=listen_host, port=listen_port)
    return


def start_webapp():
    thread = threading.Thread(target=_start_flask)
    thread.daemon = True
    thread.start()
    return


def _start_EM63():
    while True:
        run_EM63(samba=sambaIsEnabled)
        time.sleep(.2)  # lets sleep a bit, to not utilize our CPU for 100% with this thread


def start_EM63():
    thread2 = threading.Thread(target=_start_EM63)
    thread2.daemon = True
    thread2.start()
    return


def _start_OPCUA_server():
    run_OPCUA_server_start()

def start_OPCUA_server():
    thread3 = threading.Thread(target=_start_OPCUA_server)
    thread3.daemon = True
    thread3.start()
    return


def _start_OPCUA_client():
    # Set OPC UA server address and port or use defaults
    client = Client("opc.tcp://%s:%s/freeopcua/server/" % (OPCUA_HOST, OPCUA_PORT))
    client.connect()
    root = client.get_root_node()
    imms = root.get_child(["0:Objects", "2:IMMS"])
    while True:
        run_OPCUA_write_updates(imms)
        time.sleep(.2)  # lets sleep a bit, to not utilize our CPU for 100% with this thread

def start_OPCUA_client():
    thread3 = threading.Thread(target=_start_OPCUA_client)
    thread3.daemon = True
    thread3.start()
    return

def _start_rgb_led():
    # Signals machine status via RGB LED NeoPixel ring
    global varActStsMach, varLastActStsMach
    while True:
        # Check if status is changed; change led if changed or blink is needed
        if (varActStsMach == varLastActStsMach):
            if (varActStsMach == '0H000' or varActStsMach == '0C000'):
                statusled(varActStsMach)
            else:
                time.sleep(1)  # lets sleep a bit
        else:
            statusled(varActStsMach)
            varLastActStsMach=varActStsMach



def start_rgb_led():
    thread4 = threading.Thread(target=_start_rgb_led)
    thread4.daemon = True
    thread4.start()

def make_ATActSimPara2(t1):
    global varATActSimPara2period, varATActSimPara2amplitude
    global varATActSimPara2phase, varATActSimPara2offset
    if varATActSimPara2period != 0:
        varATActSimPara2 = varATActSimPara2amplitude * \
            math.sin(2 * math.pi / varATActSimPara2period * t1 +
                     varATActSimPara2phase) + varATActSimPara2offset
    else:
        varATActSimPara2 = 0
    varATActSimPara2 = format(varATActSimPara2, '8.4f')
    return varATActSimPara2


def production():
    global varActStsMach, varSetCntMld, varSetCntPrt, varSetTimCyc
    global varActCntPrt, varActCntCyc, varATActSimPara2, varActTimCyc
    global varFormState
    if 0 < 1:
        if varFormState == 'formStatepause':
            return IMM1.e_pause()
        if varFormState == 'formStateerror':
            return IMM1.e_error()
        #if varPlotATActSimPara == 1:
            # List for graph plottig
        #    sinPlotX = []
        #    sinPlotY = []
        #    sinPlotY2 = []
        #    sinPlotY3 = []
        while varActCntPrt < varSetCntPrt:
            varActStsMach = '0A000'
            #if pi3IsEnabled:
            #    runled(0)
            if varFormState == 'formStatepause':
                return IMM1.e_pause()
            if varFormState == 'formStateerror':
                return IMM1.e_error()
            # Start Timer for ActTimCyc
            # time.clock()works on win (is wall-clock),
            # but not linux because sleep time is not counted => time.monotonic
            t1 = time.monotonic()
            # Sine function for @ActSimPara2
            varATActSimPara2 = make_ATActSimPara2(t1)
            # if varPlotATActSimPara == 1:
                # Append content to list for graph plotting
                # sinPlotX.append(float(t1))
                # sinPlotX.append(datetime.datetime.now())
                # sinPlotY.append(float(varATActSimPara2))
                # sinPlotY2.append(float(varATActSimPara1))
                # sinPlotY3.append(float(varActTimCyc))

            # Sleep for cycle time simulation
            time.sleep(varSetTimCyc)
            # Part/Cycle counter
            varActCntCyc = varActCntCyc + 1
            varActCntPrt = int(varSetCntMld * varActCntCyc)
            # Stop Timer for ActTimCyc
            t2 = time.monotonic()
            dt = t2 - t1
            varActTimCyc = format(dt, '8.4f')
            valEM63print()
#            if varPlotATActSimPara == 1:
#                plotAllLocal(sinPlotX, sinPlotY, sinPlotY2, sinPlotY3)
            if varActCntPrt >= varSetCntPrt:
                print("Job finished...")
                return


def finished():
    global varFormState, varActStsMach, varSetCntMld, varSetCntPrt
    global varSetTimCyc, varActCntPrt, varActCntCyc, varActTimCyc
    while 0 < 1:
        if varFormState == 'formStateidle':
            varFormState = 'none'
            varSetCntMld = 0
            varSetCntPrt = 0
            varSetTimCyc = 0
            varActCntCyc = 0
            varActCntPrt = 0
            varActTimCyc = 0
            return
        else:
            #if pi3IsEnabled:
            #    finishedled(1)
            #else:
            time.sleep(1)  # waiting


# Check if necessary or not
# def errorState():
#    while 0<1:
#        if varFormState == 'formStateproduction':
#            #IMM1.e_confirm()
#            return;
#        else:
#            time.sleep(1)
#
# def pauseState():
#    while 0<1:
#        if varFormState == 'formStateproduction':
#            #IMM1.e_proceed()
#            return;
#        else:
#            time.sleep(1)
#
# def machineSetup():
#    while 0<1:
#        if varFormState == 'formStateproduction':
#            return;
#        else:
#            time.sleep(1)


def valEM63refresh():
    global varActStsMach, varSetCntMld, varSetCntPrt, varSetTimCyc
    global varActCntPrt, varActCntCyc, varActTimCyc, valEM63
    global varATActSimPara1, varATActSimPara2
    valEM63[0][1] = varDATE
    valEM63[1][1] = varTIME
    valEM63[2][1] = varATActSimPara1
    valEM63[3][1] = varATActSimPara2
    valEM63[4][1] = varActCntCyc
    valEM63[5][1] = varActCntPrt
    valEM63[6][1] = varActStsMach
    valEM63[7][1] = varActTimCyc
    valEM63[8][1] = varSetCntMld
    valEM63[9][1] = varSetCntPrt
    valEM63[10][1] = varSetTimCyc
    return


def valEM63print():
    global varActStsMach, varSetCntMld, varSetCntPrt, varSetTimCyc
    global varActCntPrt, varActCntCyc, varActTimCyc
    global valEM63, varATActSimPara1, varATActSimPara2
    print("---------------------------------------------")
    print("DATE = ", varDATE)
    print("TIME = ", varTIME)
    print("@ActSimPara1 = ", varATActSimPara1)
    print("@ActSimPara2 = ", varATActSimPara2)
    print("ActCntCyc = ", varActCntCyc)
    print("ActCntPrt = ", varActCntPrt)
    print("ActStsMach = ", varActStsMach)
    print("ActTimCyc = ", varActTimCyc)
    print("SetCntMld = ", varSetCntMld)
    print("SetCntPrt = ", varSetCntPrt)
    print("SetTimCyc = ", varSetTimCyc)
    print("\n")
    sys.stdout.flush()
    return


# auxiliary file access functions to use within run_EM63 to facilitate access to either local files or Samba
def remove_prefix(filepath, prefix=filepathEM63):
    """Return filename without prefix. Necessary for Samba connections"""
    if filepath.startswith(prefix):
        print("Removing prefix {} from {} for Samba interaction".format(prefix, filepath))
        return filepath[len(prefix):]
    return filepath


def file_exists(filepath, samba=False):
    """Return if the specified file exists"""
    global smbConnectSuccessful
    if samba:
        filename = remove_prefix(filepath)
        exists = smb.exists_file(filename)
        smbConnectSuccessful=True
    else:
        exists = os.path.exists(filepath)
        smbConnectSuccessful=False
    print("Check if {} exists: {}".format(filepath, exists))
    return exists


def file_read(filepath, readlines=False, samba=False):
    """Open, read file and return file contents. If readlines, return list of lines instead of single string"""
    print("Reading {} with readlines={} and samba={}".format(filepath, readlines, samba))
    if samba:
        filename = remove_prefix(filepath)
        return smb.get_file_content(filename, readlines=readlines)

    with open(filepath, 'r') as f:
        if readlines:
            content = f.readlines()
        else:
            content = f.read()
        return content


def file_write(filepath, text, samba=False):
    """Write text to file. Either append or overwrite."""
    print("Writing to {} Text: {}".format(filepath, text))
    if samba:
        filename = remove_prefix(filepath)
        smb.write_file(filename, text)
    else:
        with open(filepath, 'w+') as f:
            f.write(text)


def file_delete(filepath, samba=False):
    """Delete specified file"""
    print("Deleting file {}".format(filepath))
    if samba:
        filename = remove_prefix(filepath)
        smb.delete_file(filename)
    else:
        rmFile(filepath)


def run_EM63(samba=True):
    """If samba=False, read/write files from local (mounted) file system, else connect via Samba"""
    global varDATE, varTIME, filepathEM63, varFormEM63path, session, valEM63, varFormEM63host, varFormEM63hostname, varFormEM63user, varFormEM63pass, smb_host, smb_hostname, smb_username, smb_password, smb
    session = session + 1
    if session > 3:
        session = 1

    valEM63refresh()

    varDATE = datetime.datetime.now().strftime("%Y%m%d")
    varTIME = datetime.datetime.now().strftime("%H:%M:%S")

    if ((filepathEM63 != varFormEM63path) and varFormEM63path != ''):
        filepathEM63 = varFormEM63path
        print("EM63 path changed")
    varFormEM63path = ''

    if ((smb_host != varFormEM63host) and varFormEM63host != ''):
        smb_host = varFormEM63host
        print("EM63 Smb host changed")
        smb = SambaAccess(smb_host, username=smb_username, hostname=smb_hostname)
        print(smb)
    varFormEM63host = ''

    if ((smb_hostname != varFormEM63hostname) and varFormEM63hostname != ''):
        smb_hostname = varFormEM63hostname
        print("EM63 Smb hostname changed")
        smb = SambaAccess(smb_host, username=smb_username, hostname=smb_hostname)
    varFormEM63hostname = ''

    if ((smb_username != varFormEM63user) and varFormEM63user != ''):
        smb_username = varFormEM63user
        print("EM63 Smb user changed")
        smb = SambaAccess(smb_host, username=smb_username, hostname=smb_hostname)
    varFormEM63user = ''

    if ((smb_password != varFormEM63pass) and varFormEM63pass != ''):
        smb_password = varFormEM63pass
        print("EM63 Smb password changed")
        smb = SambaAccess(smb_host, username=smb_username, hostname=smb_hostname)
    varFormEM63pass = ''

    if filepathEM63 == '':
        print("EM63 path is not defined.")
        time.sleep(2)
        return
    else:
        # print("EM63 path is defined: " + filepathEM63)
        if filepathEM63.startswith('/') and not filepathEM63.endswith('/'):
            print("EM63 path needs / ")
            filepathEM63 = filepathEM63 + "/"
        # check if the local directory exists
        if not file_exists(filepathEM63, samba=False):
            print("EM63 path " + filepathEM63 + " does not exist.")
            time.sleep(2)
            return
        # else:
            # print("EM63 path exists.")

    # Open SESSnnnn.REQ file if it exists
    reqFile = filepathEM63 + "SESS" + str(session).zfill(4) + '.REQ'
    # print(reqFile)
    if file_exists(reqFile, samba=samba):
        print("---------------------------------------------")
        print("Request file found: "+reqFile+". Processing ...")
        reqFileContent = file_read(reqFile, samba=samba)

        # Extract Job file name from REQ file
        try:
            jobFile = re.search('"(.+?)"', reqFileContent).group(1)
            print("Job file name found: "+jobFile+".")
        except AttributeError:
            # ", " not found in the original string
            jobFile = ''
            print("No job file name found. Error ...")
        file_delete(reqFile, samba=samba)
    else:
        return

    # Look for job file named
    jobFile = filepathEM63 + jobFile
    if file_exists(jobFile, samba=samba):
        print("Job file found: "+jobFile+". Processing ...")
        jobFileLines = file_read(jobFile, readlines=True, samba=samba)
        # print(jobFileLines)
        # rmFile(jobFile)

        # Extract instructions from job file
        txtLOG = ''
        for line in jobFileLines:
            # GETID
            if 'GETID ' in line:
                # Extract target file name from line
                datFile = re.search('"(.+?)"', line).group(1)
                datFile = filepathEM63 + datFile
                file_write(datFile, txtGETID, samba=samba)
                txtLOG = 'COMMAND 2 PROCESSED "GETID command" ' \
                    + str(varDATE) + ' ' + str(varTIME) + ';'
                # print(txtLOG)

            # GETINFO
            if 'GETINFO ' in line:
                # Extract target file name from line
                datFile = re.search('"(.+?)"', line).group(1)
                datFile = filepathEM63 + datFile
                # Check if local copy of GETINFO.DAT exists: GETINFO.conf
                #if file_exists("GETINFO.conf", samba=samba):
                    # use it
                #    confFileBody = file_read('GETINFO.conf', samba=samba)
                #    file_write(datFile, confFileBody, samba=samba)
                #else:
                file_write(datFile, txtGETINFO, samba=samba)
                txtLOG = 'COMMAND 2 PROCESSED "GETINFO command" ' \
                    + str(varDATE) + ' ' + str(varTIME) + ';'
                # print(txtLOG)

            # REPORT
            if 'REPORT ' in line:
                # Extract target file name from line
                datFile = re.search('"(.+?)"', line).group(1)
                datFile = filepathEM63 + datFile
                # Write only parameters requested
                txtREPORT = ''
                valREPORT = ''
                for line2 in jobFileLines:
                    for index in range(len(valEM63)):
                        if valEM63[index][0] in line2:
                            # print(valEM63[index][0], line2)
                            newline2 = line2
                            newline2 = newline2.replace(",", "")
                            newline2 = newline2.replace(" ", "")
                            newline2 = newline2.replace("\n", "")
                            # print(valEM63[index][0], newline2)
                            if newline2 in valEM63[index][0]:
                                # Use EM63 parameter names
                                txtREPORT = txtREPORT + valEM63[index][0]
                                if index < len(valEM63):
                                    txtREPORT = txtREPORT + ','
                                # Use EM63 parameter values
                                valREPORT = valREPORT + str(valEM63[index][1])
                                if index < len(valEM63):
                                    valREPORT = valREPORT + ','
                txtREPORT = txtREPORT + '\n' + valREPORT + ';'
                txtREPORT = txtREPORT.replace(",\n", "\n")
                txtREPORT = txtREPORT.replace(",;", "")
                file_write(datFile, txtREPORT, samba=samba)
                txtLOG = 'COMMAND 2 PROCESSED "REPORT command" ' \
                    + str(varDATE) + ' ' + str(varTIME) + ';'
                # print(txtLOG)

            # Create LOG file
            if 'RESPONSE ' in line:
                # Write log file
                # Extract target file name from line for log file
                logFile = re.search('"(.+?)"', line).group(1)
                logFile = filepathEM63 + logFile
                if logFile != '':
                    txtLOG0 = 'COMMAND 1 PROCESSED "JOB command" ' \
                        + str(varDATE) + ' ' + str(varTIME) + ';\n'
                    if file_exists(logFile, samba=samba):
                        file_delete(logFile, samba=samba)
                    # if txtLOG != '' and txtLOG0 != '':
                    txtLOG0 = txtLOG0 + txtLOG
                    file_write(logFile, txtLOG0, samba=samba)
                    # print("Log file was written: ", logFile)

        # Create RSP file
        rspFile = filepathEM63 + "SESS" + str(session).zfill(4) + '.RSP'
        txtRSP = '00000001 PROCESSED "EXECUTE ' + jobFile + '";'
        file_write(rspFile, txtRSP, samba=samba)
        print("Response file was written: ", rspFile)
        sys.stdout.flush()


def run_OPCUA_server_start():
    global opcuaIsEnabled
    opcuaIsEnabled = True
    print("Starting OPC UA SERVER %s:%s" % (OPCUA_HOST, OPCUA_PORT))
    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://%s:%s/freeopcua/server/" % (OPCUA_HOST, OPCUA_PORT))

    # setup our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our nodes
    objects = server.get_objects_node()

    # populating our address space
    imms = objects.add_object(idx, "IMMS")

    imms_date = imms.add_variable(idx, "DATE", 0, varianttype=ua.VariantType.Double)
    imms_date.set_writable()

    imms_time = imms.add_variable(idx, "TIME", "", varianttype=ua.VariantType.String)
    imms_time.set_writable()

    imms_ActSimPara1 = imms.add_variable(idx, "ActSimPara1", 0, varianttype=ua.VariantType.Double)
    imms_ActSimPara1.set_writable()

    imms_ActSimPara2 = imms.add_variable(idx, "ActSimPara2", 0, varianttype=ua.VariantType.Double)
    imms_ActSimPara2.set_writable()

    imms_ActCntCyc = imms.add_variable(idx, "ActCntCyc", 0, varianttype=ua.VariantType.Double)
    imms_ActCntCyc.set_writable()

    imms_ActCntPrt = imms.add_variable(idx, "ActCntPrt", 0, varianttype=ua.VariantType.Double)
    imms_ActCntPrt.set_writable()

    imms_ActStsMach = imms.add_variable(idx, "ActStsMach", "", varianttype=ua.VariantType.String)
    imms_ActStsMach.set_writable()

    imms_ActTimCyc = imms.add_variable(idx, "ActTimCyc", 5, varianttype=ua.VariantType.Double)
    imms_ActTimCyc.set_writable()

    imms_SetCntMld = imms.add_variable(idx, "SetCntMld", 0, varianttype=ua.VariantType.Double)
    imms_SetCntMld.set_writable()

    imms_SetCntPrt = imms.add_variable(idx, "SetCntPrt", 0, varianttype=ua.VariantType.Double)
    imms_SetCntPrt.set_writable()

    imms_SetTimCyc = imms.add_variable(idx, "SetTimCyc", 0, varianttype=ua.VariantType.Double)
    imms_SetTimCyc.set_writable()

    # starting!
    server.start()


def run_OPCUA_write_updates(imms):
    # write values to OPC UA server
    global varActStsMach, varSetCntMld, varSetCntPrt, varSetTimCyc
    global varActCntPrt, varActCntCyc, varActTimCyc
    global valEM63, varATActSimPara1, varATActSimPara2
    imms.get_variables()[0].set_data_value(varDATE)
    imms.get_variables()[1].set_data_value(varTIME)
    imms.get_variables()[2].set_data_value(varATActSimPara1)
    imms.get_variables()[3].set_data_value(varATActSimPara2)
    imms.get_variables()[4].set_data_value(varActCntCyc)
    imms.get_variables()[5].set_data_value(varActCntPrt)
    imms.get_variables()[6].set_data_value(varActStsMach)
    imms.get_variables()[7].set_data_value(varActTimCyc)
    imms.get_variables()[8].set_data_value(varSetCntMld)
    imms.get_variables()[9].set_data_value(varSetCntPrt)
    imms.get_variables()[10].set_data_value(varSetTimCyc)
    return


class vIMM(StateMachine):
    # Simplified IMM states
    s_idle = State('Idle', initial=True)
    s_setup = State('Set up')
    s_production = State('Production')
    s_error = State('Machine Error')
    s_pause = State('Pause')
    s_finished = State('Job Completed')

    # Simplified IMM transitions/events
    # e_EVENT = s_fromSTATE.to(s_toSTATE)
    e_setting = s_idle.to(s_setup)
    e_start = s_setup.to(s_production)
    e_proceed = s_pause.to(s_production)
    e_confirm = s_error.to(s_production)
    e_error = s_production.to(s_error)
    e_pause = s_production.to(s_pause)
    e_finished = s_production.to(s_finished)
    e_reset = s_finished.to(s_idle)

    def on_enter_s_idle(self):
        global varActStsMach, varActCntPrt, varActCntCyc, varSetCntMld
        global varSetCntPrt, varSetTimCyc, varActTimCyc
        varActStsMach = '0I000'
        varSetCntMld = 0
        varSetCntPrt = 0
        varSetTimCyc = 0
        varActCntCyc = 0
        varActCntPrt = 0
        varActTimCyc = 0

        #if pi3IsEnabled:
        #    offled()
        return

    def on_enter_s_setup(self):
        # Initial parameters set by API
        global varActStsMach, varFormState
        varActStsMach = '0U000'
        #if pi3IsEnabled:
        #    setupled(0)
        return

    def on_enter_s_production(self):
        global varActStsMach
        varActStsMach = '0A000'
        return

    def on_enter_s_error(self):
        global varActStsMach
        varActStsMach = '0C001'
        print("State: error ...")
        return

    def on_enter_s_pause(self):
        global varActStsMach
        varActStsMach = '0H000'
        print("State: pause ...")
        return

    def on_s_error(self):
        while 0 < 1:
            if varFormState == 'formStateproduction':
                self.e_confirm()
            else:
                #if pi3IsEnabled:
                #    alarmled(1)
                #else:
                time.sleep(1)

    def on_s_pause(self):
        while 0 < 1:
            if varFormState == 'formStateproduction':
                self.e_proceed()
            else:
                #if pi3IsEnabled:
                #    pauseled(1)
                #else:
                time.sleep(1)

    def on_enter_s_finished(self):
        global varActStsMach
        varActStsMach = '0C000'
        print("Job finished... Restart?")
        finished()
        return


def waitForProduction():
    global varFormState
    while 0 < 1:
        if varFormState == 'formStateproduction':
            return
        else:
            time.sleep(1)


def autostart_production(args):
    """
    Autostart the production based on the
    given command line arguments.
    """
    global varATActSimPara1, varATActSimPara2period, varATActSimPara2amplitude
    global varATActSimPara2phase, varATActSimPara2phaseStr
    global varATActSimPara2offset
    global varSetCntMld, varSetCntPrt, varSetTimCyc, varFormState
    print("Autostarting the production ...")
    # Set variables based on args: simulation parameter
    varATActSimPara1 = int(args.varATActSimPara1)
    varATActSimPara2period = float(args.varATActSimPara2period)
    varATActSimPara2amplitude = float(args.varATActSimPara2amplitude)
    varATActSimPara2phase = float(args.varATActSimPara2phase)
    varATActSimPara2phaseStr = str(args.varATActSimPara2phase)
    varATActSimPara2offset = float(args.varATActSimPara2offset)
    # Set variables based on args: production params
    varSetCntMld = int(args.varSetCntMld)
    varSetCntPrt = int(args.varSetCntPrt)
    varSetTimCyc = float(args.varSetTimCyc)
    # Set variables based on args: finally go to productions state
    varFormState = "formStateproduction"


# #
# # Command line argument parser
# #
# def parse_args(manual_args=None):
#     """
#     CLI interface definition.
#     """
#     parser = argparse.ArgumentParser(
#         description="IMMS ('Injection Molding Machine Simulator' Application)")
#
#     parser.add_argument(
#         "-a",
#         "--autostart",
#         help="Automatically start production.",
#         required=False,
#         default=False,
#         dest="autostart",
#         action="store_true")
#
#     parser.add_argument(
#         "-p",
#         "--playback",
#         help="Playback of production data recorded.",
#         required=False,
#         default=False,
#         dest="playback",
#         action="store_true")
#
#     parser.add_argument(
#         "--varATActSimPara1",
#         required=False,
#         default=5)
#
#     parser.add_argument(
#         "--varATActSimPara2period",
#         required=False,
#         default=20.0)
#
#     parser.add_argument(
#         "--varATActSimPara2amplitude",
#         required=False,
#         default=1.0)
#
#     parser.add_argument(
#         "--varATActSimPara2phase",
#         required=False,
#         default=0)
#
#     parser.add_argument(
#         "--varATActSimPara2offset",
#         required=False,
#         default=1.0)
#
#     parser.add_argument(
#         "--varPlotATActSimPara",
#         required=False,
#         default=False)
#
#     parser.add_argument(
#         "--varSetCntMld",
#         required=False,
#         default=10)
#
#     parser.add_argument(
#         "--varSetCntPrt",
#         required=False,
#         default=10000)
#
#     parser.add_argument(
#         "--varSetTimCyc",
#         required=False,
#         default=5.0)
#
#     parser.add_argument(
#         "--enableOPCUA",
#         help="Enable OPC UA client.",
#         required=False,
#         default=False,
#         dest="enableOPCUA",
#         action="store_true")
#
#     parser.add_argument(
#         "--enablePi3",
#         help="Enable RGB LED control via Raspberry Pi 3 GPIOs.",
#         required=False,
#         default=False,
#         dest="enablePi3",
#         action="store_true")
#
#     parser.add_argument(
#         "--enable5inchTouch",
#         help="Enable optimized web gui for 5 inch touch screen.",
#         required=False,
#         default=False,
#         dest="enable5inchTouch",
#         action="store_true")
#
#     parser.add_argument(
#         "--disableSamba",
#         help="Disable Euromap 63 via Samba. Default share: ../em63_share/.",
#         required=False,
#         default=False,
#         dest="disableSamba",
#         action="store_true")
#
#     if manual_args is not None:
#         return parser.parse_args(manual_args)
#     return parser.parse_args()


def main():
    # Parse CLI arguments
    args = parse_args()
    print("Starting IMMS with arguments: {}".format(args))
    # Instantiate
    # IMM1 = vIMM()
    start_webapp()

    if args.disableSamba:
        global sambaIsEnabled
        sambaIsEnabled = False

    start_EM63()

    if args.playback:
        global playbackIsEnabled, txtGETID, txtGETINFO
        playbackIsEnabled = True
        print("Playback is enabled.")
        # open getid file for the playback
        if file_exists("../em63_playback/em63_playback_getid.dat"):
            txtGETID = file_read('../em63_playback/em63_playback_getid.dat')
        else:
            txtGETID = "No getid file found for playback."
            print(txtGETID)
        # open getinfo file for the playback
        if file_exists("../em63_playback/em63_playback_getinfo.dat"):
            # use it
            txtGETINFO = file_read('../em63_playback/em63_playback_getinfo.dat')
        else:
            txtGETINFO = "No getinfo file found for playback."
            print(txtGETINFO)

    if args.enableOPCUA:
        if (playbackIsEnabled == False):
            start_OPCUA_server()
            time.sleep(3) # wait for OPC UA server to start
            start_OPCUA_client()
        else:
            print("Playback is enabled. OPC UA is currently not supported for playback.")

    if args.enable5inchTouch:
        global tocuh5inchIsEnabled
        tocuh5inchIsEnabled = True
        print("Support for 5 inch touch screen is enabled.")

    if args.enablePi3:
        global pi3IsEnabled, pi3IsEnabled_ini
        if pi3IsEnabled_ini:
            pi3IsEnabled = True
            try:
                start_rgb_led()
                print("Support for RGB LED control via Raspberry Pi 3 is enabled.")
            except:
                pi3IsEnabled = False
                print("No hardware support for RGB LED control via Raspberry Pi 3.")
        else:
            pi3IsEnabled = False
            print("No hardware support for RGB LED control via Raspberry Pi 3.")

    if args.autostart:
        if (playbackIsEnabled == False):
            autostart_production(args)
        else:
            print("Playback is enabled. Autostart is not compatible with playback.")

    while 0 < 1:
        IMM1.e_setting()
        waitForProduction()
        IMM1.e_start()
        x = 1
        while x == 1:
            x = 0
            production()
            if IMM1.is_s_pause:
                waitForProduction()
                IMM1.e_proceed()
                #if pi3IsEnabled:
                #    pauseled(1)
                x = 1
            if IMM1.is_s_error:
                waitForProduction()
                IMM1.e_confirm()
                #if pi3IsEnabled:
                #    alarmled(1)
                x = 1
        IMM1.e_finished()
        IMM1.e_reset()


#def plotAllLocal(sinPlotX, sinPlotY, sinPlotY2, sinPlotY3):
#    pass  # deactivated plotting to reduce CPU load
    # plotActSimPara2(sinPlotX, sinPlotY, sinPlotY2)
    # plotActCnt(sinPlotY3)


# def plotActSimPara2(sinPlotX, sinPlotY, sinPlotY2):
#     x = np.array(sinPlotX)
#     y = np.array(sinPlotY)
#     y2 = np.array(sinPlotY2)
#
#     trace1 = go.Scatter(
#                 x=x,
#                 y=y2,
#                 mode='lines+markers',
#                 name='@ActSimPara1'
#                 )
#     trace2 = go.Scatter(
#                 x=x,
#                 y=y,
#                 mode='lines+markers',
#                 name='@ActSimPara2'
#                 )
#
#     plotly.offline.plot({
#         "data": [trace1, trace2],
#         "layout": go.Layout(title="Parameters")
#     }, filename='templates/plotActSimPara.html', auto_open=False)


#def plotActCnt(sinPlotY3):
#    x = np.array(sinPlotY3)
    # data = [go.Histogram(x=x, histnorm='probability')]
    # plotly.offline.plot(data,  filename='ActCntCyc2.html', auto_open=False)
#    plotly.offline.plot({
#        "data": [go.Histogram(x=x, histnorm='probability')],
#        "layout": go.Layout(title="ActCntCyc")
#    }, filename='templates/plotActCntCyc.html', auto_open=False)


if __name__ == "__main__":
    # Instantiate
    IMM1 = vIMM()
    main()
