#!/usr/bin/python3

import os
import sys
import json
import time
import glob
from serial import Serial
import paho.mqtt.client as mqtt
import constant as const_var
import function

from datetime import date, timedelta, datetime

BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_DIR = glob.glob(BASE_DIR + '28*')[0]
DEVICE_FILE = DEVICE_DIR + '/w1_slave'

#####################################################
# GLOBAL THERMOSTAT VARIABLES
water_temperature = 0
sensor_array = []

data_payload = {
  "project_id": const_var.PROJECT_ID,
  "station_id": str(const_var.STATION_ID + const_var.CPU_SERIAL),
  "longitude": 106.660172,
  "latitude": 10.762622,
  "volt_battery": 12.5,
  "volt_solar": 5.3
}

#####################################################

def send_telemetry(mqtt_client, serial_communication):
  global sensor_array
  global water_temperature

  print("Start sending telemetry - count sensor:", len(sensor_array))
  sys.stdout.flush()
  count_timer = const_var.TIME_CYCLE - 10

  while True:
    time.sleep(1)
    count_timer += 1

    if count_timer % const_var.TIME_CYCLE == 0:
      if len(sensor_array) > 0:
        print("Read sensor...")
        sys.stdout.flush()

        # Pump water in 30 second
        function.water_pump(serial_communication, 3)

        water_temperature = function.read_water_temperature(DEVICE_FILE)
        for index in range(0, len(sensor_array)):
          if const_var.STATION_TYPE == "WATER":
            sensor_array[index].value = function.read_sensor_data(serial_communication, sensor_array[index].data)

        # Flush water in 30 second
        function.water_flush(serial_communication, 3)

      else:
        print("No sensor data")
        sys.stdout.flush()

      function.publish_data_to_mqtt_server(mqtt_client, update_data_payload())
      time.sleep(1)

      count_timer = 0


def update_data_payload():
  global data_payload
  global sensor_array
  global water_temperature
  data_json_array = []
  if len(sensor_array) > 0:
    for item in sensor_array:
      json_object = {'sensor_key': item.key, 'sensor_value': item.get_value()}
      data_json_array.append(json_object)

  data_json_array.append({'sensor_key': 'temperture', 'sensor_value': water_temperature})

  data_payload["data_sensor"] = data_json_array

  return data_payload


#####################################################
# EXECUTE MAIN

if __name__ == "__main__":
  os.system('modprobe w1-gpio')
  os.system('modprobe w1-therm')

  sensor_array = function.parse_sensor_data()

  mqttClient = mqtt.Client()
  mqttClient.username_pw_set(const_var.MQTT_USERNAME, const_var.MQTT_PASSWORD)
  mqttClient.connect(const_var.MQTT_SERVER, int(const_var.MQTT_PORT), 60)
  mqttClient.loop_start()

  serialCommunication = Serial(const_var.SERIAL_PORT, const_var.SERIAL_BAUDRATE)

  send_telemetry(mqttClient, serialCommunication)