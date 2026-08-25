import exchange_variables

class pi:
    connected = True
    
    def hardware_PWM(self, GPIO_pin, GPIO_Frequency, Soll_beschleunigung):
        """ Simuliert das Verhalten der PWM-Frequenz und die quadratische Übersetzung des Motors zur Beschleunigung.
            Es wird der Wert in m/s^2 in der Console ausgegeben. Ebenso wird der Wert in der
            globalen Variable: exchange_variables.motor_output gespeichert damit dieser vom simulierten Beschleunigungssensor
            eingelesen werden kann."""
        if (Soll_beschleunigung == 0):
            print("Emulator: Der Motor ist jetzt aus")
        #Simulation der PWM-Frequenz umrechnung (nur ungefähr, aber völlig ausreichend)
        Soll_beschleunigung = Soll_beschleunigung/68027
        
        #Simuliert die quadratische Umrechnung des Motors
        exchange_variables.motor_output = 0.293*Soll_beschleunigung+0.0765*Soll_beschleunigung**2 #Die Vorgabe stimmt ca. bis 1 g mit dem realen Motor überein
        #exchange_variables.motor_output = 0.1*Soll_beschleunigung+0.9*Soll_beschleunigung**2
        
        print("Emulator: Der simulierte Motor Beschleunigt jetzt mit: ", exchange_variables.motor_output)
        
    def stop(self):
        return
