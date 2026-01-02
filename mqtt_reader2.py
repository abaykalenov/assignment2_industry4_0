import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime
import re
import matplotlib.pyplot as plt
from collections import deque
import threading
import time

MQTT_BROKER = "147.30.56.87"
MQTT_PORT = 1883
MQTT_USER = "alyabe"
MQTT_PASS = "abai0405"
MQTT_TOPIC = "sensor/data"

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "iot_data"
COLLECTION_NAME = "environment_readings"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

print("[INFO] Connected to MongoDB")

MAX_POINTS = 100
temps = deque(maxlen=MAX_POINTS)
hums = deque(maxlen=MAX_POINTS)
co2s = deque(maxlen=MAX_POINTS)
times = deque(maxlen=MAX_POINTS)

plt.ion()
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
fig.suptitle("Real-Time Sensor Data", fontsize=16)
ax1.set_ylabel("Temperature (°C)")
ax2.set_ylabel("Humidity (%)")
ax3.set_ylabel("CO₂ (ppm)")
ax3.set_xlabel("Time (last few readings)")

line1, = ax1.plot([], [], 'r-', label="Temperature")
line2, = ax2.plot([], [], 'b-', label="Humidity")
line3, = ax3.plot([], [], 'g-', label="CO₂")

for ax in [ax1, ax2, ax3]:
    ax.legend(loc="upper right")
    ax.grid(True)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"[INFO] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Message received: {payload}")

    match = re.match(r"\(([^,]+),\s*([^,]+),\s*([^)]+)\)", payload)
    if match:
        try:
            temperature = float(match.group(1))
            humidity = float(match.group(2))
            co2 = float(match.group(3))

            data = {
                "temperature": temperature,
                "humidity": humidity,
                "co2": co2,
                "timestamp": datetime.utcnow()
            }

            collection.insert_one(data)

            temps.append(temperature)
            hums.append(humidity)
            co2s.append(co2)
            times.append(datetime.now().strftime("%H:%M:%S"))

        except Exception as e:
            print(f"[ERROR] Data parse/insert failed: {e}")
    else:
        print("[WARN] Message format not recognized")

def mqtt_loop():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
mqtt_thread.start()

while True:
    if len(times) > 0:
        line1.set_data(range(len(temps)), temps)
        line2.set_data(range(len(hums)), hums)
        line3.set_data(range(len(co2s)), co2s)

        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()
        ax3.relim()
        ax3.autoscale_view()

        plt.setp(ax3, xticks=range(len(times))[::max(1, len(times)//5)], xticklabels=list(times)[::max(1, len(times)//5)])

        plt.pause(0.5)  
    else:
        time.sleep(0.5)
