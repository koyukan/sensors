import imufusion
import numpy as np

class AhrsProcessor:
    def __init__(self, sample_rate=5, gain=0.5, gyroscope_range=2000, acceleration_rejection=100, magnetic_rejection=100, recovery_trigger_period=5*10):
        self.sample_rate = sample_rate
        self.ahrs = imufusion.Ahrs()
        self.offset = imufusion.Offset(self.sample_rate)

        # Ensure you're using the correct data types and values
        convention = imufusion.CONVENTION_NWU  # This needs to be of a correct type, sometimes might be an int or enum
     

        # Configure the AHRS algorithm settings
        try:
            self.ahrs.settings = imufusion.Settings(
                convention,  # Ensure this is the correct type
                gain,  # float
                gyroscope_range,  # float or int
                acceleration_rejection,  # float
                magnetic_rejection,  # float
                int(recovery_trigger_period)  # explicitly cast to int if necessary
            )
        except TypeError as e:
            print(f"Error initializing settings: {e}")

    def process_sensor_data(self, gyro, accel, mag, orientation = None, timestamp = None):
        
    

        # Calculate delta time
        if not hasattr(self, 'last_timestamp'):
            self.last_timestamp = timestamp
            delta_time = 0
        else:
            delta_time = timestamp - self.last_timestamp
            self.last_timestamp = timestamp

        # Apply offset to gyroscope data
        gyro_to_degree = gyro * (180 / np.pi)
        corrected_gyro = self.offset.update(np.array(gyro_to_degree))

        # Update AHRS algorithm with current sensor data
        self.ahrs.update(corrected_gyro, np.array(accel)/9.80665, np.array(mag), delta_time)

        # Get the quaternion and convert to Euler angles
        quaternion = self.ahrs.quaternion
        euler_angles = quaternion.to_euler()  # Returns Euler angles in degrees
        quaternion_matrix =  np.array(quaternion.wxyz) 
        
       

        # Retrieve internal states and flags
        internal_states = self.ahrs.internal_states
        flags = self.ahrs.flags

        # Package output data
        output_data = {
            'timestamp': timestamp,
            'quaternion': quaternion_matrix,
            'euler_angles': euler_angles,
            'internal_states': {
                'acceleration_error': internal_states.acceleration_error,
                'accelerometer_ignored': internal_states.accelerometer_ignored,
                'acceleration_recovery_trigger': internal_states.acceleration_recovery_trigger,
                'magnetic_error': internal_states.magnetic_error,
                'magnetometer_ignored': internal_states.magnetometer_ignored,
                'magnetic_recovery_trigger': internal_states.magnetic_recovery_trigger
            },
            'flags': {
                'initialising': flags.initialising,
                'angular_rate_recovery': flags.angular_rate_recovery,
                'acceleration_recovery': flags.acceleration_recovery,
                'magnetic_recovery': flags.magnetic_recovery
            }
        }

        if orientation is not None:
            output_data['orientation'] = orientation

        return output_data
