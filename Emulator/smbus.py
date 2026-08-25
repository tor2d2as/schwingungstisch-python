import random
import exchange_variables
import numpy as np
import time

def SMBus(bus):
    ret_val = Bus()
    ret_val.set_bus(bus)
    return ret_val


class Bus:
    #Simulierte Register
    ACCEL_XOUT0 = 0x3B #plus das nächste
    ACCEL_YOUT0 = 0x3D #plus das nächste
    ACCEL_ZOUT0 = 0x3F #plus das nächste
    
    MPU_CONFIG = 0x1A
    ACCEL_CONFIG = 0x1C
    SMPRT_DIV = 0x19 #Sample Rate Divider
    
    PWR_MGMT_1 = 0x6B 
    
    SIGNAL_PATH_RESET = 0x68
    
    #Werte für die Register
    val_MPU_CONFIG = 0x00
    val_ACCEL_CONFIG = 0x00
    val_SMPRT_DIV = 0x00
    val_SIGNAL_PATH_RESET = 0x00
    val_PWR_MGMT_1 = 0x00
    
    #Die Periode mit der der Simulierte Tisch schwingen soll
    sinus_period = np.pi/10
    
    #Anpassung des Beschleunigungssensors an die Messbereiche
    messbereich_anpassung = 1 #2g = 1; 4g = 2; 8g = 4; 24g = 8 

    def set_bus(self, bus):
        """ Initialisert die Bus-Klasse """
        exchange_variables.init()
        self.bus = bus

    def write_byte_data(self, I2C_address, register, bits):
        """ Speichert den angegebenen Wert in einer Variable (jeweils für das angegebene Register) und gibt eine Bestätigung als Text aus.
            Wenn ein Register noch nicht implementiert wurde, wird eine entsprechende Nachricht ausgegeben."""
        print("Emulator: I2C: schreibe auf Register:", hex(register), "den Wert:", bin(bits))
        if (register == self.MPU_CONFIG):
            self.val_MPU_CONFIG = bits
            
        elif (register == self.ACCEL_CONFIG):
            self.val_ACCEL_CONFIG = bits
            if(bits == 0):
                self.messbereich_anpassung = 1 #2g
            elif(bits == 8):
                self.messbereich_anpassung = 2 #4g
            elif(bits == 16):
                self.messbereich_anpassung = 4 #8g
            elif(bits == 24):
                self.messbereich_anpassung = 8 #16g
            
        elif (register == self.SMPRT_DIV):
            self.val_SMPRT_DIV = bits
        
        elif (register == self.SIGNAL_PATH_RESET):
            self.val_SIGNAL_PATH_RESET = bits
            
        elif (register == self.PWR_MGMT_1):
            self.val_PWR_MGMT_1 = bits
            
        else:
            print("Emulator, das Register:", hex(register), " wurde noch nicht für den I2C-Port (schreibend) implementiert.")
    
    def read_byte_data(self, I2C_address, register):
        """ Erlaubt das auslesen der simulierten Register, inkl. eines simulierten Beschleunigungswertes.
            Dieser kann durch das setzen des internen Booleans: use_noise mit oder ohne noise ausgegeben werden.
            Der Beschleunigungswert wird von dem simulierten Motor Output über die globale Variable: exchange_variables.motor_output in m/s^2 eingelesen.
            Wenn ein Register nicht implementiert ist, wird eine Nachricht in die Console ausgegeben."""
        #print("Emulator:", read_address, register)
        if ((register == self.ACCEL_XOUT0) or (register == self.ACCEL_YOUT0) or (register == self.ACCEL_ZOUT0)):
            
            #time.sleep(random.randint(0,100)/100000)
            
            # Simuliert einen Auslesefehler des Sensors, dies kann genutzt werden, um zu prüfen, wie das System im Fehlerfall reagiert.
            # Dies ist vor allem bei der automatischen Kalibrierung wichtig, damit der Motor nicht versehentlich über
            # die 1,5 g zu lange beschleunigt.
            # Der Fehler tritt in der Praxis normalerweise nicht auf, war aber beim initialen Aufbau der Hardware temporär relevant.
            use_error = False 
            if use_error:
                error = random.randrange(0,10,1)
                if(error < 4):
                    raise Exception("Emulator: Einlesen von MPU6050 Fehlgeschlagen (Diese Exception kann im smbus deaktiviert werden).")
            
            # In der Praxis misst der Beschleunigungssensor nicht immer den exakten Wert, dies wird hier versucht abzubilden.
            # Bei den hier angegebenen Werten handelt es sich um Schätzwerte.
            use_noise = True      
            if use_noise:
                value = exchange_variables.motor_output * np.sin(self.sinus_period*(int(time.time()*1000)))
                noise = random.randrange(-15,15,1)/100
                tmp = (value+noise)*1670
            else:
                tmp = exchange_variables.motor_output*1670
                
            tmp = tmp / self.messbereich_anpassung
                            
            self.binary_val = format(int(tmp), "016b")
            #Hier wird der erste Teil des simulierten Beschleunigungswerts zurückgegeben.
            #In dem nachfolgenden, simulierten Register wird der zweite Teil zurückgegeben. 
            # (Ein Register kann hier maximal 8 Bit haben, wir haben aber einen 16 Bit Ausgabewert).
            return int(self.binary_val[:8], 2)
        elif ((register == self.ACCEL_XOUT0+1) or (register == self.ACCEL_YOUT0+1) or (register == self.ACCEL_ZOUT0+1)):
            #Gibt den zweiten Teil des simulierten Beschleunigungswerts zurück.
            return int(self.binary_val[8:], 2) 
            
        elif (register == self.MPU_CONFIG):
            print("Emulator, das Register:", hex(register), " wurde mit dem Wert:", bin(self.val_MPU_CONFIG),"ausgelesen.")
            return self.val_MPU_CONFIG
        
        elif (register == self.ACCEL_CONFIG):
            print("Emulator, das Register:", hex(register), " wurde mit dem Wert:", bin(self.val_ACCEL_CONFIG),"ausgelesen.")
            return self.val_ACCEL_CONFIG

        elif (register == self.SMPRT_DIV):
            print("Emulator, das Register:", hex(register), " wurde mit dem Wert:", bin(self.val_SMPRT_DIV),"ausgelesen.")
            return self.val_SMPRT_DIV
        
        elif (register == self.SIGNAL_PATH_RESET):
            print("Emulator, das Register:", hex(register), " wurde mit dem Wert:", bin(self.val_SIGNAL_PATH_RESET),"ausgelesen.")
            return self.val_SIGNAL_PATH_RESET
        
        else:
            print("Emulator, das Register:", hex(register), " wurde noch nicht für den I2C-Port (lesend) implementiert.")
