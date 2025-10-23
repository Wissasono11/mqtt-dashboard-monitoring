import network
import utime
import ujson
from umqtt.simple import MQTTClient
import machine
import dht

class ESP32DHTMqtt:
    """ESP32 dengan sensor DHT dan MQTT publish"""

    def __init__(self, broker_host, client_id, topics_config):
        self.broker_host = broker_host
        self.client_id = client_id
        self.topics = topics_config

        self.wifi = network.WLAN(network.STA_IF)
        self.mqtt = None

        self.led_red = machine.Pin(18, machine.Pin.OUT)
        self.led_yellow = machine.Pin(19, machine.Pin.OUT)
        self.led_green = machine.Pin(20, machine.Pin.OUT)

        self.dht_sensor = dht.DHT11(machine.Pin(21))

        print(f"ESP32 DHT MQTT Sensor initialized - Client ID: {client_id}")

    def connect_wifi(self, ssid, password, timeout=15):
        """Hubungkan ke WiFi"""
        print(f"Connecting to WiFi: {ssid}...")
        self.wifi.active(True)
        self.wifi.connect(ssid, password)

        start_time = utime.time()
        while not self.wifi.isconnected():
            if utime.time() - start_time > timeout:
                print("WiFi connection timeout!")
                return False
            print(".", end="")
            utime.sleep_ms(500)

        print(f"\nConnected! IP: {self.wifi.ifconfig()[0]}")
        return True
    
    def on_message(self, topic, msg):
        message = msg.decode()
        if topic.decode() == "sensor/esp32/2/led":
            if message == "on":
                self.led_control_enabled = True
            else:
                self.led_control_enabled = False

    def connect_mqtt(self):
        """Hubungkan ke broker MQTT"""
        try:
            print(f"Connecting to MQTT broker: {self.broker_host}...")
            self.mqtt = MQTTClient(self.client_id, self.broker_host)
            print("Connected to MQTT broker!")
            self.mqtt.set_callback(self.on_message)
            self.mqtt.subscribe("sensor/esp32/2/led")
            self.mqtt.connect()
            return True
        except Exception as e:
            print(f"MQTT connection error: {e}")
            return False

    def read_dht_data(self):
        """Baca data dari sensor DHT"""
        try:
            self.dht_sensor.measure()
            temperature = self.dht_sensor.temperature()
            humidity = self.dht_sensor.humidity()

            print(f"Temperature: {temperature:.2f}°C, Humidity: {humidity:.2f}%")
            return temperature, humidity
        except Exception as e:
            print(f"Error reading DHT sensor: {e}")
            return None, None

    def update_led_status(self, temperature):
        """Atur LED sesuai rentang suhu"""
        self.led_red.off()
        self.led_yellow.off()
        self.led_green.off()

        if temperature is None:
            return

        if temperature > 30:
            self.led_red.on()
        elif 25 <= temperature <= 30:
            self.led_yellow.on()
        else:
            self.led_green.on()

    def publish_sensor_data(self):
        """Publish data sensor ke MQTT"""
        try:
            temperature, humidity = self.read_dht_data()
            if temperature is None or humidity is None:
                print("Skip publish (invalid sensor data)")
                return False

            self.update_led_status(temperature)

            payload_temp = ujson.dumps({
                "temperature": temperature,
                "timestamp": int(utime.time())
            })
            payload_hum = ujson.dumps({
                "humidity": humidity,
                "timestamp": int(utime.time())
            })

            self.mqtt.publish(self.topics["sensor_temp"], payload_temp)
            self.mqtt.publish(self.topics["sensor_humidity"], payload_hum)

            print(f"Published:\n  Temp -> {payload_temp}\n  Hum -> {payload_hum}")
            return True

        except Exception as e:
            print(f"Publish error: {e}")
            return False

    def run(self, publish_interval=5):
        """Loop utama"""
        print("Starting DHT sensor data publishing...")

        while True:
            try:
                if not self.mqtt.sock:
                    print("MQTT connection lost, reconnecting...")
                    self.connect_mqtt()

                self.publish_sensor_data()
                utime.sleep(publish_interval)

            except Exception as e:
                print(f"Error in main loop: {e}")
                utime.sleep(2)

# Setup utama
def run_esp32_dht():
    """Jalankan ESP32 dengan DHT MQTT"""
    BROKER = "test.mosquitto.org"
    CLIENT_ID = "esp-sensor-suhu-2"
    SSID = "YourSSID"
    PASSWORD = "YourPassword"
    TOPICS = {
        "sensor_temp": "sensor/esp32/2/temperature",
        "sensor_humidity": "sensor/esp32/2/humidity"
    }

    sensor = ESP32DHTMqtt(BROKER, CLIENT_ID, TOPICS)

    if not sensor.connect_wifi(SSID, PASSWORD):
        print("WiFi connection failed!")
        return

    if not sensor.connect_mqtt():
        print("MQTT connection failed!")
        return

    sensor.run(publish_interval=5)

if __name__ == "__main__":
    run_esp32_dht()
