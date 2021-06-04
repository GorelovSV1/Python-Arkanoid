import paho.mqtt.client as mqtt
import time
from influxdb import InfluxDBClient
from queue import Queue

INFLUXDB_ADDRESS = '127.0.0.1'
INFLUXDB_USER = 'telegraf'
INFLUXDB_PASSWORD = 'telegraf'
INFLUXDB_DATABASE = 'coords'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, database=INFLUXDB_DATABASE)


def send_coords_ball_data_to_influxdb(x: int, y: int) -> None:

    #создает JSON для отправки в DB
    json_body = [
        {
            "measurement": "arkanoid",
            "tags": {
                "host": "game",
            },
            "fields": {
                "ball_x": int(x),
                "ball_y": int(y)
            }
        }
    ]
    influxdb_client.write_points(json_body)
    return None


def send_coords_paddle_data_to_influxdb(x: int) -> None:

    #создает JSON для отправки в DB
    json_body = [
        {
            "measurement": "arkanoid_paddle",
            "tags": {
                "host": "game",
            },
            "fields": {
                "paddle_x": int(x)
            }
        }
    ]
    influxdb_client.write_points(json_body)
    return None



def init_influxdb_database() -> None:
    """
    создает базу данных, если ее не существует
    """
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)
    return None


def on_message(client, userdata, message):
    data = str(message.payload.decode("utf-8"))
    if message.topic == 'coords/paddle':
        print("message received paddle x", str(message.payload.decode("utf-8")))
        print("message topic=", message.topic)
        q1.put(data)
    elif message.topic == 'coords/ball':
        print("message received ball coords", str(message.payload.decode("utf-8")))
        print("message topic=", message.topic)
        q2.put(data)



q1 = Queue()
q2 = Queue()
time.sleep(25)
init_influxdb_database()
client_2 = mqtt.Client("Sergey")
client_2.on_message = on_message
client_2.connect("127.0.0.1", 1883, 60)  # подключение к брокеру
client_2.loop_start()
print('Подключен')
client_2.subscribe('coords/paddle')
client_2.subscribe('coords/ball')
while True:

    client_2.on_message = on_message
    while not q1.empty():
        message = q1.get()
        send_coords_paddle_data_to_influxdb(message)
        if message is None:
            continue
        print("received from queue", message)
    while not q2.empty():
        message = q2.get()
        message = message.split(',')
        x = int(message[0])
        y = int(message[1])
        send_coords_ball_data_to_influxdb(x, y)
        if message is None:
            continue
        print("received from queue", message)
    time.sleep(4)  # wait