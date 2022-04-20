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
    device_client.publish(str(constant.MQTT_TOPIC + constant.IOTHUB_DEVICE_DPS_DEVICE_ID), json.dumps(data), 0, True)


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
        if len(data_array) >= 7:
            array_size = len(data_array)
            value = data_array[array_size - 4] * 256 + data_array[array_size - 3]
            return value
        else:
            return 0
    return 0

###################################################################
def calCRC16(data):
    crc_table=[0x0000,0xC0C1,0xC181,0x0140,0xC301,0x03C0,0x0280,0xC241,0xC601,0x06C0,0x0780,0xC741,0x0500,0xC5C1,0xC481,0x0440,0xCC01,0x0CC0,0x0D80,0xCD41,0x0F00,0xCFC1,0xCE81,0x0E40,0x0A00,0xCAC1,0xCB81,0x0B40,0xC901,0x09C0,0x0880,0xC841,0xD801,0x18C0,0x1980,0xD941,0x1B00,0xDBC1,0xDA81,0x1A40,0x1E00,0xDEC1,0xDF81,0x1F40,0xDD01,0x1DC0,0x1C80,0xDC41,0x1400,0xD4C1,0xD581,0x1540,0xD701,0x17C0,0x1680,0xD641,0xD201,0x12C0,0x1380,0xD341,0x1100,0xD1C1,0xD081,0x1040,0xF001,0x30C0,0x3180,0xF141,0x3300,0xF3C1,0xF281,0x3240,0x3600,0xF6C1,0xF781,0x3740,0xF501,0x35C0,0x3480,0xF441,0x3C00,0xFCC1,0xFD81,0x3D40,0xFF01,0x3FC0,0x3E80,0xFE41,0xFA01,0x3AC0,0x3B80,0xFB41,0x3900,0xF9C1,0xF881,0x3840,0x2800,0xE8C1,0xE981,0x2940,0xEB01,0x2BC0,0x2A80,0xEA41,0xEE01,0x2EC0,0x2F80,0xEF41,0x2D00,0xEDC1,0xEC81,0x2C40,0xE401,0x24C0,0x2580,0xE541,0x2700,0xE7C1,0xE681,0x2640,0x2200,0xE2C1,0xE381,0x2340,0xE101,0x21C0,0x2080,0xE041,0xA001,0x60C0,0x6180,0xA141,0x6300,0xA3C1,0xA281,0x6240,0x6600,0xA6C1,0xA781,0x6740,0xA501,0x65C0,0x6480,0xA441,0x6C00,0xACC1,0xAD81,0x6D40,0xAF01,0x6FC0,0x6E80,0xAE41,0xAA01,0x6AC0,0x6B80,0xAB41,0x6900,0xA9C1,0xA881,0x6840,0x7800,0xB8C1,0xB981,0x7940,0xBB01,0x7BC0,0x7A80,0xBA41,0xBE01,0x7EC0,0x7F80,0xBF41,0x7D00,0xBDC1,0xBC81,0x7C40,0xB401,0x74C0,0x7580,0xB541,0x7700,0xB7C1,0xB681,0x7640,0x7200,0xB2C1,0xB381,0x7340,0xB101,0x71C0,0x7080,0xB041,0x5000,0x90C1,0x9181,0x5140,0x9301,0x53C0,0x5280,0x9241,0x9601,0x56C0,0x5780,0x9741,0x5500,0x95C1,0x9481,0x5440,0x9C01,0x5CC0,0x5D80,0x9D41,0x5F00,0x9FC1,0x9E81,0x5E40,0x5A00,0x9AC1,0x9B81,0x5B40,0x9901,0x59C0,0x5880,0x9841,0x8801,0x48C0,0x4980,0x8941,0x4B00,0x8BC1,0x8A81,0x4A40,0x4E00,0x8EC1,0x8F81,0x4F40,0x8D01,0x4DC0,0x4C80,0x8C41,0x4400,0x84C1,0x8581,0x4540,0x8701,0x47C0,0x4680,0x8641,0x8201,0x42C0,0x4380,0x8341,0x4100,0x81C1,0x8081,0x4040]

    crc_hi=0xFF
    crc_lo=0xFF

    for w in data:
        index = crc_lo ^ w
        crc_val = crc_table[index]
        crc_temp = crc_val >> 8
        crc_val_low = crc_val-(crc_temp << 8)
        crc_lo = crc_val_low ^ crc_hi
        crc_hi = crc_temp

    crc = []
    crc.append (crc_lo)
    crc.append (crc_hi)
    return crc


def addCRC16(data):
    crc = calCRC16(data)
    data.append(crc[0])
    data.append(crc[1])
    return data


