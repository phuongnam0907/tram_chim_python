#!/usr/bin/python

# DEFINITION

import RPi.GPIO as GPIO
import serial
import time
import json

TOPIC = "/tram_chim_monitoring/dong_thap/"

gemho_001_temp_soil     = [0x02, 0x03,0x00, 0x00, 0x00, 0x01, 0x84, 0x39]
gemho_001_hum_soil      = [0x02, 0x03,0x00, 0x01, 0x00, 0x01, 0xD5, 0xF9]
gemho_001_ec            = [0x02, 0x03,0x00, 0x04, 0x00, 0x01, 0xC5, 0xF8]

gemho_002_temperature   = [0x02, 0x03,0x00, 0x00, 0x00, 0x01, 0x84, 0x39]
gemho_002_humidity      = [0x02, 0x03,0x00, 0x01, 0x00, 0x01, 0xD5, 0xF9]
gemho_002_co2           = [0x02, 0x03,0x00, 0x04, 0x00, 0x01, 0xC5, 0xF8]

gemho_003_temperature   = [0x03, 0x03, 0x00, 0x00, 0x00, 0x01, 0x85, 0xE8]
gemho_003_humidity      = [0x03, 0x03, 0x00, 0x01, 0x00, 0x01, 0xD4, 0x28]

gemho_004_pm25          = [0x02, 0x03,0x00, 0x00, 0x00, 0x01, 0x84, 0x39]
gemho_004_pm10          = [0x02, 0x03,0x00, 0x01, 0x00, 0x01, 0xD5, 0xF9]

SERIAL_PORT_NBIOT = "/dev/ttyS0"
SERIAL_PORT_SENSOR = "/dev/ttyUSB0"
POWER_KEY = 4

rec_buff = ''
data_payload = {
  "project_id": "projectid123456",
  "project_name": "projectnameABC",
  "station_id": "stationid123456",
  "station_name": "stationnamABC",
  "longitude": 106.660172,
  "latitude": 10.762622,
  "volt_battery": 12.2,
  "volt_solar": 5.3,
  "gemho_001_temp_soil": 30.1,
  "gemho_001_hum_soil": 25.1,
  "gemho_001_ec": 20,
  "gemho_002_temperature": 30.2,
  "gemho_002_humidity": 25.2,
  "gemho_002_co2": 21,
  "gemho_003_temperature": 30.3,
  "gemho_003_humidity": 25.3,
  "gemho_004_pm25": 22,
  "gemho_004_pm10": 23
}

# FUNCTION

def readSerial():
    bytesToRead = serial_sensor.inWaiting()
    if (bytesToRead > 0):
        out = serial_sensor.read(bytesToRead)
        print("Received:", out)
        data_array = [b for b in out]
        #print(len(data_array))
        #print(data_array)
        if len(data_array) == 7:
            value = data_array[3]*256 + data_array[4]
            print("Decode value is:",  value)


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
    serial_nbiot.write((command+'\r\n').encode())
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
        serial_nbiot.write( 'AT\r\n'.encode() )
        time.sleep(1)
        serial_nbiot.write( 'AT\r\n'.encode() )
        serial_nbiot.sleep(1)
        serial_nbiot.write( 'AT\r\n'.encode() )
        time.sleep(1)
        if serial_nbiot.inWaiting():
            time.sleep(0.01)
            recBuff = serial_nbiot.read(serial_nbiot.inWaiting())
            print('SOM7080X is ready\r\n')
            print( 'try to start\r\n' + recBuff.decode() )
            if 'OK' in recBuff.decode():
                recBuff = ''
                break
        else:
            powerOn(POWER_KEY)


def sendData():
    try:
        checkStart()
        print('wait for signal')
        time.sleep(5)
        # sendAt('AT+SMCONF?', 'OK', 5)
        sendAt('AT+CSQ', 'OK', 1)
        sendAt('AT+CPSI?', 'OK', 1)
        sendAt('AT+CNMP=38', 'OK', 5)
        sendAt('AT+CGREG?', '+CGREG: 0,1', 0.5)
        sendAt('AT+CNACT=0,1', 'OK', 1)
        sendAt('AT+CACID=0', 'OK', 1)
        sendAt('AT+CNACT?', 'OK', 1)
        sendAt('AT+SMCONF=\"CLIENTID\",id123331', 'OK', 1)
        sendAt('AT+SMCONF=\"USERNAME\",mqttbroker', 'OK', 5)
        sendAt('AT+SMCONF=\"PASSWORD\",Mqtt!@#456', 'OK', 5)
        sendAt('AT+SMCONF=\"URL\",mqttserver.tk,1883', 'OK', 1)
        sendAt('AT+SMCONF=\"KEEPTIME\",60', 'OK', 1)
        sendAt('AT+SMCONF?', 'OK', 5)
        sendAt('AT+SMCONN', 'OK', 5)
        sendAt('AT+SMSUB=\"waveshare_pub\",1', 'OK', 1)
        sendAt('AT+SMPUB=\"waveshare_sub\",17,1,0', 'OK', 1)
        serial_nbiot.write(json.dumps(data_payload).encode())
        time.sleep(10);
        print('send message successfully!')
        sendAt('AT+SMDISC', 'OK', 1)
        sendAt('AT+CNACT=0,0', 'OK', 1)
        powerDown(POWER_KEY)
    except:
        if serial_nbiot != None:
            serial_nbiot.close()
        powerDown(POWER_KEY)
        GPIO.cleanup()


if __name__ == '__main__':
    print("************* GEMHO Sensor 485 *************")

    serial_nbiot = serial.Serial(port=SERIAL_PORT_NBIOT, baudrate=9600)
    serial_nbiot.flushInput()
    serial_sensor = serial.Serial(port=SERIAL_PORT_SENSOR, baudrate=9600)

    while True:
        serial_sensor.write(serial.to_bytes(gemho_002_temperature))
        time.sleep(1)
        readSerial()

        serial_sensor.write(serial.to_bytes(gemho_002_humidity))
        time.sleep(1)
        readSerial()

        serial_sensor.write(serial.to_bytes(gemho_002_co2))
        time.sleep(1)
        readSerial()

        sendData()
        time.sleep(5)

    # import paho.mqtt.client as mqtt
    #
    # client = mqtt.Client()
    # client.username_pw_set("mqttbroker", "Mqtt!@#456")
    # client.connect("mqttserver.tk", 1883)  # connect to broker
    # client.loop_start()  # start the loop
    #
    # client.publish(TOPIC, json.dumps(data_payload))
    #
    # client.loop_stop()
