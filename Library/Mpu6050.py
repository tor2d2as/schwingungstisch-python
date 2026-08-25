"""
---------------------------------------------------------------------------
Copyright notice for this file:
---------------------------------------------------------------------------
Released under the MIT License
Copyright (c) 2015, 2016, 2017, 2021 Martijn (martijn@mrtijn.nl) and contributers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Original file from: https://github.com/m-rtijn/mpu6050
---------------------------------------------------------------------------
End of the Copyright notice 
---------------------------------------------------------------------------

This program handles the communication over I2C
between a Raspberry Pi and a MPU-6050 Gyroscope / Accelerometer combo.

-------------------------
This is a modified version for the project "Schwingungstisch", it is not fully
compatible with the original version of this libary
-------------------------
"""

import smbus
import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal
import RPi.GPIO as GPIO

from collections import deque
from statistics import mean
import heapq

from MCP4921 import MCP4921

class Mpu6050(QObject):

    # Global Variables
    GRAVITIY_MS2 = 9.80665
    address = None
    bus = None

    # Scalemodifiers
    ACCEL_SCALE_MODIFIER_2G = 16384.0
    ACCEL_SCALE_MODIFIER_4G = 8192.0
    ACCEL_SCALE_MODIFIER_8G = 4096.0
    ACCEL_SCALE_MODIFIER_16G = 2048.0
    #The initial value will be set during initialisiation
    current_accel_scale_modifier = -1

    # Pre-defined ranges
    ACCEL_RANGE_2G = 0x00
    ACCEL_RANGE_4G = 0x08
    ACCEL_RANGE_8G = 0x10
    ACCEL_RANGE_16G = 0x18

    #The frequencies in the variable names are referring to the gyroscope, the frequencies for the acceleration sensor are mentioned in the brackets behind. 
    FILTER_BW_256=0x00 #260
    FILTER_BW_188=0x01 #184
    FILTER_BW_98=0x02  #94
    FILTER_BW_42=0x03  #44
    FILTER_BW_20=0x04  #21
    FILTER_BW_10=0x05  #10 (the same for both)
    FILTER_BW_5=0x06   #5  (the same for both)

    # MPU-6050 register
    PWR_MGMT_1 = 0x6B
    #PWR_MGMT_2 = 0x6C
    
    SIGNAL_PATH_RESET = 0x68

    ACCEL_XOUT0 = 0x3B
    ACCEL_YOUT0 = 0x3D
    ACCEL_ZOUT0 = 0x3F

    ACCEL_CONFIG = 0x1C
    MPU_CONFIG = 0x1A
    
    SMPRT_DIV = 0x19 #Sample Rate Divider
    update_data_periodic = False #Will be used to stop the loop, which is used to print the values on the UI. 
    output_on_oszi = False #Will be used to stop the loop, which is used to set the voltage output on the oscilloscope.
    #enable_fit_oszi_out = False| (Will be initialized in the init method) Used to adjust the oscilloscope output to cover the full range of the accelerometer, or only to the maximum value of the accelerometer
    adjust_oszi_out = -1 #Used to optimize the voltage output for the oscilloscope
    enable_higher_max_accel = False #Specify whether the table should accelerate to 1 g or 1.5 g.
    periodic_output_register = ACCEL_YOUT0 #Defines the register used to read the measured acceleration values (The sensor can measure in X, Y and Z and we need only one axis)
        
    update_accel_UI = pyqtSignal(float) #Sends the current acceleration to Main_UI
    
    def __init__(self, address, mBluetooth_module, enable_fit_oszi_out, bus=1):
        super().__init__()
        self.bluetooth_module = mBluetooth_module
        self.address = address
        self.bus = smbus.SMBus(bus)
        self.mcp4921 = MCP4921()
        # Wake up the MPU-6050 since it starts in sleep mode
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x00)
        self.enable_fit_oszi_out = enable_fit_oszi_out
        self._update_accel_scale_modifier()
        #self._update_gyro_scale_modifier()
    
    def read_filter_range(self):
        """Reads the low-pass filter frequency, it returns -1 if an error occurs
        return values coding:
        0 = accel: 260 Hz, Gyro: 256 Hz
        1 = accel: 184 Hz, Gyro: 188 Hz
        2 = accel: 94 Hz, Gyro: 98 Hz
        3 = accel: 44 Hz, Gyro: 42 Hz
        4 = accel: 21 Hz, Gyro: 20 Hz
        5 = accel: 10 Hz, Gyro: 10 Hz
        6 = accel: 5 Hz, Gyro: 5 Hz"""
        ret_val = -1
        
        # Only the last 3 bit from the register are relevant for the frequency
        raw_data = self.bus.read_byte_data(self.address, self.MPU_CONFIG) & 0b00000111
        if raw_data == self.FILTER_BW_256:
            ret_val = 0
        elif raw_data == self.FILTER_BW_188:
            ret_val = 1
        elif raw_data == self.FILTER_BW_98:
            ret_val = 2
        elif raw_data == self.FILTER_BW_42:
            ret_val = 3
        elif raw_data == self.FILTER_BW_20:
            ret_val = 4
        elif raw_data == self.FILTER_BW_10:
            ret_val = 5
        elif raw_data == self.FILTER_BW_5:
            ret_val = 6
        return ret_val
    
    def read_sample_rate_divider(self):
        """ Returns the value for the sample rate divider. This value is required to calculate the sample rate. """
        return self.bus.read_byte_data(self.address, self.SMPRT_DIV)
    
    def set_sample_rate_divider(self, sample_rate_divider):
        """It sets the sample rate divider (0-255). With this value and the Output Rate (for Accelarator and Gyroskop)
        the sample rate can be specified. The output rate can be calculated by the 'sample_rate = Output_rate / (1 + sample_rate_divider)"""
        #Ensures that only values between 0 and 255 are written to the register.
        if (sample_rate_divider >= 0) and (sample_rate_divider <= 255):
            # First change it to 0x00 to make sure we write the correct value later
            self.bus.write_byte_data(self.address, self.SMPRT_DIV, 0x00)

            # Write the new range to the SMPRT_DIV register
            self.bus.write_byte_data(self.address, self.SMPRT_DIV, sample_rate_divider)
        else:
            print("The sample_rate_divider hasn't changed. It has to be in a range between 0 and 255.")
            
    def reset_mpu6050(self):
        """It resets all register of the MPU6050 to default and wakes the devices up"""
        #raw_data = self.bus.read_byte_data(self.address, self.PWR_MGMT_1) & 0b01111111
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1,  0b10000000)# | raw_data)
        # Wake up the MPU-6050 since it goes to sleep mode during the reset
        time.sleep(0.1)
        
        raw_data = self.bus.read_byte_data(self.address, self.SIGNAL_PATH_RESET) & 0b11111000
        self.bus.write_byte_data(self.address, self.SIGNAL_PATH_RESET,  0b00000111 | raw_data)
        time.sleep(0.1)
        self.bus.write_byte_data(self.address, self.PWR_MGMT_1, 0x00)
        
    def stop_data_periodic(self):
        """ It stops the update of the acceleration sensor on the UI. """
        self.update_data_periodic = False
        
    def start_data_periodic(self):
        """ By calling, the accelaration values will be periodically read out from the sensor and updated on the UI.
            It also sends the values to the phone App (if connected). """
        if self.update_data_periodic is False:
            self.update_data_periodic = True
            self.timeout = True
            self.y_accel = 0
            self.data = deque(maxlen=2000)

            self.acceleration_to_send = 0.0
            self.old_acceleration_to_send = -1.0
            self.notify_data_to_UI_Event = threading.Event()
            self.send_data_to_ui_thread = threading.Thread(target=self._send_data_to_UI)
            self.send_data_to_ui_thread.start()
            threading.Thread(target=self._get_data_periodic).start()
            
    def _get_data_periodic(self):
        """ It reads the data from the MPU6050 as fast as possible. If the oscilloscope output is on, it will set the value to the oscilloscope output 
            (if disabled, the value will be set to 0). Furthermore, all values will be saved temporarily.
            On an external thread: Every 0,25 sec., it will calculate the acceleration value from the 50 highest measured values 
            and send them to the Main_UI, and, if connected, also to the phone App. """
        while(self.update_data_periodic):
            try:
                self.y_accel = self.read_i2c_word(self.periodic_output_register)
            except Exception as e:
                print(e)
                continue
            
            if self.output_on_oszi:
                self.mcp4921.setOutput(int(self.y_accel/self.adjust_oszi_out)+2048)
                if not self.output_on_oszi:
                    #This event can occur because we update the self.output_on_oszi variable from a different thread.
                    self.mcp4921.stop()
            
            accel = self.calculate_accel_for_ui(self.y_accel)
            #print(accel)
            self.data.append(abs(accel))
            
            if self.timeout:
                self.acceleration_to_send = round(mean(heapq.nlargest(50, self.data)), 2)
                self.notify_data_to_UI_Event.set()

        #Make sure the thread ends properly
        if self.send_data_to_ui_thread.is_alive():
            self.notify_data_to_UI_Event.set()
            self.send_data_to_ui_thread.join()
        self.acceleration_to_send = 0.0
        self._update_UI()
        self.timeout = True
        #self._send_data_to_UI()
        
    def calculate_accel_for_ui(self, value):
        """ It calculates the acceleration value in m/s^2. """
        return round(value/self.current_accel_scale_modifier * self.GRAVITIY_MS2, 2)
        
            
    def _send_data_to_UI(self):
        """ It has to run on an external Thread and self.notify_data_to_UI_Event has to be exist.
            It updates the UI approx. every 0,25 sec. with the new value in self.acceleration_to_send
            and also sends the value via Bluetooth.
            Notify new data with: self.notify_data_to_UI_Event.set()
             """
        while(self.update_data_periodic):
            self.notify_data_to_UI_Event.wait()
            self.notify_data_to_UI_Event.clear()
            self.timeout = False
            self._update_UI()
            time.sleep(0.25)
            self.timeout = True

    def _update_UI(self):
        """ It sends the value in self.notify_data_to_UI_Event.set() to the UI and via Bluetooth """
        acceleration = self.acceleration_to_send
        if self.old_acceleration_to_send is not acceleration:
            self.old_acceleration_to_send = acceleration
            self.update_accel_UI.emit(acceleration)
            self.bluetooth_module.send_data_to_phone("{\"actual_accel\":\"%s\"}" % acceleration)
        
            
    def stop_oszi_out(self):
        """ Stops the oscilloscope output. """
        self.output_on_oszi = False
        self.mcp4921.stop()
        
    def start_oszi_out(self):
        """ The method starts the output of the acceleration values on the MCP4921 (Oscilloscope output).
            Furthermore, it resets the scaling factor for the Oscilloscope Output."""
        if self.output_on_oszi is False:
            self.mcp4921.start()
            self.change_adjust_oszi_out()
            self.output_on_oszi = True
            print("Das Signal wird nun auf das Oszi ausgegeben")
            
    def change_adjust_oszi_out(self):
        """ Calculates the factor by which the measured acceleration value should be divided.
            To do this, simply call the method when changing the settings; the value self.adjust_oszi_out
            is updated globally within the class and is therefore immediately available the next time the oscilloscope outputs a value."""
        if self.enable_fit_oszi_out:
            modifier = self.current_accel_scale_modifier/2048
            if self.enable_higher_max_accel:
                modifier = modifier * 1.5
            
            self.adjust_oszi_out = modifier
        else:
            self.adjust_oszi_out = 16
        #print("enable oszi out", self.enable_fit_oszi_out)
        #print("scale mod:", self.current_accel_scale_modifier)
        #print("oszi Anpassung:", self.adjust_oszi_out)

    # I2C communication methods

    def read_i2c_word(self, register, only_positive=False):
        """Read two i2c registers and combine them.

        Note: This method throws an error if the accelerometer does not respond -> Use a try-catch block

        register -- the first register to read from.
        Returns the combined read results.
        """
        # Read the data from the registers
        high = self.bus.read_byte_data(self.address, register)
        low = self.bus.read_byte_data(self.address, register + 1)

        value = (high << 8) + low
        if only_positive:
            return value
        else:
            if (value >= 0x8000):
                return -((65535 - value) + 1)
            else:
                return value

    # MPU-6050 Methods

    def set_accel_range(self, accel_range):
        """Sets the range of the accelerometer to range.

        accel_range -- the range to set the accelerometer to. Using a
        pre-defined range is advised.
        """
        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, 0x00)

        # Write the new range to the ACCEL_CONFIG register
        self.bus.write_byte_data(self.address, self.ACCEL_CONFIG, accel_range)
        self._update_accel_scale_modifier()

    def read_accel_range(self, raw = False):
        """Reads the range the accelerometer is set to.

        If raw is True, it will return the raw value from the ACCEL_CONFIG register
        If raw is False, it will return an integer: 0 for 2g, 1 for 4g, 2 for 8g or 3 for 16g.
        When it returns -1 something went wrong.
        """
        raw_data = self.bus.read_byte_data(self.address, self.ACCEL_CONFIG)
        self._update_accel_scale_modifier(raw_data)

        if raw is True:
            return raw_data
        elif raw is False:
            if raw_data == self.ACCEL_RANGE_2G:
                return 0 #2g
            elif raw_data == self.ACCEL_RANGE_4G:
                return 1 #4g
            elif raw_data == self.ACCEL_RANGE_8G:
                return 2 #8g
            elif raw_data == self.ACCEL_RANGE_16G:
                return 3 #16g
            else:
                return -1
        
    def _update_accel_scale_modifier(self, raw_data = None):
        """ It reads the current value range of the acceleration sensor on the MPU6050 and safes it in the variable: self.current_accel_scale_modifier.
            It also updates the output scale for the oscilloscope. """
        accel_scale_modifier = None
        if raw_data is None:
            accel_range = self.bus.read_byte_data(self.address, self.ACCEL_CONFIG)
        else:
            accel_range = raw_data

        if accel_range == self.ACCEL_RANGE_2G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
        elif accel_range == self.ACCEL_RANGE_4G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_4G
        elif accel_range == self.ACCEL_RANGE_8G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_8G
        elif accel_range == self.ACCEL_RANGE_16G:
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_16G
        else:
            print("Unkown range - accel_scale_modifier set to self.ACCEL_SCALE_MODIFIER_2G")
            accel_scale_modifier = self.ACCEL_SCALE_MODIFIER_2G
            
        self.current_accel_scale_modifier = accel_scale_modifier
        self.change_adjust_oszi_out()
    
    
    def set_filter_range(self, filter_range):
        """ Sets the low-pass bandpass filter frequency.
        NOTE: The values for the acceleration sensor are differing slightly."""
        # Keep the current EXT_SYNC_SET configuration in bits 3, 4, 5 in the MPU_CONFIG register
        #The bits 6, 7 aren't defined yet and shouldn't be changed, just in case
        
        EXT_SYNC_SET = self.bus.read_byte_data(self.address, self.MPU_CONFIG) & 0b11111000
        
        # First change it to 0x00 to make sure we write the correct value later
        self.bus.write_byte_data(self.address, self.MPU_CONFIG, EXT_SYNC_SET & 0b11111000)
        
        return self.bus.write_byte_data(self.address, self.MPU_CONFIG,  EXT_SYNC_SET | filter_range)
    
