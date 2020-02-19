# Default configuration of IMMS_APP

## General configuration
Local: configure IMMS via Website: http://127.0.0.1:5000
Local: default EM63 shared session folder: /home/marcel/em63/
Container: see Dockerfile for environment variables

# Application of IMMS_APP

## Get help
```sh
$~ python3 IMMS_APP.py --help
```

## Autostart
Start the application in autostart with default values for process parameters.
```sh
$~ python3 IMMS_APP.py --autostart
```

## Manual start
Start the application. Start the process.

### Manual start of IMMS_APP
```sh
$~ python3 IMMS_APP.py
```

### Manual start of the simulation
Select Setup
&rarr; Parameter &rarr; and define 2 configurable parameters
&rarr; Job &rarr; and define your job
&rarr; Machine State &rarr; and select Production
Request data using session and job files in EM63 shared session folder
When job is finished switch from machine state job completed back to idle
Select Setup &rarr; Machine State &rarr; Select Idle

# Packages
Particular packages are useful; check which is needed.
```sh
$~ apt install python3-lxml python-lxml libxml2-dev libxslt-dev python-dev
$~ apt-install smbclient
```
# Modules needed
Before installing new packages via pip
```sh
pip3 install --upgrade pip
```
Install new packages via pip
```sh
$~ pip3 install python-statemachine --user
$~ pip3 install Flask --user
$~ pip3 install opcua 
$~ pip3 install opcua-client
$~ pip3 install pysmb
$~ pip3 install netifaces
```
Numby and Plotly are not longer needed, but you can install it
```sh
$~ pip3 install numpy --user
$~ pip3 install plotly --user
```


# OPC UA Support
With `--enableOPCUA` you can enable an integrated OPC UA server.
The two environment variables  `OPCUA_HOST` and `OPCUA_PORT` can be set accordingly, if it is enabled.
Default values are `OPCUA_HOST="localhost"` and `OPCUA_PORT="4840"`.
The following Variables are created within the ``IMMS`` object on the server and get updated periodically:
```
DATE <Double>
TIME <String>
ATActSimPara1 <Double>
ATActSimPara2 <Double>
ActCntCyc <Double>
ActCntPrt <Double>
ActStsMach <String>
ActTimCyc <Double>
SetCntMld <Double>
SetCntPrt <Double>
SetTimCyc <Double>
```

Data on the OPC UA server can be easily browsed and visualized using ``opcua-client``.

# TODO

## EM63 communication
State: EM63 file exchange does not work fine.
Sometimes the process is running and IMMS_APP do not respond to REQ files. 
MDC is not able to work. After restart of IMMS_APP, it works fine again until next crash.
Issue: Maybe, the thread2 for EM63 communication was crashed. 

## EM63 log file
State: File with correct name is created.
Issue: COMMAND 1 is written to LOG file, COMMAND 2 can not be written.Log file is written before COMMAND2 is read.
Reason: RESPONSE is named in JOB file before REPORT, GETID, GETINFO.

## EM63 shared session folder
Make EM63 web configuration persistent.
Currently it is only temporary stored via web gui.

## Visualization in web GUI

### Parameter live visulization in monitoring tab
State: Live plot is not possible. html web site is static.
Issue: Refresh is used but html web sites already visited are not refreshed.
Reason: Maybe, website is already cached and cache refresh is not defined.

### Visualization of machine state
State: Current machine state is not visualized.
ToDo: Transfer machine state data from python script to web server.

## Misc
Reduce global variables and use call by reference instead of global variables.
