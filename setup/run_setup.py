#!/usr/bin/python3

import os
import subprocess

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

#input file
fin = open(current_path + "/template/constant.template", "r")
#output file to write the result to
fout = open(current_path + "/constant.py", "w")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
    line_data = line
    
    if line.find("cpu_serial_replace") > -1:
        line_data = line.replace('cpu_serial_replace', getserial())
    if line.find("root_path_replace") > -1:
        line_data = line.replace('root_path_replace', current_path)
        
    fout.write(line_data)
    
#close input and output files
fin.close()
fout.close()

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
