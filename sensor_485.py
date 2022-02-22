#!/usr/bin/python

# DEFINITION

import RPi.GPIO as GPIO
import serial
import time
import json
import os

""" 
PUBLIC VARIABLES

# List the variables that are commonly used in the program
"""

MQTT_HOST = ""
MQTT_PORT = ""
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_TOPIC = ""
SERIAL_PORT_NBIOT = ""
BAUD_RATE_NBIOT = 9600
SERIAL_PORT_SENSOR = ""
BAUD_RATE_SENSOR = 9600
LIST_SENSORS = []
SENSING_PERIOD = 600 # 10 minutes default

# Hardcode variables
rec_buff = ''
POWER_KEY = 4
data_payload = {
    "project_id": "",
    "project_name": "",
    "station_id": "",
    "station_name": "",
    "longitude": 106.660172,
    "latitude": 10.762622,
    "volt_battery": 12.2,
    "volt_solar": 5.3,
    "data_ss": {}
}


""" 
SUB-FUNCTIONS

# List the functions that are commonly used in the program
"""


def init_config_file():
    # get sensor config from json file
    global LIST_SENSORS
    f = open("/home/pi/tram_chim_python/.config/sensor.json")
    LIST_SENSORS = json.load(f)
    f.close()

    # Open file .config/config.json
    f = open("/home/pi/tram_chim_python/.config/config.json")
    temp_json = json.load(f)

    # get mqtt config from json file
    global MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC
    MQTT_HOST = temp_json['config_mqtt']['MQTT_HOST']
    MQTT_PORT = temp_json['config_mqtt']['MQTT_PORT']
    MQTT_USERNAME = temp_json['config_mqtt']['MQTT_USERNAME']
    MQTT_PASSWORD = temp_json['config_mqtt']['MQTT_PASSWORD']
    MQTT_TOPIC = temp_json['config_mqtt']['MQTT_TOPIC']

    # get serial config from json file
    global SERIAL_PORT_NBIOT, SERIAL_PORT_SENSOR, BAUD_RATE_NBIOT, BAUD_RATE_SENSOR
    SERIAL_PORT_NBIOT = temp_json['config_serial']['SERIAL_PORT_NBIOT']
    SERIAL_PORT_SENSOR = temp_json['config_serial']['SERIAL_PORT_SENSOR']
    BAUD_RATE_NBIOT = temp_json['config_serial']['BAUD_RATE_NBIOT']
    BAUD_RATE_SENSOR = temp_json['config_serial']['BAUD_RATE_SENSOR']

    # get program config from json file
    SENSING_PERIOD = temp_json['config_payload']['sensing_period']

    # get project status from json file
    global data_payload
    data_payload['project_id'] = temp_json['config_payload']['project_id']
    data_payload['project_name'] = temp_json['config_payload']['project_name']
    data_payload['station_id'] = temp_json['config_payload']['station_id']
    data_payload['station_name'] = temp_json['config_payload']['station_name']

    # Close file .config/config.json
    f.close()


def parse_name_sensor():
    global data_payload
    temp_object = []
    for item in LIST_SENSORS:
        temp_object.append({"ss_name":item['sensor_name'], "ss_unit": item['sensor_unit'], "ss_value": -1.0})
    data_payload['data_ss'] = temp_object
    # print(data_payload)


def current_milli_time():
    return round(time.time() * 1000)


def read_serial():
    bytesToRead = serial_sensor.inWaiting()
    if (bytesToRead > 0):
        out = serial_sensor.read(bytesToRead)
        # print(out)
        data_array = [b for b in out]
        if len(data_array) == 7:
            value = data_array[3] * 256 + data_array[4]
            # print("value: " + str(value))
            return value
        else:
            return 0


# def getGpsPosition():
#     rec_null = True
#     answer = 0
#     print('Start GPS session...')
#     rec_buff = ''
#     time.sleep(5)
#     sendAt('AT+CGNSPWR=1', 'OK', 0.1)
#     while rec_null:
#         answer = sendAt('AT+CGNSINF', '+CGNSINF: ', 1)
#         if 1 == answer:
#             answer = 0
#             if ',,,,,,' in rec_buff:
#                 print('GPS is not ready')
#                 rec_null = False
#                 time.sleep(1)
#         else:
#             print('error %d' % answer)
#             rec_buff = ''
#             sendAt('AT+CGNSPWR=0', 'OK', 1)
#             return False
#         time.sleep(1.5)


def get_index_list_sensor(sensor_name):
    for i in range(len(LIST_SENSORS)):
        if LIST_SENSORS[i]['sensor_name'] == sensor_name:
            return i


