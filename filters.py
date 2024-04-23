# fir_filter.py
class FIRFilter:
    """A simple Finite Impulse Response (FIR) filter."""
    def __init__(self, length=10, coefficient=0.1):
        self.buffer = [0.0] * length
        self.coefficient = coefficient
        self.length = length
        self.index = 0

    def update(self, value):
        """Update the filter with a new value and return the filtered output."""
        self.buffer[self.index] = value
        self.index = (self.index + 1) % self.length
        return sum(self.buffer) * self.coefficient


class RCFilter:
    """A simple first-order low-pass RC filter."""
    def __init__(self, cutoff_freq_hz, sample_time_s):
        """
        Initialize the RC filter with a cutoff frequency and sample time.
        :param cutoff_freq_hz: Cutoff frequency of the filter in Hertz.
        :param sample_time_s: Sample time in seconds.
        """
        # Compute the equivalent 'RC' time constant from the cutoff frequency
        RC = 1.0 / (6.28318530718 * cutoff_freq_hz)

        # Pre-compute filter coefficients
        self.coeff_a = sample_time_s / (sample_time_s + RC)
        self.coeff_b = RC / (sample_time_s + RC)

        # Initialize the output buffer
        self.previous_output = 0.0

    def update(self, inp):
        """
        Update the filter with a new input value and return the filtered output.
        :param inp: New input value for the filter.
        :return: Filtered output value.
        """
        # Compute new output sample
        current_output = self.coeff_a * inp + self.coeff_b * self.previous_output

        # Update the previous output with the current output
        self.previous_output = current_output

        return current_output
