import constant
import json

def parse_sensor_data(type):
    pass


def ead_sensor_data(serial, data):
    pass


def publish_data_to_mqtt_server(device_client, data):
    device_client.publish(constant.MQTT_TOPIC, json.dumps(data), 0, True)