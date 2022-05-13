#!/usr/bin/python3

import json
import time
from serial import Serial
import paho.mqtt.client as mqtt
import constant as const_var
import function

from datetime import date, timedelta, datetime


#####################################################
# GLOBAL THERMOSTAT VARIABLES
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
  print("Start sending telemetry")
  global sensor_array
  count_timer = 0

  while True:
    time.sleep(1)
    count_timer += 1
    
    if count_timer % const_var.TIME_CYCLE == 0:
      if len(sensor_array) > 0:
          for index in range(0, len(sensor_array)):
              if const_var.STATION_TYPE == "AIR_SOIL":
                  sensor_array[index].value = function.read_sensor_data(serial_communication, sensor_array[index].data)
      else:
        print("No sensor data")

      function.publish_data_to_mqtt_server(mqtt_client, update_data_payload())
      time.sleep(1)

      count_timer = 0
      

def update_data_payload():
  global data_payload
  global sensor_array
  data_json_array = []
  if len(sensor_array) > 0:
    for item in sensor_array:
      json_object = {'sensor_key': item.key, 'sensor_value': item.get_value()}
      data_json_array.append(json_object)

  data_payload["data_sensor"] = data_json_array

  return data_payload


#####################################################
# EXECUTE MAIN

if __name__ == "__main__":
  sensor_array = function.parse_sensor_data()

  mqttClient = mqtt.Client()
  mqttClient.username_pw_set(const_var.MQTT_USERNAME, const_var.MQTT_PASSWORD)
  mqttClient.connect(const_var.MQTT_SERVER, int(const_var.MQTT_PORT), 60)
  mqttClient.loop_start()

  serialCommunication = Serial(const_var.SERIAL_PORT, const_var.SERIAL_BAUDRATE)

  send_telemetry(mqttClient, serialCommunication)