import constant
import json

def parse_sensor_data():
    temp_array = []
    if True:
        return temp_array, constant.SATATION_TYPE_WATER
    else:
        return temp_array, constant.SATATION_TYPE_AIR_SOIL


def parse_request_url(data):
    if (len(data) > 0):
        pass
    return data


def read_sensor_data(serial, data):
    if serial.isOpen() == True:
        return write_serial_data(serial, data)
    else:
        print("ERROR: Cannot open serial port")
        return -1


def publish_data_to_mqtt_server(device_client, data):
    device_client.publish(constant.MQTT_TOPIC, json.dumps(data), 0, True)


def write_serial_data(serial, data):
    try:
        serial.write(serial.to_bytes(data))
        time.sleep(1)
        return read_serial(serial)
    except:
        print("ERROR: Failed to write data")
        return -1


def read_serial_data(serial):
    bytesToRead = serial.inWaiting()
    if (bytesToRead > 0):
        out = serial.read(bytesToRead)
        data_array = [b for b in out]
        if len(data_array) == 7:
            value = data_array[3] * 256 + data_array[4]
            return value
        else:
            return 0