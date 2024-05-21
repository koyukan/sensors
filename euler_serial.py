import asyncio
import serial_asyncio

class EulerSerial:
    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.reader = None
        self.writer = None
        self.on_data = None
        self.on_calibration_start = None
        self.on_calibration_end = None
        self.running = False

    async def initialize_serial(self):
        while self.reader is None or self.writer is None:
            try:
                self.reader, self.writer = await serial_asyncio.open_serial_connection(
                    url=self.port, baudrate=self.baud_rate
                )
                print("Connected successfully to", self.port)
            except serial.serialutil.SerialException as e:
                print(f"Failed to connect to {self.port}: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    def set_on_data_handler(self, handler):
        self.on_data = handler

    def set_on_calibration_start_handler(self, handler):
        self.on_calibration_start = handler

    def set_on_calibration_end_handler(self, handler):
        self.on_calibration_end = handler

    async def start_reading(self):
        await self.initialize_serial()
        self.running = True
        asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        while self.running:
            try:
                if self.reader:
                    data = await self.reader.readline()
                    data = data.decode('utf-8').strip()
                    
                    if "Start compass calibration" in data:
                        if self.on_calibration_start:
                            asyncio.create_task(self.on_calibration_start(data))
                        print("Compass calibration has started.")
                    
                    elif "End of compass calibration" in data:
                        if self.on_calibration_end:
                            asyncio.create_task(self.on_calibration_end("Compass calibration completed successfully."))
                        print("Compass calibration has ended successfully.")
                    
                    elif "Calibrating Accelerometer and Gyroscope" in data:
                        print("Calibration of Accelerometer and Gyroscope has started.")
                    
                    elif "Accelerometer & Gyro calibration complete" in data:
                        print("Accelerometer and Gyroscope calibration completed successfully.")
                    
                    elif "Acc Bias" in data:
                        print("Calibration biases:", data)
                    
                    elif data == "":
                        print("Received empty line.")

                    elif self.on_data:
                        print("Data:", data)
                        data_split = data.split()
                        dict_data = {
                            "timestamp": int(data_split[0]),
                            "accel": [float(data_split[1]), float(data_split[2]), float(data_split[3])],
                            "gyro": [float(data_split[4]), float(data_split[5]), float(data_split[6])],
                            "mag": [float(data_split[7]), float(data_split[8]), float(data_split[9])]
                        }
                        asyncio.create_task(self.on_data(dict_data))
                    
            except (serial.serialutil.SerialException, OSError) as e:
                print("Connection lost... attempting to reconnect. Error:", e)
                self.reader = None
                self.writer = None
                await self.initialize_serial()

    async def stop_reading(self):
        self.running = False

    async def close(self):
        await self.stop_reading()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