#     GYRO_RANGE_250DEG = 0x00
#     GYRO_RANGE_500DEG = 0x08
#     GYRO_RANGE_1000DEG = 0x10
#     GYRO_RANGE_2000DEG = 0x18
    
#     current_gyro_scale_modifier = -1

#     GYRO_SCALE_MODIFIER_250DEG = 131.0
#     GYRO_SCALE_MODIFIER_500DEG = 65.5
#     GYRO_SCALE_MODIFIER_1000DEG = 32.8
#     GYRO_SCALE_MODIFIER_2000DEG = 16.4

#     TEMP_OUT0 = 0x41
# 
#     GYRO_XOUT0 = 0x43
#     GYRO_YOUT0 = 0x45
#     GYRO_ZOUT0 = 0x47

#     GYRO_CONFIG = 0x1B


#    def _get_sensor_register(self, register, scale_modifier):
#        """It reads the given register, and divides them through the scale modifier"""
#        raw = self.read_i2c_word(register)
#        return raw / scale_modifier


#     def get_accel_data(self, g = False):
#         """Gets and returns the X, Y and Z values from the accelerometer.
# 
#         If g is True, it will return the data in g
#         If g is False, it will return the data in m/s^2
#         Returns a dictionary with the measurement results.
#         """
#         x = self._get_sensor_register(self.ACCEL_XOUT0, self.current_accel_scale_modifier)
#         y = self._get_sensor_register(self.ACCEL_YOUT0, self.current_accel_scale_modifier)
#         z = self._get_sensor_register(self.ACCEL_ZOUT0, self.current_accel_scale_modifier)
# 
#         if g is True:
#             return {'x': x, 'y': y, 'z': z}
#         elif g is False:
#             x = x * self.GRAVITIY_MS2
#             y = y * self.GRAVITIY_MS2
#             z = z * self.GRAVITIY_MS2
#             return {'x': x, 'y': y, 'z': z}


