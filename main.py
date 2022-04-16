#!/usr/bin/python3

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import os
import asyncio
import random
import logging
import json
import time
from serial import Serial
import paho.mqtt.client as mqtt
import constant as const_var
import function

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device import constant, Message, MethodResponse
from datetime import date, timedelta, datetime

logging.basicConfig(level=logging.ERROR)

# The device "Thermostat" that is getting implemented using the above interfaces.
# This id can change according to the company the user is from
# and the name user wants to call this Plug and Play device
model_id = "dtmi:com:example:Thermostat;1"

#####################################################
# GLOBAL THERMOSTAT VARIABLES
sensor_array = []

data_payload = {
    "project_id": const_var.PROJECT_ID,
    "project_name": const_var.PROJECT_NAME,
    "station_id": str(const_var.STATION_ID + const_var.IOTHUB_DEVICE_DPS_DEVICE_ID),
    "station_name": str(const_var.STATION_NAME + const_var.IOTHUB_DEVICE_DPS_DEVICE_ID),
    "longitude": 106.660172,
    "latitude": 10.762622,
    "volt_battery": 66,
    "volt_solar": 5.3
}

#####################################################
# COMMAND HANDLERS : User will define these handlers
# depending on what commands the DTMI defines


async def reboot_handler(values):
    if values and type(values) == int:
        print("Rebooting after delay of {delay} secs".format(delay=values))
        asyncio.sleep(values)
    print("Done rebooting")


async def max_min_handler(values):
    if values:
        print(
            "Will return the max, min and average temperature from the specified time {since} to the current time".format(
                since=values
            )
        )
    print("Done generating")


# END COMMAND HANDLERS
#####################################################

#####################################################
# CREATE RESPONSES TO COMMANDS


def create_max_min_report_response(values):
    """
    An example function that can create a response to the "getMaxMinReport" command request the way the user wants it.
    Most of the times response is created by a helper function which follows a generic pattern.
    This should be only used when the user wants to give a detailed response back to the Hub.
    :param values: The values that were received as part of the request.
    """
    response_dict = {
        # "startTime": (datetime.now() - timedelta(0, moving_window_size * 8)).isoformat(),
        "endTime": datetime.now().isoformat(),
    }
    # serialize response dictionary into a JSON formatted str
    response_payload = json.dumps(response_dict, default=lambda o: o.__dict__, sort_keys=True)
    print(response_payload)
    return response_payload


def create_reboot_response(values):
    response = {"result": True, "data": "reboot succeeded"}
    return response


# END CREATE RESPONSES TO COMMANDS
#####################################################

#####################################################
# TELEMETRY TASKS


async def send_telemetry_from_thermostat(device_client, telemetry_msg):
    msg = Message(json.dumps(telemetry_msg))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
    print("Sent message")
    await device_client.send_message(msg)


# END TELEMETRY TASKS
#####################################################

#####################################################
# CREATE COMMAND AND PROPERTY LISTENERS


async def execute_command_listener(
    device_client, method_name, user_command_handler, create_user_response_handler
):
    while True:
        if method_name:
            command_name = method_name
        else:
            command_name = None

        command_request = await device_client.receive_method_request(command_name)
        print("Command request received with payload")
        print(command_request.payload)

        values = {}
        if not command_request.payload:
            print("Payload was empty.")
        else:
            values = command_request.payload

        await user_command_handler(values)

        response_status = 200
        response_payload = create_user_response_handler(values)

        command_response = MethodResponse.create_from_method_request(
            command_request, response_status, response_payload
        )

        try:
            await device_client.send_method_response(command_response)
        except Exception:
            print("responding to the {command} command failed".format(command=method_name))


async def execute_property_listener(device_client):
    ignore_keys = ["__t", "$version"]
    while True:
        patch = await device_client.receive_twin_desired_properties_patch()  # blocking call

        print("the data in the desired properties patch was: {}".format(patch))

        version = patch["$version"]
        prop_dict = {}

        for prop_name, prop_value in patch.items():
            if prop_name in ignore_keys:
                continue
            else:
                prop_dict[prop_name] = {
                    "ac": 200,
                    "ad": "Successfully executed patch",
                    "av": version,
                    "value": prop_value,
                }

        await device_client.patch_twin_reported_properties(prop_dict)


# END COMMAND AND PROPERTY LISTENERS
#####################################################

#####################################################
# An # END KEYBOARD INPUT LISTENER to quit application


def stdin_listener():
    """
    Listener for quitting the sample
    """
    while True:
        selection = "."
        if selection == "Q" or selection == "q":
            print("Quitting...")
            break


# END KEYBOARD INPUT LISTENER
#####################################################


#####################################################
# PROVISION DEVICE
async def provision_device(provisioning_host, id_scope, registration_id, symmetric_key, model_id):
    provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host=provisioning_host,
        registration_id=registration_id,
        id_scope=id_scope,
        symmetric_key=symmetric_key,
    )
    provisioning_device_client.provisioning_payload = {"modelId": model_id}
    return await provisioning_device_client.register()


