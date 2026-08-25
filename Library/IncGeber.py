#Getestet bei 3,3 Volt
import RPi.GPIO as GPIO
#import time
from PyQt6.QtCore import QObject, pyqtSignal

class IncGeber(QObject):
    """ Der Incrementgeber sollte mit 3,3 V betrieben werden """
    incGeber_moved = pyqtSignal(bool)
    incGeber_pressed = pyqtSignal()
    
    def __init__(self, dt_pin=4, clk_pin=26, button_pin=6):
        """ Initialisiert den Incrementgeber.
            Mit den Argumenten dt_pin, clk_pin und button_pin können die verwendeten Hardware Pins des
            Raspberry pis angepasst werden. """
        super().__init__()
        self.DT_pin = dt_pin
        self.CLK_pin = clk_pin
        self.button = button_pin
        #The value which is set by the user
        #self.start_value = 0
    
    def _decode_value(self, clk, dt):
        """ Übersetzt die Eingabewerte in Dezimalzahlen (Hinweis: Es wird nicht das normale Binärsystem verwendet!)
            dec = bin
            0 = 10
            1 = 00
            2 = 01
            3 = 11 """
        if (clk == False) and (dt == False):
            return 1
        elif (clk == False) and (dt == True):
            return 2
        elif (clk == True) and (dt == False):
            return 0
        else:
            return 3
        
    def pin_changed(self, pin_changed):
        """ Die Methode wird aufgerufen wenn am Incrementgeber wurde.
            Sie bestimmt ob dieser nach links oder rechts gedreht wurde und ruft
            das pyqt Signal "incGeber_moved" mit true oder false ab (abhängig von der Drehrichtung) """
        clk = GPIO.input(self.CLK_pin)
        dt = GPIO.input(self.DT_pin)
        actual_value = self._decode_value(clk, dt)
        #Filter if two times the same value comes directly after each other
        if actual_value is not self.old_value:
            if (self.old_value == 0) and (actual_value == 3):
                self.incGeber_moved.emit(False)
            elif (self.old_value == 3) and (actual_value == 0):
                self.incGeber_moved.emit(True)
            elif self.old_value > actual_value:
                self.incGeber_moved.emit(False)
            else:
                self.incGeber_moved.emit(True)
            self.old_value = actual_value
            
    def button_action(self, pin):
        """ Die Methode wird aufgerufen, wenn der Incrementgeber gedrückt wird """
        self.incGeber_pressed.emit()

    def start_reading(self, set_pins_to_BCM=True):
        """ Es werden die Interrupts für die Input Pins des Incrementgebers initialisiert. """
        if set_pins_to_BCM == True:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.DT_pin, GPIO.IN) #DT
        GPIO.setup(self.CLK_pin, GPIO.IN) #CLK
        GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP) #SW

        self.old_value = self._decode_value(GPIO.input(self.CLK_pin), GPIO.input(self.DT_pin))
                
        GPIO.add_event_detect(self.DT_pin, GPIO.BOTH, callback=self.pin_changed)
        GPIO.add_event_detect(self.CLK_pin, GPIO.BOTH, callback=self.pin_changed)
        GPIO.add_event_detect(self.button, GPIO.FALLING, callback=self.button_action)
        
    def stop_reading(self):
        """ Die Interrupts für den Incrementgeber werden ausgeschaltet. """
        GPIO.remove_event_detect(self.DT_pin)
        GPIO.remove_event_detect(self.CLK_pin)
        GPIO.remove_event_detect(self.button)
            
