import pigpio
import time
import subprocess
import threading
import math

class Motor_Steuerung:
    actual_pwm = 0
    is_run_thread_adjust_accel = False 
    #Initialisierungen für die Hardware
    GPIO_PIN = 19
    GPIO_FREQUENCY = 200 #PWM Frequenz in Hz (Frequenzen über 30 MHz gehen wahrscheinlich nicht, laut Dokumentation von pigpio)
    duty_cicle = 0
    
    step_size = 20000 #Die größe mit der die Beschleunigung erhöht wird, um ein zu schnelles anfahren des Motors zu verhindern
    
    def __init__(self, config_Manager_motor, root_dir):
        """ Initialisiert die pigpio-Library, welche die PWM-Frequenz für den Motor via Hardware PWM setzen kann."""
        self.config_Manager_motor = config_Manager_motor
        
        self.pi = pigpio.pi()
        if not self.pi.connected:
            print("Versuche pigpio zu aktivieren")
            subprocess.call(["sh", f"{root_dir}/Library/enable_pigpio.sh"])
            time.sleep(2)
            self.pi = pigpio.pi()
            if not self.pi.connected:
                print("Kann nicht zu pigpio daemon verbinden, bitte installiere das entsprechende Programm nach.")
                exit()
            else:
                print("pigpio erfolgreich aktiviert")
        self.pi.hardware_PWM(self.GPIO_PIN, 0, 0) #Bei der Initialisierung soll der Motor immer aus sein
        
    def refresh_config(self):
        """ Hierdurch wird die Config für die Umrechnung von der Beschleunigungsvorgabe zur
            Beschleunigungsausgabe neu eingelesen."""
        self.a_147 = float(self.config_Manager_motor.read_value_from_xml_config("a_147"))
        self.b_147 = float(self.config_Manager_motor.read_value_from_xml_config("b_147"))
        self.c_147 = float(self.config_Manager_motor.read_value_from_xml_config("c_147"))
        self.rundung_147 = int(self.config_Manager_motor.read_value_from_xml_config("rundung_147"))
        self.offset_147 = float(self.config_Manager_motor.read_value_from_xml_config("offset_147"))
        
        self.a_98 = float(self.config_Manager_motor.read_value_from_xml_config("a_98"))
        self.b_98 = float(self.config_Manager_motor.read_value_from_xml_config("b_98"))
        self.c_98 = float(self.config_Manager_motor.read_value_from_xml_config("c_98"))
        self.rundung_98 = int(self.config_Manager_motor.read_value_from_xml_config("rundung_98"))
        self.offset_98 = float(self.config_Manager_motor.read_value_from_xml_config("offset_98"))
        
    def set_motor_new_accel(self, new_accel, max_Value, use_thread=True):
        """ Liest die Config neu ein und rechnet danach die vorgegebene Beschleunigung in die benötigte PWM-Frequenz um.
            Im Anschluss wird diese auf den Motor gegeben (mit einer langsamen Hochfahrkurve)"""
        self.refresh_config()
        self.set_motor_new_pwm(self._calculate_pwm(new_accel, max_Value))
            
    def set_motor_new_pwm(self, new_pwm, use_thread=True):
        """ Setzt die gewünschte PWM-Frequenz für den Motor (mit einer langsamen Hochfahrkurve)
            Zusätzlich kann definiert werden, ob das hoch/runterfahren des Motors auf einem externen Thread
            oder dem aktuellen Thread geschehen soll."""
        if self.is_run_thread_adjust_accel == True:
            #Stellt sicher das der Thread nicht mehr läuft, bevor ein neuer aufgerufen wird
            self.is_run_thread_adjust_accel = False           
            self.thread_adjust_accel.join()
        self.is_run_thread_adjust_accel = True
        
        if use_thread:
            self.thread_adjust_accel = threading.Thread(target=self._set_motor_new_pwm, args=[new_pwm])
            self.thread_adjust_accel.start()
        else:
            #Der Ausschaltvorgang sollte in einigen Fällen (z.B. zum Ausschalten auf dem Mainthread passieren
            self._set_motor_new_pwm(0)        
        
    def shutdown_motor(self):
        """ Schaltet den Motor aus und gibt die Ressourcen frei.
            Die Methode darf und muss nur aufgerufen werden, wenn das Programm geschlossen wird.
            Im normalen Programm muss stattdessen: set_motor_new_pwm(0) verwendet werden"""
        if self.pi is not None:
            self.set_motor_new_pwm(0, use_thread=False)
            self.pi.hardware_PWM(self.GPIO_PIN, 0, 0)
            self.pi.stop()
            self.pi = None
        else:
            print("Motor sollte bereits aus sein")
         
    def _calculate_pwm(self, x, max_Value=False):
        """ Berechnet für die vorgegebenen Beschleunigung die benötigte PWM-Frequenz. """
        if x > 0.05:
            if max_Value:
                #Es wird die Kurve für 1,5 g verwendet
                a=self.a_147
                b=self.b_147
                c=self.c_147
                rundungsfehler_korrektur=self.rundung_147
                x = x + self.offset_147
            else:
                #Es wird die Kurve für 1 g verwendet
                a=self.a_98
                b=self.b_98
                c=self.c_98
                rundungsfehler_korrektur=self.rundung_98
                x = x + self.offset_98

            unter_wurzel = b**2 + 4*a *(-c + x*rundungsfehler_korrektur)
            if(unter_wurzel >= 0) and (a != 0):
                x = (-b + math.sqrt(unter_wurzel))/(2*a)
            else:
                #Andernfalls würde man in einen mathematischen Fehler reinlaufen. 
                #Die 68027*14,7=1.000.000 (1.000.000 ist auch der Max. Wert für die Beschleunigung, 
                #für eine allgemeine Annäherung der Funktion ist es in kleineren Bereichen ok.
                x = x * 68027 
        else:
            x = 0
        return x
        
    def _set_motor_new_pwm(self, soll_pwm_value):
        """ Sorgt dafür, dass der Motor langsam hochfährt, um Beschädigungen zu vermeiden. Der Task blockiert den aktuellen Thread. """
        tmp_pwm = self.actual_pwm
        compare_value = 0
        while(self.is_run_thread_adjust_accel):
            if tmp_pwm > soll_pwm_value:
                tmp_pwm = tmp_pwm - self.step_size
                compare_value = tmp_pwm - soll_pwm_value
                
            elif tmp_pwm < soll_pwm_value:
                tmp_pwm = tmp_pwm + self.step_size
                compare_value = soll_pwm_value - tmp_pwm
                    
            if(compare_value <= 0.5):
                tmp_pwm = soll_pwm_value
                self.is_run_thread_adjust_accel = False
            
            time.sleep(0.1)
                
            self._set_accelaration(tmp_pwm)
            
    def _set_accelaration(self, pwm_value):
        """ Setzt die PWM-Wert für den Motor auf den Wert in pwm_value.
            Die Variable kann dabei Werte zwischen einschließlich 0 und 1 Million annehmen."""
        if self.pi is not None:
            try:
                if pwm_value < 0:
                    pwm_value = 0
                if pwm_value > 1000000:
                    pwm_value = 1000000
                self.actual_pwm = int(pwm_value)
                self.pi.hardware_PWM(self.GPIO_PIN, self.GPIO_FREQUENCY, self.actual_pwm)
                print("Der Motor beschleunigt jetzt mit {value}".format(value=self.actual_pwm))
            except Exception as e:
                print("Error. schalte Motor aus", e)
                self.shutdown_motor()
        
        