def checkCRC16(data):
    crc1 = []
    crc1.append(data[len(data) - 2])
    crc1.append(data[len(data) - 1])
    data = data[:-2]

    crc2 = calCRC16(data)
    if (crc1[0] == crc2[0]) and (crc1[1] == crc2[1]):
        return True
    return False


def serial_read_data(ser, length):
    out = []
    time.sleep(0.5)
    #read number of bytes in buffer
    byteToRead = ser.inWaiting()
    #read array of bytes from buffer
    if byteToRead > 0:
        out = ser.read(byteToRead)
    #convert data from byte to int
    data_out = [b for b in out]
    return data_out


def read_data_sensor(ser, data):
    if ser.isOpen():
        ser.write(serial.to_bytes(data))
        time.sleep(0.5)
        result = serial_read_data(serial, 100)
        return result[len(result) - 3] * 256 + result[len(result) - 4]
    else:
        return 0



def setPump(ser, state):
    if state == True:
        relay_on = [0x0F, 0x06, 0x00, 0x00, 0x00, 0xFF]
        ser.write(addCRC16(relay_on))
        result = serial_read_data(ser, 100)
    else:
        relay_off = [0x0F, 0x06, 0x00, 0x00, 0x00, 0x00]
        ser.write(addCRC16(relay_off))
        result = serial_read_data(ser, 100)


def setFlush(ser, state):
    if state == True:
        relay_on = [0x00, 0x06, 0x00, 0x00, 0x00, 0xFF]
        ser.write(addCRC16(relay_on))
        result = serial_read_data(ser, 100)
    else:
        relay_off = [0x00, 0x06, 0x00, 0x00, 0x00, 0x00]
        ser.write(addCRC16(relay_off))
        result = serial_read_data(ser, 100)


def readPumpLevel(ser):
    adc2 = [0x01, 0x04, 0x00, 0x01, 0x00, 0x01]
    ser.write(addCRC16(adc2))
    result = serial_read_data(ser, 100)

    return result


def Flush_Water(ser):
    counter_timer = 90
    setFlush(ser, True)
    time.sleep(0.5)
    setFlush(ser, True)
    while True:
        counter_timer = counter_timer - 1
        if counter_timer % 10 == 0:
            print(counter_timer)
        if counter_timer == 0:
            break
        
        time.sleep(1)

    setFlush(ser, False)
    time.sleep(0.5)
    setFlush(ser, False)


def Pump_Water(ser):
    counter_timer = 105
    
    setPump(ser, True)
    time.sleep(0.5)
    setPump(ser, True)

    while True:
        counter_timer = counter_timer - 1
        if(counter_timer == 0):
            break
        if(readPumpLevel(ser) > 1000):
            break
        time.sleep(0.5)

    setPump(ser, False)
    time.sleep(0.5)
    setPump(ser, False)


def read_temp_raw(file_path):
    f = open(file_path, 'r')
    lines = f.readlines()
    f.close()
    return lines


def river_water_level(ser):
    data = [0x01, 0x03, 0x00, 0x02, 0x00, 0x02, 0x65, 0xCB]
    serial.write(data)
    result = serial_read_data(serial, 100)
    
    return result

def read_temp(file_path):
    lines = read_temp_raw(file_path)
    
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(file_path)

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 2)

def modify_tds(value, temperature):
    averageVoltage = value * 5.0 / 4096.0
    
    compensationCoefficient=1.0+0.02*(temperature-25.0)
    compensationVolatge=averageVoltage/compensationCoefficient
    
    tdsValue=(133.42*compensationVolatge*compensationVolatge*compensationVolatge - 255.86*compensationVolatge*compensationVolatge + 857.39*compensationVolatge)*0.5
    
    return tdsValue

def modify_turbidity(value, temperature):
    x = value * 5.0 / 4096.0
    print("Turbidity (V)", x)
    y = 3000 - (x * 781.25)
    print("Turbidity (NTU)", y)
    return y

def modify_ph(value, temperature):
    voltage = value * 5 / 4096.0
    voltage = voltage * 1000
    print("PH(mV)", voltage)
    neutralVoltage = 1500
    acidVoltage = 2032.44
    
    slope = (7.0-4.0)/((neutralVoltage-1500.0)/3.0 - (acidVoltage-1500.0)/3.0)
    intercept =  7.0 - slope*(neutralVoltage-1500.0)/3.0
    
    phValue = slope*(voltage-1500.0)/3.0+intercept
    print("PH: ", phValue)
    return phValue

def modify_oxy(value, temprature):
    return 0
 
def modify_ec(value, temprature):
    return 0