#     def read_sample_rate_accel(self):
#         """ It returns the sample rate for the accelrator in Hz
#         NOTE: If the sample rate for accelarator and gyroscope differs, the same values for the accelarator
#         can be written multiple times to the register """
#         SMPRT_DIV = self.read_sample_rate_divider()
#         #accel_rate = self.read_output_rate_in_Hz()['accel_rate']
#         #accel_sr = accel_rate / (1 + SMPRT_DIV)
#         accel_sr = 1000 / (1 + SMPRT_DIV)
#         
#         return accel_sr

#     def read_output_rate_in_Hz(self):
#         """It returns the output rate of the gyroscope and accelarator in Hz
#         NOTE: The output rate for the accelarator is always 1000 Hz"""
#         raw_data = self.bus.read_byte_data(self.address, self.MPU_CONFIG) & 0b00000111
#         gyro_rate = 1000
#         #The value 0x07 is a reserved bit, which can't be set with this libary 
#         if (raw_data == self.FILTER_BW_256) or (raw_data == 0x07):
#             gyro_rate = 8000
#         return {'accel_rate': 1000, 'gyro_rate': gyro_rate}
    
#     def read_sample_rate_gyro(self):
#         """ It returns the sample rate for the gyroscope in Hz
#         NOTE: If the sample rate for accelarator and gyroscope differs, the same values for the accelarator
#         can be written multiple times to the """
#         SMPRT_DIV = self.read_sample_rate_divider()
#         gyro_rate = self.read_output_rate_in_Hz()['gyro_rate']
#         
#         gyro_sr = gyro_rate / (1 + SMPRT_DIV)
#         
#         return gyro_sr
    
