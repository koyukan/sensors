import asyncio
from euler_serial import EulerSerial

def on_calibration(message):
    # Handle calibration messages here
    print("Handling calibration message:", message)
    # You could update some status indicators in your application's UI, for example
    
def handle_data(message):
    print("Handling data message:", message)
    try:
        print("Message:", message)
    except ValueError:
        print("Error: One of the values is not a valid number.")
        print("Message:", message)

async def main():
    # Create an instance of EulerSerial
    euler_reader = EulerSerial('/dev/ttyACM0', baud_rate=921600)
    
    # Set the handlers
    euler_reader.set_on_data_handler(handle_data)
    euler_reader.set_on_calibration_start_handler(on_calibration)
    euler_reader.set_on_calibration_end_handler(on_calibration)
    
    # Start reading
    await euler_reader.start_reading()
    
    # Keep the program running until user input to stop
    await asyncio.sleep(0.1)  # Give some time for the initial setup
    print("Press Ctrl+C to stop...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        await euler_reader.stop_reading()
        await euler_reader.close()

if __name__ == "__main__":
    asyncio.run(main())
