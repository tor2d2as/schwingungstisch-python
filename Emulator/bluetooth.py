import time

""" Erlaubt eine Basic-Simulation der Bluetooth Verbindungen.
    Die meisten Funktionen existieren nur das es keinen Error gibt.
    Das Basic Verhalten wird hier nur vereinfacht abgebildet."""

PORT_ANY = 0

class RFCOMM():
    def placeholder():
        return

class BluetoothSocket(RFCOMM):
    
    def __init__(self, test):
        return
    
    def bind(anything, test):
        return
    
    def listen(test, argument):
        return
    
    def getsockname(hallo):
        """ Es wird das Objekt connection_objects zurückgegeben + der Hardgecodede String: name2"""
        return (connection_objects(), "name2")
    
    def accept(argument):
        """ Wartet eine Sekunde, bevor die Verbindung als erfolgreich akzeptiert wurde.
            Es wird das Objekt connection_objects zurückgegeben + der Hardgecodede String: name2"""
        time.sleep(1)
        return (connection_objects(), "name2")
    
    def close(self):
        print("Emulator: Serversocket geschlossen")
        return
    
class connection_objects():
    
    def close(self):
        return
    
    def recv(self, arg):
        return received_messages("Emulator: Simulated data")
        
class received_messages():
    
    def __init__(self, content):
        self.message = content
    
    def decode(self):
        """ Stürzt absichtlich ab, siehe Ausgabe in der Console.
            Ohne den Absturz würde es den Wert, der bei Initialisierung der Klasse gesetzt wurde, zurückgeben."""
        print("Emulator: Die Methode received_messages.decode() im simulierten Bluetooth-Module läuft absichtlich in einen Error, um eine Endless Loop zu vermeiden. Die Endless loop wurde im orginal Code verwendet, um direkt wieder auf neue Nachrichten von der Handy App zu warten, im Emulator nicht implementiert!")
        print(self.not_existing)
        return self.message
        