#####################################################
# MAIN STARTS
async def main():
    switch = os.getenv("IOTHUB_DEVICE_SECURITY_TYPE")
    if switch == "DPS":
        provisioning_host = (
            os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
            if os.getenv("IOTHUB_DEVICE_DPS_ENDPOINT")
            else "global.azure-devices-provisioning.net"
        )
        id_scope = os.getenv("IOTHUB_DEVICE_DPS_ID_SCOPE")
        registration_id = os.getenv("IOTHUB_DEVICE_DPS_DEVICE_ID")
        symmetric_key = os.getenv("IOTHUB_DEVICE_DPS_DEVICE_KEY")

        registration_result = await provision_device(
            provisioning_host, id_scope, registration_id, symmetric_key, model_id
        )

        if registration_result.status == "assigned":
            print("Device was assigned")
            print(registration_result.registration_state.assigned_hub)
            print(registration_result.registration_state.device_id)

            device_client = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=symmetric_key,
                hostname=registration_result.registration_state.assigned_hub,
                device_id=registration_result.registration_state.device_id,
                product_info=model_id,
            )
        else:
            raise RuntimeError(
                "Could not provision device. Aborting Plug and Play device connection."
            )

    elif switch == "connectionString":
        conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
        print("Connecting using Connection String " + conn_str)
        device_client = IoTHubDeviceClient.create_from_connection_string(
            conn_str, product_info=model_id
        )
    else:
        raise RuntimeError(
            "At least one choice needs to be made for complete functioning of this sample."
        )

    # Connect the client.
    await device_client.connect()

    ################################################
    # Set and read desired property (target temperature)

    max_temp = 10.96  # Initial Max Temp otherwise will not pass certification
    await device_client.patch_twin_reported_properties({"maxTempSinceLastReboot": max_temp})

    ################################################
    # Register callback and Handle command (reboot)
    print("Listening for command requests and property updates")

    listeners = asyncio.gather(
        execute_command_listener(
            device_client,
            method_name="reboot",
            user_command_handler=reboot_handler,
            create_user_response_handler=create_reboot_response,
        ),
        execute_command_listener(
            device_client,
            method_name="getMaxMinReport",
            user_command_handler=max_min_handler,
            create_user_response_handler=create_max_min_report_response,
        ),
        execute_property_listener(device_client),
    )

    ################################################
    # Send telemetry (current temperature)

    async def send_telemetry():
        print("Sending telemetry for temperature")
        global mqttClient
        global serialCommunication
        global sensor_array

        count_timer = 0
        while True:
            # time.sleep(1)
            count_timer += 1

            if count_timer % const_var.TIME_CYCLE == 0:
                if len(sensor_array) > 0:
                    for index in range(0, len(sensor_array)):
                        sensor_array[index].value = function.read_sensor_data(serialCommunication, sensor_array[index].data)
                else:
                    print("No sensor data")

                function.publish_data_to_mqtt_server(mqttClient, update_data_payload())
                await send_telemetry_from_thermostat(device_client, update_data_sensor())
                await asyncio.sleep(8)
            
            if count_timer > const_var.REQUEST_CYCLE:
                sensor_array = function.upđate_data_from_url(sensor_array)
                count_timer = 0

            

    loop = asyncio.get_event_loop()
    send_telemetry_task = loop.create_task(send_telemetry())

    # Run the stdin listener in the event loop
    #loop = asyncio.get_running_loop()
    user_finished = loop.run_in_executor(None, stdin_listener)
    # # Wait for user to indicate they are done listening for method calls
    await user_finished

    if not listeners.done():
        listeners.set_result("DONE")

    listeners.cancel()

    send_telemetry_task.cancel()

    # Finally, shut down the client
    await device_client.shutdown()


def update_data_sensor():
    global sensor_array
    data_json = {}
    if len(sensor_array) > 0:
        for item in sensor_array:
            data_json[item.key] = item.get_value()

    return json.loads(data_json)


def update_data_payload():
    global data_payload
    global sensor_array
    data_json_array = []
    if len(sensor_array) > 0:
        for item in sensor_array:
            json_object = {}
            json_object['sensor_name'] = item.name
            json_object['sensor_unit'] = item.measure_unit
            json_object['sensor_value'] = item.get_value()
            data_json_array.append(json_object)

    data_payload["data_sensor"] = data_json_array

    return data_payload


#####################################################
# EXECUTE MAIN

if __name__ == "__main__":
    os.environ['IOTHUB_DEVICE_SECURITY_TYPE'] = const_var.IOTHUB_DEVICE_SECURITY_TYPE
    os.environ['IOTHUB_DEVICE_DPS_ID_SCOPE'] = const_var.IOTHUB_DEVICE_DPS_ID_SCOPE
    os.environ['IOTHUB_DEVICE_DPS_DEVICE_ID'] = const_var.IOTHUB_DEVICE_DPS_DEVICE_ID
    os.environ['IOTHUB_DEVICE_DPS_DEVICE_KEY'] = const_var.IOTHUB_DEVICE_DPS_DEVICE_KEY
    os.environ['IOTHUB_DEVICE_DPS_ENDPOINT'] = const_var.IOTHUB_DEVICE_DPS_ENDPOINT

    sensor_array = function.parse_sensor_data()
    sensor_array = function.upđate_data_from_url(sensor_array)

    mqttClient = mqtt.Client()
    mqttClient.username_pw_set(const_var.MQTT_USERNAME, const_var.MQTT_PASSWORD)
    mqttClient.connect(const_var.MQTT_SERVER, int(const_var.MQTT_PORT), 60)
    mqttClient.loop_start()

    serialCommunication = Serial(const_var.SERIAL_PORT, const_var.SERIAL_BAUDRATE)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
