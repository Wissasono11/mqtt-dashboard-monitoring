# esp32_sensor.py - Publish sensor data via MQTT
import network
import utime
import ujson
from umqtt.simple import MQTTClient
import machine
import random

class ESP32MqttSensor:
    """ESP32 Sensor dengan MQTT publish"""

    def __init__(self, broker_host, client_id, topics_config):
        """Inisialisasi sensor dan MQTT"""
        self.broker_host = broker_host
        self.client_id = client_id
        self.topics = topics_config

        # Setup WiFi
        self.wifi = network.WLAN(network.STA_IF)
        self.mqtt = None

        # Setup LED untuk status
        self.status_led = machine.Pin(2, machine.Pin.OUT)
        self.status_led.off()

        print(f"ESP32 MQTT Sensor initialized - Client ID: {client_id}")

    def connect_wifi(self, ssid, password, timeout=10):
        """Hubungkan ke WiFi"""
        print(f"Connecting to WiFi: {ssid}...")

        self.wifi.active(True)
        self.wifi.connect(ssid, password)

        start_time = utime.time()
        while not self.wifi.isconnected():
            if utime.time() - start_time > timeout:
                print("WiFi connection timeout!")
                return False

            self.status_led.on()
            utime.sleep_ms(500)
            self.status_led.off()
            utime.sleep_ms(500)
            print(".", end="")

        self.status_led.on()
        print(f"\nConnected to WiFi!")
        print(f"IP: {self.wifi.ifconfig()[0]}")
        return True

    def connect_mqtt(self):
        """Hubungkan ke MQTT broker"""
        try:
            print(f"Connecting to MQTT broker: {self.broker_host}...")

            self.mqtt = MQTTClient(self.client_id, self.broker_host)
            self.mqtt.connect()

            print("Connected to MQTT broker!")
            return True

        except Exception as e:
            print(f"MQTT connection error: {e}")
            return False

    def read_sensor_data(self):
        """Baca data sensor (simulator)"""
        # Ini adalah simulator - ganti dengan sensor real
        data = {
            'temperature': 20 + random.randint(0, 15) / 10,
            'humidity': 40 + random.randint(0, 40),
            'pressure': 1000 + random.randint(-50, 50) / 10,
            'timestamp': int(utime.time())
        }
        return data

    def publish_sensor_data(self):
        """Publish sensor data ke MQTT"""
        try:
            data = self.read_sensor_data()
            payload = ujson.dumps(data)

            # Publish temperature
            self.mqtt.publish(
                self.topics['sensor_temp'],
                payload
            )

            print(f"Published: {payload}")
            return True

        except Exception as e:
            print(f"Publish error: {e}")
            return False

    def run(self, publish_interval=5):
        """Main loop - publish data secara berkala"""
        print("Starting sensor data publishing...")

        while True:
            try:
                if not self.mqtt.sock:
                    print("MQTT connection lost, reconnecting...")
                    self.connect_mqtt()

                self.publish_sensor_data()

                # LED blink sebagai indicator
                self.status_led.off()
                utime.sleep(publish_interval - 1)
                self.status_led.on()
                utime.sleep(1)

            except Exception as e:
                print(f"Error in main loop: {e}")
                utime.sleep(1)

# Setup untuk ESP32
def run_esp32_mqtt():
    """Jalankan MQTT sensor di ESP32"""
    # Konfigurasi
    BROKER = "test.mosquitto.org"  # IP address PC/laptop Anda
    CLIENT_ID = "esp32-sensor-02"
    SSID = "YourSSID"
    PASSWORD = "YourPassword"
    TOPICS = {
        'sensor_temp': 'sensor/esp32/temperature02',
        'sensor_humidity': 'sensor/esp32/humidity02',
        'sensor_pressure': 'sensor/esp32/pressure02'
    }

    # Inisialisasi
    sensor = ESP32MqttSensor(BROKER, CLIENT_ID, TOPICS)

    # Connect ke WiFi
    if not sensor.connect_wifi(SSID, PASSWORD):
        print("Failed to connect WiFi!")
        return

    # Connect ke MQTT
    if not sensor.connect_mqtt():
        print("Failed to connect MQTT!")
        return

    # Run main loop
    sensor.run(publish_interval=5)

# Upload dan jalankan di ESP32
if __name__ == "__main__":
    run_esp32_mqtt()