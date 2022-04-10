# Tram Chim Monitoring

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

4. Run these command or copy line by line in terminal
```
sudo /usr/bin/python3 setup.py
```
NOTE: enter the password if required

5. Cpu Serial will print here
Example:
```
Root PATH: /home/pi/tram_chim_python
CPU Serial: 100000001bc98da9
```

6. Edit DEVICE_ID and DEVICE_ID of Azure server
```
nano constant.py
```
After changing, save it
- Press "Ctrl + X"
- Press "Y"
- Press "Enter"

7. Modify these lines
```
########## MODIFY THIS BY "USER" !!!!!!
IOTHUB_DEVICE_DPS_DEVICE_ID = ""
IOTHUB_DEVICE_DPS_DEVICE_KEY = ""
########## END MODIFY ##########
```

8. After finshing configurable, run these commands
```
sudo systemctl enable python_iot.service
sudo systemctl start python_iot.service
sudo reboot
```

