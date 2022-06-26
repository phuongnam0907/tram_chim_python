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
    json_object = data_json[find_index_from_key_value(data_json, "CPUSerial", constant.CPU_SERIAL)]
    try:
        time_pump = json_object['TimeOutPump']
    except:
        time_pump = constant.DEFAULT_TIME_PUMP
    try:
        time_flush = json_object['TimeOutFlush']
    except:
        time_flush = constant.DEFAULT_TIME_FLUSH
    object_array = json_object['SensorData']
    temp_array = []
    if len(object_array) > 0:
        for item in object_array:
            temp_array.append(Sensor(key=item['sensorMapKey'],
                                     data=item['sensorData']))

    return temp_array, time_pump, time_flush


def read_sensor_data(ser, data):
    if ser.isOpen():
        return write_serial_data(ser, data)
    else:
        print("ERROR: Cannot open serial port")
        sys.stdout.flush()
        return 0


def read_temp_raw(file_path):
    f = open(file_path, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_water_temperature(file_path):
    lines = read_temp_raw(file_path)

    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(file_path)

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 2)

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


def water_pump(ser, secs):

    dataOn = [15, 6, 0, 0, 0, 255, 200, 164]
    dataOff = [15, 6, 0, 0, 0, 0, 136, 228]

    print("Pump ON")
    sys.stdout.flush()
    read_sensor_data(ser, dataOn)

    time.sleep(secs)

    print("Pump OFF")
    sys.stdout.flush()
    read_sensor_data(ser, dataOff)

    return 0


def water_flush(ser, secs):

    dataOn = [0, 6, 0, 0, 0, 255, 200, 91]
    dataOff = [0, 6, 0, 0, 0, 0, 136, 27]

    print("Flush ON")
    sys.stdout.flush()
    read_sensor_data(ser, dataOn)

    time.sleep(secs)

    print("Flush OFF")
    sys.stdout.flush()
    read_sensor_data(ser, dataOff)

    return 0