#     def get_temp(self):
#         """Reads the temperature from the onboard temperature sensor of the MPU-6050.
# 
#         Returns the temperature in degrees Celcius.
#         """
#         raw_temp = self.read_i2c_word(self.TEMP_OUT0)
# 
#         # Get the actual temperature using the formule given in the
#         # MPU-6050 Register Map and Descriptions revision 4.2, page 30
#         actual_temp = (raw_temp / 340.0) + 36.53
# 
#         return actual_temp
        
#     def _update_gyro_scale_modifier(self, raw_data=None):
#         """ Es liest den aktuellen Wertbereich des Gyroskops vom MPU6050 aus und errechnet damit
#             einen ScaleModifier. Dieser wird verwendet, damit der korrekte Wert für die Drehbewegung ausgegeben werden kann."""
#         gyro_scale_modifier = None
#         if raw_data is None:
#             gyro_range = self.bus.read_byte_data(self.address, self.GYRO_CONFIG)
#         else:
#             gyro_range = raw_data
# 
#         if gyro_range == self.GYRO_RANGE_250DEG:
#             gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
#         elif gyro_range == self.GYRO_RANGE_500DEG:
#             gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_500DEG
#         elif gyro_range == self.GYRO_RANGE_1000DEG:
#             gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_1000DEG
#         elif gyro_range == self.GYRO_RANGE_2000DEG:
#             gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_2000DEG
#         else:
#             print("Unkown range - gyro_scale_modifier set to self.GYRO_SCALE_MODIFIER_250DEG")
#             gyro_scale_modifier = self.GYRO_SCALE_MODIFIER_250DEG
#         self.current_gyro_scale_modifier = gyro_scale_modifier

