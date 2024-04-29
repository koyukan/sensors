import serial
import threading
import time

class EulerSerial:
    def __init__(self, port, baud_rate=115200):
        """
        Initialize the serial connection.
        :param port: The port to connect to, e.g., '/dev/ttyACM0'.
        :param baud_rate: The baud rate for the serial connection. Default is 115200.
        """
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.initialize_serial()
        self.on_data = None
        self.on_calibration_start = None
        self.on_calibration_end = None
        self.running = False

    def initialize_serial(self):
        while self.ser is None:
            try:
                self.ser = serial.Serial(self.port, self.baud_rate)
                self.ser.flushInput()
                print("Connected successfully to", self.port)
            except serial.SerialException as e:
                print(f"Failed to connect to {self.port}: {e}. Retrying in 5 seconds...")
                time.sleep(1)

    def set_on_data_handler(self, handler):
        """
        Set the function that will be called when new sensor data is received.
        :param handler: A function to call with the new data.
        """
        self.on_data = handler

    def set_on_calibration_start_handler(self, handler):
        """
        Set the function that will be called when calibration starts.
        :param handler: A function to call with the start calibration message.
        """
        self.on_calibration_start = handler

    def set_on_calibration_end_handler(self, handler):
        """
        Set the function that will be called when calibration ends.
        :param handler: A function to call with the end calibration message.
        """
        self.on_calibration_end = handler

    def start_reading(self):
        """
        Start reading data from the serial port in a separate thread.
        """
        self.running = True
        thread = threading.Thread(target=self._read_loop)
        thread.start()

    def _read_loop(self):
        """
        Continuously reads data from the serial port in a dedicated thread, handling different types of messages.
        """
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    # Handle start of compass calibration
                    if "Start compass calibration" in data:
                        if self.on_calibration_start:
                            self.on_calibration_start(data)
                        print("Compass calibration has started.")
                    
                    # Handle end of compass calibration
                    elif "End of compass calibration" in data:
                        if self.on_calibration_end:
                            self.on_calibration_end("Compass calibration completed successfully.")
                        print("Compass calibration has ended successfully.")
                    
                    # Informative logging for accelerometer and gyroscope calibration
                    elif "Calibrating Accelerometer and Gyroscope" in data:
                        print("Calibration of Accelerometer and Gyroscope has started.")
                    
                    # Informative logging for the end of accelerometer and gyroscope calibration
                    elif "Accelerometer & Gyro calibration complete" in data:
                        print("Accelerometer and Gyroscope calibration completed successfully.")
                    
                    # Log any specific biases detected during calibration
                    elif "Acc Bias" in data:
                        print("Calibration biases:", data)
                    
                    # Log the empty line between calibration and sensor data
                    elif data == "":
                        print("End of calibration cycle.")

                    # Handle regular sensor data
                    elif self.on_data:
                        self.on_data(data)
                    
            except (serial.SerialException, OSError) as e:
                # Log the error and attempt to reconnect
                print("Connection lost... attempting to reconnect. Error:", e)
                self.ser.close()  # Properly close the connection
                self.ser = None
                # Attempt to reconnect until successful
                while self.ser is None:
                    time.sleep(5)
                    self.initialize_serial()




    def stop_reading(self):
        """
        Stop the reading loop.
        """
        self.running = False

    def close(self):
        """
        Close the serial connection.
        """
        self.stop_reading()
        if self.ser:
            self.ser.close()
