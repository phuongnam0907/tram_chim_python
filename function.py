import constant
import json
import time
import requests
import serial


#####################################################
# Class sensor
class Sensor:
    def __init__(self, name, key, data, measure_unit, calibrate_factor=None):
        self.name = name
        self.data = data
        self.key = key
        self.measure_unit = measure_unit
        self.value = 0.0
        if calibrate_factor is not None:
            self.calibrate_factor = calibrate_factor
        else:
            self.calibrate_factor = 1

    def get_value(self):
        return round(self.value * self.calibrate_factor, 2)


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
    object_array = data_json[find_index_from_key_value(data_json, "CPUSerial", constant.CPU_SERIAL)]['SensorData']
    temp_array = []
    if len(object_array) > 0:
        for item in object_array:
            temp_array.append(Sensor(name=item['sensorName'],
                                     key=item['sensorMapKey'],
                                     data=item['sensorData'],
                                     measure_unit=item['sensorUnit'],
                                     calibrate_factor=item['sensorCalib']))

    return temp_array


def update_data_from_url(data):
    data_json = download_url_data()
    object_array = data_json[find_index_from_key_value(data_json, "CPUSerial", constant.CPU_SERIAL)]['SensorData']
    if 0 < len(data) == len(object_array) and len(object_array) > 0:
        for item in data:
            item.calibrate_factor = object_array[find_index_from_key_value(object_array, "sensorMapKey", item.key)]['sensorCalib']
    return data


def read_sensor_data(ser, data):
    if ser.isOpen():
        return write_serial_data(ser, data)
    else:
        print("ERROR: Cannot open serial port")
        return 0


def publish_data_to_mqtt_server(device_client, data):
    print("Publish data to MQTT Server")
    device_client.publish(constant.MQTT_TOPIC, json.dumps(data), 0, True)


def write_serial_data(ser, data):
    try:
        ser.write(serial.to_bytes(data))
        time.sleep(1)
        return read_serial_data(ser)
    except:
        print("ERROR: Failed to write data")
        return 0


def read_serial_data(ser):
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        out = ser.read(bytesToRead)
        data_array = [b for b in out]
        if len(data_array) == 7:
            value = data_array[3] * 256 + data_array[4]
            return value
        else:
            return 0
    return 0