#     def set_gyro_range(self, gyro_range):
#         """Sets the range of the gyroscope to range.
# 
#         gyro_range -- the range to set the gyroscope to. Using a pre-defined
#         range is advised.
#         """
#         # First change it to 0x00 to make sure we write the correct value later
#         self.bus.write_byte_data(self.address, self.GYRO_CONFIG, 0x00)
# 
#         # Write the new range to the ACCEL_CONFIG register
#         self.bus.write_byte_data(self.address, self.GYRO_CONFIG, gyro_range)
#         self._update_gyro_scale_modifier()


#    def read_gyro_range(self, raw = False):
#        """Reads the range the gyroscope is set to.

#         If raw is True, it will return the raw value from the GYRO_CONFIG
#         register.
#         If raw is False, it will return 0 for 250°, 1 for 500°, 2 for 1000°, 3 for 2000° or -1. If the
#         returned value is equal to -1 something went wrong.
#         """
#         raw_data = self.bus.read_byte_data(self.address, self.GYRO_CONFIG)
#         self._update_gyro_scale_modifier(raw_data)
# 
#         if raw is True:
#             return raw_data
#         elif raw is False:
#             if raw_data == self.GYRO_RANGE_250DEG:
#                 return 0 #250
#             elif raw_data == self.GYRO_RANGE_500DEG:
#                 return 1 #500
#             elif raw_data == self.GYRO_RANGE_1000DEG:
#                 return 2 #1000
#             elif raw_data == self.GYRO_RANGE_2000DEG:
#                 return 3 #2000
#             else:
#                 return -1

#    def get_gyro_data(self):
#        """Gets and returns the X, Y and Z values from the gyroscope.
#    
#        Returns the read values in a dictionary.
#        """
#       x = self._get_sensor_register(self.GYRO_XOUT0, self.current_gyro_scale_modifier)
#       y = self._get_sensor_register(self.GYRO_YOUT0, self.current_gyro_scale_modifier)
#       z = self._get_sensor_register(self.GYRO_ZOUT0, self.current_gyro_scale_modifier)

#        return {'x': x, 'y': y, 'z': z}

#    def get_all_data(self):
#        """Reads and returns all the available data."""
#        temp = self.get_temp()
#        accel = self.get_accel_data()
#        gyro = self.get_gyro_data()
#
#        return [accel, gyro, temp]
