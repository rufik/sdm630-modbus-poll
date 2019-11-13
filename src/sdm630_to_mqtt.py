from paho.mqtt.client import Client
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.register_read_message import ReadInputRegistersResponse
from serial.serialutil import PARITY_NONE
import logging
import traceback
from apscheduler.schedulers.background import BlockingScheduler

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger("SDM630_READER")
log.setLevel(logging.INFO)

MQTT_HOST = "192.168.66.2"
TOPIC_PREFIX = "power/sdm630/"

DEVICE = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A900UKZJ-if00-port0"
SLAVES = (1, 2)

# registers to be read (decimal format)
REGISTERS = {
    "L1_Voltage": 0,
    "L2_Voltage": 2,
    "L3_Voltage": 4,
    "L1_Current": 6,
    "L2_Current": 8,
    "L3_Current": 10,
    "L1_Power_Watt": 12,
    "L2_Power_Watt": 14,
    "L3_Power_Watt": 16,
    "L1_Power_VA": 18,
    "L2_Power_VA": 20,
    "L3_Power_VA": 22,
    "L1_Power_VAr": 24,
    "L2_Power_VAr": 26,
    "L3_Power_VAr": 28,
    "Line_to_Neutral_AVG_Volts": 42,
    "Total_Power_Watt": 52,
    "Total_Power_VA": 56,
    "Total_Power_VAr": 60,
    "Frequency": 70,
    "Import_Energy_kWh": 72,
    "Export_Energy_kWh": 74,
    "Import_Energy_kVArh": 76,
    "Export_Energy_kVArh": 78,
    "Total_System_Power_Demand_Max": 86,
    "Neutral_Current": 224,
    "L1_Current_THD": 240,
    "L2_Current_THD": 242,
    "L3_Current_THD": 244,
    "Total_Energy_kWh": 342,
    "Total_Energy_kVArh": 344,
}


def setup_serial(device) -> ModbusSerialClient:
    serial = ModbusSerialClient(method="rtu", port=device, baudrate=38400, stopbits=1)
    serial.bytesize = 8
    serial.parity = PARITY_NONE
    return serial


def read_register(serial: ModbusSerialClient, slave: int, register: int) -> float:
    result: ReadInputRegistersResponse = serial.read_input_registers(address=register, count=2, unit=slave)
    if result.isError():
        log.error("Reading of slave=%s register=%s is NOT successfull! Details: %s", slave, register, result)
        raise result
    v: float = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Big).decode_32bit_float()
    return v


def publish_mqtt(mqtt: Client, slave: int, reg_name: str, value):
    topic = TOPIC_PREFIX + str(slave) + "/" + reg_name
    mqtt.publish(topic=topic, payload=value, qos=0)


def read_meters():
    mqtt = Client(client_id="sdm630-reader")
    mqtt.connect(host=MQTT_HOST)
    log.info("Connected to MQTT host.")

    serial = setup_serial(DEVICE)

    if serial.connect():
        log.info("Connected to serial device %s", serial)
        for slave in SLAVES:
            log.info("Handling slave=%s", slave)
            for reg_name, reg in REGISTERS.items():
                try:
                    log.debug("Handling register=%s", reg_name)
                    value = read_register(serial=serial, slave=slave, register=reg)
                    log.debug("Register=%s value read=%f", reg_name, value)
                    publish_mqtt(mqtt=mqtt, slave=slave, reg_name=reg_name, value=value)
                except:
                    log.error(
                        "Error handling register %s for slave=%s!", reg_name, slave)
                    # traceback.print_exc()
            serial.close()
    else:
        log.error("Cannot connect to serial device %s !", serial)

    log.info("Done, cleaning up.")
    mqtt.disconnect()


# MAIN LOGIC
log.info("Start!")

scheduler = BlockingScheduler()
scheduler.add_job(read_meters, 'cron', hour='*', minute='*', second="0,30", max_instances=1, misfire_grace_time=1)
log.info("Scheduled readings: %s", scheduler.get_jobs()[0])
scheduler.start()

log.info("Finished!")
