from ahrsPhoneSensor import SensorDataHandler

def callback(data):
    print('incoming data: ', data)

#main function
if __name__ == "__main__":
    handler = SensorDataHandler("10.0.0.128:8080", ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field"], debugLevel=5)
    handler.connect()
    handler.add_callback(callback)
    print("Connected to server")