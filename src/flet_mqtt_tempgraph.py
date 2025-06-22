import flet as ft
import paho.mqtt.client as mqtt
import time
from threading import Thread
from collections import deque

# Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "temperaturas/sonda1"
MAX_DATA_POINTS = 50  # Number of points to keep in memory

# Global data storage
temperature_data = deque(maxlen=MAX_DATA_POINTS)
timestamps = deque(maxlen=MAX_DATA_POINTS)

# MQTT Client Setup
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        temp = float(msg.payload.decode())
        print(f"Received temperature: {temp}°C")
        temperature_data.append(temp)
        timestamps.append(time.time())
    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Start MQTT client in background thread
def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, 1883, 60)
    mqtt_client.loop_forever()

mqtt_thread = Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# Flet App
def main(page: ft.Page):
    page.title = "Live MQTT Temperature Monitor"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    
    # UI Elements
    title = ft.Text("Live Temperature Data", size=24, weight=ft.FontWeight.BOLD)
    status = ft.Text(f"Connected to: {MQTT_BROKER} | Topic: {MQTT_TOPIC}")
    current_temp = ft.Text("Waiting for data...", size=20)
    chart = ft.LineChart()
    
    # Configure Chart
    chart.expand = True
    chart.tooltip_bgcolor = ft.colors.with_opacity(0.8, ft.colors.WHITE)
    chart.min_y = -50
    chart.max_y = 100  # Adjust based on expected temperature range
    chart.min_x = 0
    chart.max_x = MAX_DATA_POINTS
    chart.border = ft.border.all(1, ft.colors.GREY_400)
    
    # Create chart data series
    data_series = ft.LineChartData(
        color=ft.colors.BLUE,
        stroke_width=2,
        curved=True,
        stroke_cap_round=True,
        below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE),
        data_points=[
            ft.LineChartDataPoint(i, 0) for i in range(MAX_DATA_POINTS)
        ]
    )
    
    chart.data_series = [data_series]
    
    # Add UI elements to page
    page.add(
        ft.Column(
            [
                title,
                status,
                current_temp,
                ft.Container(chart, height=300, width=600),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
    
    # Update function that runs periodically
    def update_ui():
        while True:
            if temperature_data:
                # Update current temperature display
                current_temp.value = f"Current: {temperature_data[-1]:.1f}°C"
                
                # Update chart data points
                for i, temp in enumerate(temperature_data):
                    data_series.data_points[i] = ft.LineChartDataPoint(i, temp)
                
                # Shift older data to the left
                chart.min_x = max(0, len(temperature_data) - MAX_DATA_POINTS)
                chart.max_x = max(MAX_DATA_POINTS, len(temperature_data))
                
                # Refresh the page
                chart.update()
                current_temp.update()
            
            time.sleep(0.5)  # Update twice per second
    
    # Start update thread
    update_thread = Thread(target=update_ui, daemon=True)
    update_thread.start()

# Run the app
# ======================================
ft.app(target=main, view=ft.WEB_BROWSER)
