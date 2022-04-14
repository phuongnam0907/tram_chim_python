#!/usr/bin/python3

import os
import requests

def download_url_data():
    URL = "https://ubc.sgp1.cdn.digitaloceanspaces.com/TramChimPark/Config/config.json"
    r = requests.get(url=URL)
    return r.json()

def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"
    print("CPU Serial:", cpuserial)

    return cpuserial

current_path = os.environ["ROOT_PATH"]
cpu_serial = getserial()
data_json = download_url_data()
station_type = ""
device_id = ""
device_key = ""

if len(data_json) > 0:
    for item in data_json:
        if item['CPUSerial'] == cpu_serial:
            station_type = item['StationType']
            device_id = item['AzureID']
            device_key = item['AzureToken']

print("Type:", station_type)
print("Device ID:", device_id)

#input file
fin = open(current_path + "/template/constant.template", "r")
#output file to write the result to
fout = open(current_path + "/constant.py", "w")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
    line_data = line
    
    if line.find("cpu_serial_replace") > -1:
        line_data = line.replace('cpu_serial_replace', cpu_serial)
    if line.find("root_path_replace") > -1:
        line_data = line.replace('root_path_replace', current_path)
    if line.find("station_type_replace") > -1:
        line_data = line.replace('station_type_replace', station_type)
    if line.find("device_id_replace") > -1:
        line_data = line.replace('device_id_replace', device_id)
    if line.find("device_key_replace") > -1:
        line_data = line.replace('device_key_replace', device_key)
        
    fout.write(line_data)
    
#close input and output files
fin.close()
fout.close()

###########################################################################
# Create service auto run
if os.path.exists("/etc/systemd/system/python_iot.service"):
    os.remove("/etc/systemd/system/python_iot.service")
else:
    print("The file does not exist")

#input file
fin = open(current_path + "/template/python_iot.service.template", "r")
#output file to write the result to
fout = open("/etc/systemd/system/python_iot.service", "w")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
    line_data = line
    if line.find("root_path_replace") > -1:
        line_data = line.replace('root_path_replace', current_path)
        
    fout.write(line_data)
    
#close input and output files
fin.close()
fout.close()
