#import threading
from collections import deque
from statistics import mean
import heapq
#import matplotlib.pylab as plt
import numpy as np
import time
#import math
from PyQt6.QtCore import QObject, pyqtSignal

class Kalibration(QObject):
    
    kalibration_finished = pyqtSignal(str)
    
    def __init__(self, config_Manager_motor, mpu6050, motor_steuerung):
        super().__init__()
        self.config_Manager_motor = config_Manager_motor
        self.mpu6050 = mpu6050
        self.motor_steuerung = motor_steuerung
        
    def start_kalibration(self,start_value=50000, step_size = 25000, end_value=1000000, max_kalibrierung=False, max_werte=2000, anzahl_hoechste=30):
        """ Startet die Kalibration des Tisches und schaltet ihn nach der Kalibration wieder aus.
            Dazu wird der Tisch mit den Schritten in step_size immer schneller
            und es wird die dortige Beschleunigung gemessen. Danach wird eine Kalibrationskurve (c+b*x+a*x^2) der Messwerte berechnet.
            Die Messwerte a, b, c werden in die Config gespeichert. Zusätzlich wird ein rundungsfehler_korrektur mit abgespeichert, dieser wird verwendet
            damit die Werte a, b, c nicht zu klein (z.B. e-11) werden. Der Wert ist derzeit konstant mit 1000 festgelegt.
            start_value = Der Wert bei dem die Kalibration startet (PWM-Frequenz)
            step_size = In welchen Abschnitten gemessen werden soll (PWM-Frequenz)
            end_value = Bis zu welcher PWM-Frequenz max. erhöht werden soll, im Falle das der MPU6050 einen Defekt hat (Deaktivert = 1.000.000)
            max_kalibrierung = False: Es wird bis 1 g kalibriert; True = Es wird bis 1,5 g kalibriert
            max_werte = Wie viele Messwerte pro Schritt gesammelt werden
            anzahl_hoechste = Von den gesammelten Messwerte pro Schritt wird der mean für die höchste n Werte genommen, wobei n = anzahl_hoechste ist."""
        self.tmp_data = deque(maxlen=max_werte)
        
        if max_kalibrierung:
            max_accel = 14.7
            max_accel_text = "1,5 g"
        else:
            max_accel = 9.8
            max_accel_text = "1 g"
            
        self.kalibration_finished.emit(f"Kalibrierung für {max_accel_text} läuft...")
        
        rundungsfehler_korrektur = 1000 #Die ermittelten Werte für die Formel sind teils sehr klein (z.B. 10^-11), damit diese größer werden, wird dieser Faktor verwendet
        
        measurement_values = dict()
        counter = start_value
        print("starte Kalibrierung")
        
        out = 0
        while((counter < end_value) and (out < max_accel)):
            #self.collect_data = True
            self.motor_steuerung._set_accelaration(counter)
            
            time.sleep(0.1)
            
            if not self._collect_measurement(max_werte):
                self.kalibration_finished.emit("Fehler MPU6050, abgebrochen!")
                self.motor_steuerung.set_motor_new_pwm(0, use_thread=False) #Die Kalibrierung läuft sowieso auf einem eigenen Thread, einen weiteren Thread zu nutzen macht keinen Sinn
                return
            
            #print(self.tmp_data)
            out = self.mpu6050.calculate_accel_for_ui(mean(heapq.nlargest(anzahl_hoechste, self.tmp_data)))
            measurement_values.update({counter : out * rundungsfehler_korrektur})
            print("Messwert, PWM:", counter, "Beschleunigung:", out)
            counter = counter + step_size
            self.tmp_data.clear()
            
        print("Kalibrierung beendet")
        #lists = sorted(measurement_values.items()) # sorted by key, return a list of tuples
        #sort_x, sort_y = zip(*lists) # unpack a list of pairs into two tuples
        
        x = list(measurement_values.keys())
        y = list(measurement_values.values())
        
        #Berechne die Polynom Funktion 2ter Ordnung
        coefficients = np.polyfit(x, y, 2)
        #x_fit = np.linspace(x[0], x[-1], 30)
        
        #polynomial = np.poly1d(coefficients)
        #y_fit = polynomial(x_fit)
        
        a = coefficients[0]
        b = coefficients[1]
        c = coefficients[2]
        
        print("Formel: (", c, "+", b, "* x +", a, "* x^2)/", rundungsfehler_korrektur)
        
        #print("Vorgabe für den Motor, für eine Beschleunigung von 3:")
        #print("variante 1:", (-b + math.sqrt(b**2 + 4*a *(-c + 3*rundungsfehler_korrektur)))/(2*a)) #Das ist die gesuchte Formel
        #print("variante 2:", -(math.sqrt(-4*a*c + 4*a*3 + b**2) + b)/(2*a)) #Zweite Lösung für die Formel (hier nicht sinnvoll)
        #-------------
        #print(f"Formel: x=(-{b} + math.sqrt({b}**2 + 4*{a} *(-{c} + x*{rundungsfehler_korrektur})))/(2*{a})")
        
        print("Werte zum kopieren:")
        print(f"a={a}")
        print(f"b={b}")
        print(f"c={c}")
        print(f"rundungsfehler_korrektur={rundungsfehler_korrektur}")
        
        if (a != 0) and (b != 0) and (c != 0):
            if max_kalibrierung:
                #Speichert die Werte wenn bis 1,5 g kalibriert wurde
                self.config_Manager_motor.write_single_value_to_xml("a_147",a)
                self.config_Manager_motor.write_single_value_to_xml("b_147",b)
                self.config_Manager_motor.write_single_value_to_xml("c_147",c)
                self.config_Manager_motor.write_single_value_to_xml("rundung_147",rundungsfehler_korrektur)
            else:
                #Speichert die Werte wenn bis 1 g kalibriert wurde
                self.config_Manager_motor.write_single_value_to_xml("a_98",a)
                self.config_Manager_motor.write_single_value_to_xml("b_98",b)
                self.config_Manager_motor.write_single_value_to_xml("c_98",c)
                self.config_Manager_motor.write_single_value_to_xml("rundung_98",rundungsfehler_korrektur)
        
        self.kalibration_finished.emit(f"Kalibrierung {max_accel_text} beendet, fahre herunter.")
        self.motor_steuerung.set_motor_new_pwm(0, use_thread=False) #Die Kalibrierung läuft sowieso auf einem eigenen Thread, einen weiteren Thread zu nutzen macht keinen Sinn
        self.kalibration_finished.emit(f"Für {max_accel_text} beendet, neue Kalibrierung?")
        
        #Plotte das Ergebnis
        #plt.plot(x_fit,y_fit, label="gefitted", color='red')
        #plt.plot(x, y, 'bo', label="values", color='green')
        #plt.legend()
        #plt.grid()
        #plt.show()
            
    def _collect_measurement(self, anzahl_werte):
        """ Sammelt die angegebene Anzahl an Messwerten und speichert diese in self.tmp_data ab."""
        i = 0
        abbruch = 0
        while(i <= anzahl_werte):
            try:
                self.tmp_data.append(abs(self.mpu6050.read_i2c_word(self.mpu6050.periodic_output_register)))
                i = i + 1
                abbruch = 0
            except Exception as e:
                print(e)
                abbruch = abbruch + 1
                if abbruch == 20:
                    return False
        return True
