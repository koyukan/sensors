# Filename: euler_serial.py

import serial
import threading

class EulerSerial:
    def __init__(self, port, baud_rate=115200):
        """
        Initialize the serial connection.
        :param port: The port to connect to, e.g., '/dev/ttyACM0'.
        :param baud_rate: The baud rate for the serial connection. Default is 115200.
        """
        self.ser = serial.Serial(port, baud_rate)
        self.ser.flushInput()
        self.on_data = None
        self.running = False

    def set_on_data_handler(self, handler):
        """
        Set the function that will be called when new data is received.
        :param handler: A function to call with the new data.
        """
        self.on_data = handler

    def start_reading(self):
        """
        Start reading data from the serial port in a separate thread.
        """
        self.running = True
        thread = threading.Thread(target=self._read_loop)
        thread.start()

    def _read_loop(self):
        """
        The loop that runs in a separate thread to read data from the serial port.
        """
        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if self.on_data:
                        self.on_data(data)
        except Exception as e:
            print(f"Error reading from serial port: {e}")
            self.close()

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
        self.ser.close()
