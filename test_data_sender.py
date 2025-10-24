import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

class DHT11Simulator:
    """Simulator untuk ESP32 DHT11 MQTT Publisher"""
    
    def __init__(self, broker_host, client_id):
        self.broker_host = broker_host
        self.client_id = client_id
        
        # MQTT Topics
        self.topic_temp = "sensor/esp32/2/temperature"
        self.topic_hum = "sensor/esp32/2/humidity"
        self.topic_led = "sensor/esp32/2/led"

        self.led_control_enabled = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker: {self.broker_host}")
            self.connected = True
            client.subscribe(self.topic_led)
            print(f"Subscribed to: {self.topic_led}")
        else:
            print(f"Connection failed with code {rc}")
            self.connected = False
    
    def on_message(self, client, userdata, msg):
        try:
            message = msg.payload.decode()
            if msg.topic == self.topic_led:
                if message == "on":
                    self.led_control_enabled = True
                    print("LED Control: ENABLED")
                else:
                    self.led_control_enabled = False
                    print("LED Control: DISABLED")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def connect(self):
        try:
            print(f"Connecting to {self.broker_host}...")
            self.client.connect(self.broker_host, 1883, 60)
            self.client.loop_start()

            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            if not self.connected:
                print("Connection timeout!")
                return False
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def generate_random_temp(self):
        base_temp = random.uniform(22, 33)
        noise = random.uniform(-0.5, 0.5)
        temp = round(base_temp + noise, 1)
        return temp
    
    def generate_random_humidity(self):
        base_hum = random.uniform(50, 85)
        noise = random.uniform(-2, 2)
        hum = round(base_hum + noise, 1)
        return hum
    
    def get_led_status(self, temperature):
        if temperature > 30:
            return "RED (Suhu Tinggi)"
        elif 25 <= temperature <= 30:
            return "YELLOW (Suhu Normal)"
        else:
            return "GREEN (Suhu Rendah)"
    
    def publish_sensor_data(self):
        try:
            temperature = self.generate_random_temp()
            humidity = self.generate_random_humidity()
            timestamp = int(time.time())
            
            # payload JSON
            payload_temp = json.dumps({
                "temperature": temperature,
                "timestamp": timestamp
            })
            
            payload_hum = json.dumps({
                "humidity": humidity,
                "timestamp": timestamp
            })
            
            # Publish ke MQTT
            self.client.publish(self.topic_temp, payload_temp)
            self.client.publish(self.topic_hum, payload_hum)

            #Status
            led_status = self.get_led_status(temperature) if self.led_control_enabled else "OFF (LED Disabled)"
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] Data Published:")
            print(f"   - Temperature: {temperature}C")
            print(f"   - Humidity: {humidity}%")
            print(f"   - LED Status: {led_status}")
            print(f"   - Timestamp: {timestamp}")
            
            return True
            
        except Exception as e:
            print(f"Publish error: {e}")
            return False
    
    def run(self, interval=2):
        """Loop utama - publish setiap interval detik"""
        print("\n" + "="*60)
        print("DHT11 MQTT Simulator Started")
        print("="*60)
        print(f"Broker: {self.broker_host}")
        print(f"Client ID: {self.client_id}")
        print(f"Publish Interval: {interval} seconds")
        print(f"Topics:")
        print(f"   - Temperature: {self.topic_temp}")
        print(f"   - Humidity: {self.topic_hum}")
        print(f"Listening:")
        print(f"   - LED Control: {self.topic_led}")
        print("="*60)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                if self.connected:
                    self.publish_sensor_data()
                else:
                    print("Not connected to broker, trying to reconnect...")
                    self.connect()
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nSimulator stopped by user")
            self.client.loop_stop()
            self.client.disconnect()
            print("Disconnected from MQTT Broker")
            print("Goodbye!\n")

def main():
    """Main function"""
    BROKER = "test.mosquitto.org"
    CLIENT_ID = "esp-simulator-dht11-001"
    INTERVAL = 2  # detik
    
    # Buat instance simulator
    simulator = DHT11Simulator(BROKER, CLIENT_ID)
    
    if simulator.connect():
        simulator.run(interval=INTERVAL)
    else:
        print("Failed to connect to MQTT Broker")
        print("Tips:")
        print("   - Pastikan koneksi internet aktif")
        print("   - Cek apakah broker tersedia?")

# by: Arbath
if __name__ == "__main__":
    main()