import constant
import json
import time
import requests
import serial
import sys

#####################################################
# Class sensor
class Sensor:
    def __init__(self, key, data):
        self.data = data
        self.key = key
        self.value = 0.0

    def get_value(self):
        return round(self.value, 2)


def download_url_data():
    r = requests.get(url=constant.URL_CALIBRATION)
    return r.json()


def find_index_from_key_value(json_array, key, value):
    if len(json_array) > 0:
        index = 0
        for item in json_array:
            if item[key] == value:
                return index
            index += 1
    return -1


def parse_sensor_data():
    data_json = download_url_data()
    print("Json data", json.dumps(data_json))
    sys.stdout.flush()
    object_array = data_json[find_index_from_key_value(data_json, "CPUSerial", constant.CPU_SERIAL)]['SensorData']
    temp_array = []
    if len(object_array) > 0:
        for item in object_array:
            temp_array.append(Sensor(key=item['sensorMapKey'],
                                     data=item['sensorData']))

    return temp_array


def read_sensor_data(ser, data):
    if ser.isOpen():
        return write_serial_data(ser, data)
    else:
        print("ERROR: Cannot open serial port")
        sys.stdout.flush()
        return 0


def publish_data_to_mqtt_server(device_client, data):
    print("Publish data to MQTT Server")
    sys.stdout.flush()
    device_client.publish(str(constant.MQTT_TOPIC + constant.CPU_SERIAL), json.dumps(data), 0, True)


def write_serial_data(ser, data):
    try:
        ser.write(serial.to_bytes(data))
        time.sleep(1)
        return read_serial_data(ser)
    except:
        print("ERROR: Failed to write data")
        sys.stdout.flush()
        return 0


def read_serial_data(ser):
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        out = ser.read(bytesToRead)
        data_array = [b for b in out]
        if len(data_array) >= 7:
            array_size = len(data_array)
            value = data_array[array_size - 4] * 256 + data_array[array_size - 3]
            return value
        else:
            return 0
    return 0