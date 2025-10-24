import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

class MQTTDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 DHT11 Monitoring Dashboard")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e2e')
        
        # MQTT Configuration
        self.broker = "test.mosquitto.org"
        self.client_id = "dashboard-monitor-001"
        self.topic_temp = "sensor/esp32/2/temperature"
        self.topic_hum = "sensor/esp32/2/humidity"
        self.topic_led = "sensor/esp32/2/led"
        
        # Data storage (maksimal 50 data points)
        self.max_data_points = 50
        self.temp_data = deque(maxlen=self.max_data_points)
        self.hum_data = deque(maxlen=self.max_data_points)
        self.time_data = deque(maxlen=self.max_data_points)
        
        # LED Status
        self.led_enabled = False
        
        # MQTT Client
        self.mqtt_client = None
        self.connected = False
        
        # Setup UI
        self.setup_ui()
        
        # Connect to MQTT
        self.connect_mqtt()
        
    def setup_ui(self):
        """Setup User Interface"""
        
        # ============ HEADER ============
        header_frame = tk.Frame(self.root, bg='#2d2d44', height=100)
        header_frame.pack(fill='x', padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="ESP32 DHT11 Monitoring Dashboard",
            font=('Segoe UI', 24, 'bold'),
            bg='#2d2d44',
            fg='#00ff88'
        )
        title_label.pack(pady=(10, 0))
        
        identity_label = tk.Label(
            header_frame,
            text="Bayu Wicaksono | NIM: 23106050002",
            font=('Segoe UI', 12),
            bg='#2d2d44',
            fg='#b4befe'
        )
        identity_label.pack(pady=(0, 5))
        
        # ============ STATUS BAR ============
        status_frame = tk.Frame(self.root, bg='#2d2d44', height=50)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))
        status_frame.pack_propagate(False)
        
        # Connection Status
        self.connection_label = tk.Label(
            status_frame,
            text="● Disconnected",
            font=('Segoe UI', 11),
            bg='#2d2d44',
            fg='#f38ba8'
        )
        self.connection_label.pack(side='left', padx=20, pady=10)
        
        # Last Update
        self.last_update_label = tk.Label(
            status_frame,
            text="Last Update: --:--:--",
            font=('Segoe UI', 10),
            bg='#2d2d44',
            fg='#cdd6f4'
        )
        self.last_update_label.pack(side='left', padx=10)
        
        # ============ MAIN CONTENT ============
        content_frame = tk.Frame(self.root, bg='#1e1e2e')
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Left Panel - Current Values & Controls
        left_panel = tk.Frame(content_frame, bg='#2d2d44', width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Current Temperature
        temp_frame = tk.Frame(left_panel, bg='#363654', height=150)
        temp_frame.pack(fill='x', padx=15, pady=15)
        temp_frame.pack_propagate(False)
        
        tk.Label(
            temp_frame,
            text="🌡️Suhu",
            font=('Segoe UI', 14, 'bold'),
            bg='#363654',
            fg='#f9e2af'
        ).pack(pady=(15, 5))
        
        self.temp_value_label = tk.Label(
            temp_frame,
            text="--°C",
            font=('Segoe UI', 32, 'bold'),
            bg='#363654',
            fg='#fab387'
        )
        self.temp_value_label.pack()
        
        self.temp_status_label = tk.Label(
            temp_frame,
            text="Waiting for data...",
            font=('Segoe UI', 9),
            bg='#363654',
            fg='#a6adc8'
        )
        self.temp_status_label.pack(pady=(5, 10))
        
        # Current Humidity
        hum_frame = tk.Frame(left_panel, bg='#363654', height=150)
        hum_frame.pack(fill='x', padx=15, pady=(0, 15))
        hum_frame.pack_propagate(False)
        
        tk.Label(
            hum_frame,
            text="💧Kelembapan",
            font=('Segoe UI', 14, 'bold'),
            bg='#363654',
            fg='#89dceb'
        ).pack(pady=(15, 5))
        
        self.hum_value_label = tk.Label(
            hum_frame,
            text="--%",
            font=('Segoe UI', 32, 'bold'),
            bg='#363654',
            fg='#89b4fa'
        )
        self.hum_value_label.pack()
        
        self.hum_status_label = tk.Label(
            hum_frame,
            text="Waiting for data...",
            font=('Segoe UI', 9),
            bg='#363654',
            fg='#a6adc8'
        )
        self.hum_status_label.pack(pady=(5, 10))
        
        # LED Control
        led_frame = tk.Frame(left_panel, bg='#363654')
        led_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        tk.Label(
            led_frame,
            text="💡Kontrol Indikator LED",
            font=('Segoe UI', 14, 'bold'),
            bg='#363654',
            fg='#f5c2e7'
        ).pack(pady=(15, 10))
        
        self.led_status_label = tk.Label(
            led_frame,
            text="Status: DISABLED",
            font=('Segoe UI', 12),
            bg='#363654',
            fg='#f38ba8'
        )
        self.led_status_label.pack(pady=10)
        
        # LED Button
        self.led_button = tk.Button(
            led_frame,
            text="ENABLE",
            font=('Segoe UI', 12, 'bold'),
            bg='#a6e3a1',
            fg='#1e1e2e',
            activebackground='#94e2d5',
            activeforeground='#1e1e2e',
            relief='flat',
            cursor='hand2',
            command=self.toggle_led
        )
        self.led_button.pack(pady=10, padx=30, ipady=10, fill='x')
        
        # LED Indicator Description
        indicator_frame = tk.Frame(led_frame, bg='#363654')
        indicator_frame.pack(pady=10, padx=15, fill='x')
        
        tk.Label(
            indicator_frame,
            text="Indikator LED:",
            font=('Segoe UI', 10, 'bold'),
            bg='#363654',
            fg='#cdd6f4'
        ).pack(anchor='w', pady=(5, 5))
        
        indicators = [
            ("🔴 RED", "Suhu > 30°C"),
            ("🟡 YELLOW", "Suhu 25-30°C"),
            ("🟢 GREEN", "Suhu < 25°C")
        ]
        
        for color, desc in indicators:
            tk.Label(
                indicator_frame,
                text=f"{color}: {desc}",
                font=('Segoe UI', 9),
                bg='#363654',
                fg='#a6adc8'
            ).pack(anchor='w', padx=10, pady=2)
        
        # Right Panel - Charts
        right_panel = tk.Frame(content_frame, bg='#2d2d44')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 6), facecolor='#2d2d44')
        
        # Temperature Chart
        self.ax1 = self.fig.add_subplot(211, facecolor='#1e1e2e')
        self.temp_line, = self.ax1.plot([], [], color='#fab387', linewidth=2, marker='o', markersize=4)
        self.ax1.set_title('Grafik Suhu Real-Time (°C)', color='#f9e2af', fontsize=12, fontweight='bold', pad=10)
        self.ax1.set_ylabel('Suhu (°C)', color='#cdd6f4', fontsize=10)
        self.ax1.tick_params(colors='#a6adc8', labelsize=8)
        self.ax1.grid(True, alpha=0.2, color='#585b70')
        self.ax1.spines['bottom'].set_color('#585b70')
        self.ax1.spines['top'].set_color('#585b70')
        self.ax1.spines['right'].set_color('#585b70')
        self.ax1.spines['left'].set_color('#585b70')
        
        # Humidity Chart
        self.ax2 = self.fig.add_subplot(212, facecolor='#1e1e2e')
        self.hum_line, = self.ax2.plot([], [], color='#89b4fa', linewidth=2, marker='o', markersize=4)
        self.ax2.set_title('Grafik Kelembapan Real-Time (%)', color='#89dceb', fontsize=12, fontweight='bold', pad=10)
        self.ax2.set_ylabel('Kelembapan (%)', color='#cdd6f4', fontsize=10)
        self.ax2.set_xlabel('Time', color='#cdd6f4', fontsize=10)
        self.ax2.tick_params(colors='#a6adc8', labelsize=8)
        self.ax2.grid(True, alpha=0.2, color='#585b70')
        self.ax2.spines['bottom'].set_color('#585b70')
        self.ax2.spines['top'].set_color('#585b70')
        self.ax2.spines['right'].set_color('#585b70')
        self.ax2.spines['left'].set_color('#585b70')
        
        self.fig.tight_layout(pad=3.0)
        
        # Embed matplotlib in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=15, pady=15)
        
    def connect_mqtt(self):
        """Connect to MQTT Broker"""
        try:
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.client_id)
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_message = self.on_message
            
            self.mqtt_client.connect(self.broker, 1883, 60)
            
            # Start MQTT loop in separate thread
            mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever, daemon=True)
            mqtt_thread.start()
            
        except Exception as e:
            print(f"MQTT Connection Error: {e}")
            
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to MQTT"""
        if reason_code == 0:
            self.connected = True
            print(f"Connected to MQTT Broker: {self.broker}")
            
            # Subscribe to topics
            client.subscribe(self.topic_temp)
            client.subscribe(self.topic_hum)
            
            # Update connection status
            self.connection_label.config(text="● Connected", fg='#a6e3a1')
            
        else:
            self.connected = False
            print(f"Connection failed with code {reason_code}")
            
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            current_time = datetime.now()
            
            if msg.topic == self.topic_temp:
                temp = payload.get('temperature')
                if temp is not None:
                    self.temp_data.append(temp)
                    self.time_data.append(current_time)
                    self.update_temperature_display(temp)
                    
            elif msg.topic == self.topic_hum:
                hum = payload.get('humidity')
                if hum is not None:
                    self.hum_data.append(hum)
                    self.update_humidity_display(hum)
            
            # Update last update time
            self.last_update_label.config(text=f"Last Update: {current_time.strftime('%H:%M:%S')}")
            
            # Update charts
            self.update_charts()
            
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def update_temperature_display(self, temp):
        """Update temperature display"""
        self.temp_value_label.config(text=f"{temp}°C")
        
        # Update status based on temperature
        if temp > 30:
            status = "🔴 Suhu Tinggi"
            color = '#f38ba8'
        elif 25 <= temp <= 30:
            status = "🟡 Suhu Normal"
            color = '#f9e2af'
        else:
            status = "🟢 Suhu Rendah"
            color = '#a6e3a1'
            
        self.temp_status_label.config(text=status, fg=color)
        
    def update_humidity_display(self, hum):
        """Update humidity display"""
        self.hum_value_label.config(text=f"{hum}%")
        
        # Update status based on humidity
        if hum > 70:
            status = "Kelembapan Tinggi"
            color = '#89b4fa'
        elif 50 <= hum <= 70:
            status = "Normal Humidity"
            color = '#a6e3a1'
        else:
            status = "Low Humidity"
            color = '#f9e2af'
            
        self.hum_status_label.config(text=status, fg=color)
        
    def update_charts(self):
        """Update line charts"""
        if len(self.time_data) > 0:
            # Update temperature chart
            self.temp_line.set_data(range(len(self.temp_data)), list(self.temp_data))
            self.ax1.relim()
            self.ax1.autoscale_view()
            
            # Update humidity chart
            self.hum_line.set_data(range(len(self.hum_data)), list(self.hum_data))
            self.ax2.relim()
            self.ax2.autoscale_view()
            
            # Set x-axis labels (show only few time labels)
            if len(self.time_data) > 5:
                step = max(1, len(self.time_data) // 5)
                x_ticks = range(0, len(self.time_data), step)
                x_labels = [self.time_data[i].strftime('%H:%M:%S') for i in x_ticks]
                self.ax2.set_xticks(x_ticks)
                self.ax2.set_xticklabels(x_labels, rotation=45, ha='right')
            
            # Redraw canvas
            self.canvas.draw()
            
    def toggle_led(self):
        """Toggle LED control"""
        if not self.connected:
            print("Not connected to MQTT broker")
            return
            
        self.led_enabled = not self.led_enabled
        
        if self.led_enabled:
            message = "on"
            self.led_button.config(
                text="DISABLE",
                bg='#f38ba8',
                activebackground='#eba0ac'
            )
            self.led_status_label.config(
                text="Status: ENABLED",
                fg='#a6e3a1'
            )
        else:
            message = "off"
            self.led_button.config(
                text="ENABLE",
                bg='#a6e3a1',
                activebackground='#94e2d5'
            )
            self.led_status_label.config(
                text="Status: DISABLED",
                fg='#f38ba8'
            )
        
        # Publish to MQTT
        self.mqtt_client.publish(self.topic_led, message)
        print(f"LED Control: {message.upper()}")
        
    def on_closing(self):
        """Handle window closing"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MQTTDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