def get_sensors_value():
    for item in data_payload['data_ss']:
        try:
            ss_object = LIST_SENSORS[get_index_list_sensor(item['ss_name'])]
            ss_factor = ss_object['sensor_factor']
            ss_byte = ss_object['sensor_byte']
            serial_sensor.write(serial.to_bytes(ss_byte))
            time.sleep(1)
            item['ss_value'] = round(read_serial() * ss_factor, 0 if isinstance(ss_factor, int) else 1 )
        except:
            # print("get_sensors_value: get FAILED")
            pass

def powerOn(powerKey):
    print("SIM7070X is starting:")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(powerKey, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(powerKey, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(powerKey, GPIO.LOW)
    time.sleep(5)
    serial_nbiot.flushInput()
    print("SIM7070X is ready")


def powerDown(powerKey):
    print('SIM7070X is loging off:')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(powerKey, GPIO.OUT)
    GPIO.output(powerKey, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(powerKey, GPIO.LOW)
    time.sleep(5)
    print('Good bye')


def sendAt(command, back, timeout):
    rec_buff = ""
    serial_nbiot.write((command + '\r\n').encode())
    time.sleep(timeout)
    if serial_nbiot.inWaiting():
        time.sleep(0.1)
        rec_buff = serial_nbiot.read(serial_nbiot.inWaiting())
    if rec_buff != "":
        if back not in rec_buff.decode():
            print(command + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(command + ' no responce')


def checkStart():
    while True:
        # simcom module uart may be fool,so it is better to send much times when it starts.
        serial_nbiot.write('AT\r\n'.encode())
        time.sleep(1)
        serial_nbiot.write('AT\r\n'.encode())
        time.sleep(1)
        serial_nbiot.write('AT\r\n'.encode())
        time.sleep(1)
        if serial_nbiot.inWaiting():
            time.sleep(0.01)
            recBuff = serial_nbiot.read(serial_nbiot.inWaiting())
            print('SOM7080X is ready\r\n')
            print('try to start\r\n' + recBuff.decode())
            if 'OK' in recBuff.decode():
                recBuff = ''
                break
        else:
            powerOn(POWER_KEY)


def send_data():
    try:
        powerDown(POWER_KEY)
        checkStart()
        print('wait for signal')
        time.sleep(10)
        sendAt('AT+CSQ', 'OK', 1)
        sendAt('AT+CNMP=38', 'OK', 1)
        sendAt('AT+CGREG?', '+CGREG: 0,1', 0.5)
        sendAt('AT+CNACT=0,1', 'OK', 1)
        sendAt('AT+CACID=0', 'OK', 1)
        sendAt('AT+CNACT?', 'OK',1)
        sendAt('AT+CNMP?', 'OK',1)
        # getGpsPosition()
        sendAt('AT+SMCONF=\"CLIENTID\",id_' + str(current_milli_time()), 'OK', 0.25)
        sendAt('AT+SMCONF=\"USERNAME\",' + MQTT_USERNAME, 'OK', 0.25)
        sendAt('AT+SMCONF=\"PASSWORD\",' + MQTT_PASSWORD, 'OK', 0.25)
        sendAt('AT+SMCONF=\"URL\",' + MQTT_HOST + ',' + MQTT_PORT, 'OK', 0.25)
        sendAt('AT+SMCONF=\"KEEPTIME\",60', 'OK', 0.25)
        sendAt('AT+SMCONN', 'OK', 3)
        sendAt('AT+SMPUB=\"' + MQTT_TOPIC + str(data_payload['station_id']) + '\",' + str(len(json.dumps(data_payload))) + ',0,1', 'OK', 2)
        serial_nbiot.write(json.dumps(data_payload).encode())
        time.sleep(10)
        print('send message successfully!')
        sendAt('AT+SMDISC', 'OK', 1)
        sendAt('AT+CNACT=0,0', 'OK', 1)
        powerDown(POWER_KEY)
    except:
        print('send_data: Exception')
        powerDown(POWER_KEY)
        GPIO.cleanup()


if __name__ == '__main__':
    print("************* GEMHO Sensor 485 *************")

    init_config_file()
    parse_name_sensor()

    try:
        serial_nbiot = serial.Serial(port=SERIAL_PORT_NBIOT, baudrate=BAUD_RATE_NBIOT)
        serial_nbiot.flushInput()
        serial_sensor = serial.Serial(port=SERIAL_PORT_SENSOR, baudrate=BAUD_RATE_SENSOR)
    except:
        print("Cannot open Serial Port")
        pass
    count = 0
    time.sleep(150)
    while True:
        get_sensors_value()
        data_payload['project_id'] = count
        count += 1
        # print(data_payload)
        send_data()
        time.sleep(270)
