# Tram Chim Monitoring

## Setup WATER station
Follow this [link](https://pinout.xyz/pinout/1_wire) to open One-Wire driver

## How to setup
1. SSH to Pi device
- Example IP device: 192.168.0.100
- Default username: <b>pi</b>
- Default password: <b>raspberry</b>
- Example command:
```
ssh pi@192.168.0.100
```
- Then enter password
2. Copy all source to Pi device
3. Go to location of source on Pi device
Example command:
```
cd /home/pi/tram_chim_python
```

4. First of all, get CPU serial by running this script
```
sudo python3 get_cpu.py
```
NOTE: enter the password if required

Output example:
```
CPU Serial: 100000001bc98da9
```
Then copy the CPU serial to the JSON config file.

<b>NOTE:</b> Type of CPU serial is <b>STRING</b>

5. After the CPU serials are modifed, upload to server. Then run the next script to install
```
sudo /usr/bin/python3 setup.py
```
When install success, it will print the result like this

Example:
```
Root PATH: /home/pi/tram_chim_python
CPU Serial: 100000001bc98da9
Type: AIR_SOIL
Dervice ID: solar-air-001
```

6. After finshing configurable, run these commands
```
sudo systemctl enable python_iot.service
sudo systemctl start python_iot.service
sudo reboot
```

