import spidev

class MCP4921:
    """ Die Klasse regelt den Output vom MCP4921 und damit den Analogausgang für das Oszilloskop.
        Der MCP4921 liefert dabei ein 12 bit Outputsignal, was bei einer maximal Spannung von 3,3 V eine
        Auflösung von 0,8 mV liefert """
    spi = None 
    #DEBUG = False
    spi_max_speed = 4 * 1000000 # 4 MHz
    #V_Ref = 3300 # 3V3 in mV
    Resolution = 2**12 # 12 bits für den MCP4921
    CE = 0 # CE0 or CE1, select SPI device on bus
    #Die Variable settings erlaubt es auf dem MCP4921 E/P Einstellungen vorzunehmen.
    #Die Bedeutung der Ausgabewerte kann aus der Dokumentation des Chips auf Seite 18 entnommen werden: https://cdn-reichelt.de/documents/datenblatt/A200/MCP4921_MCP4922_MIC.pdf
    settings = 0b00110000
    
    def start(self):
        """ Initialisiert die Verbindung zum MPU4921 """
        self.spi = spidev.SpiDev()
        self.spi.open(0,self.CE)
        self.spi.max_speed_hz = self.spi_max_speed
        self.has_started = True
        
    def stop(self):
        """ Setzt den Oszilloskopoutput des Raspberry Pi's auf 0 und gibt die Ressourcen für den
            Oszilloskop Output frei. """
        if self.spi:
            self.setOutput(0, _call_comes_from_stop=True)
            self.spi.close()
            self.has_started = False 

    def setOutput(self, val, _call_comes_from_stop=False):
        """ Es setzt den Wert val (zwischen 0 und 4095) auf den Ausgang des MCP4921.
            Werte die größer als 4095 oder kleiner 0 sind, werden automatisch auf das Limit gekappt.
            Die Umrechnung des val Wert zur Ausgangsspannung geschieht direkt auf dem MCP4921
            _call_comes_from_stop = Nur true, wenn von der Stop Methode aufgerufen wird, ansonsten immer false"""
        try:
            #print("Start Oszi Output")
            if(val > 4095):
                val = 4095
            if(val < 0):
                val = 0
            
            binary_val = format(val, "012b")
                
            highByte = int(binary_val[:4], 2)
            lowByte = int(binary_val[4:], 2)
            
            highByte = (highByte & 0b00001111) | (self.settings & 0b11110000)
            
            #if DEBUG :
                #print("binary_val= ", binary_val)
                #print("Highbyte = {0:8b}".format(highByte))
                #print("Lowbyte =  {0:8b}".format(lowByte))
                #print(type(highByte))
            self.spi.xfer2([highByte, lowByte])
        except:
            #print("Error bei der Oszilloskopausgabe: ", e)
            if not _call_comes_from_stop:
                self.stop()
