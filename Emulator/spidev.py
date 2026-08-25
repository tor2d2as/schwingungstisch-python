class SpiDev:
    
    max_speed_hz = 0
    
    def xfer2(self, val):
        """ Berechnet den Wert der an den MCP4921 gesendet wird und gibt diesen in der Console aus."""
        highbyte = format(val[0] & 0b00001111, "004b")
        lowbyte = format(val[1], "004b")
        print("Emulator, Oszi-Out:", int(highbyte + lowbyte, 2))
    
    def open(self, value, port):
        """ Simuliert das öffnen des Ports zum MCP4921
            Wobei hier einfach nur die angegebenen Werte zwischengespeichert werden."""
        self.value = value
        self.port = port
        return
    
    def close(self):
        """ Gibt aus das die Verbindung zum MCP4921 geschlossen wurde. Device und Portnummer
            wurden in der Methode open() zwischengespeichert."""
        print("Emulator: Schließe spi-Verbindung zu dem Device: ", self.value, "auf Port: ", self.port)
