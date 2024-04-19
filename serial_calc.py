# Import the EulerSerial class
from euler_serial import EulerSerial

# Define a handler function for new data
def handle_new_data(data):
    print("Received data:", data)

# Create an instance of EulerSerial
euler_reader = EulerSerial('/dev/ttyACM0')
euler_reader.set_on_data_handler(handle_new_data)

# Start reading
euler_reader.start_reading()

try:
    # Keep the main thread running, otherwise Python will exit
    input("Press enter to stop...\n")
finally:
    euler_reader.close()
