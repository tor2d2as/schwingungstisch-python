import bluetooth
from PyQt6.QtCore import QObject, pyqtSignal, QCoreApplication
import threading
import subprocess
#Um den Raspberry Pi für andere Bluetoothgeräte sichtbar zu machen, muss das Command Line Tool: bluetoothctl installiert sein.

#Anpassen des Gerätenamens als "Schwingungstisch": sudo raspi-config nonint do_hostname Schwingungstisch

class Bluetooth_Module(QObject):
    update_connection_state = pyqtSignal(str, bool)
    received_data = pyqtSignal(str)
    
    receive_data = False
    has_connection = False
    
    #Variablen die für die Main_UI verwendet werden
    REQUEST_STATUS_UPDATE_MAIN = "request_status_update_main"
    TABLE_STATE = "table_state"
    OSZI_STATE = "oszi_state"
    UPDATE_SET_ACCEL = "update_set_accel"
    ACTUAL_ACCEL = "actual_accel"
    
    #Variablen die für die Einstellungen verwendet werden
    REQUEST_STATUS_UPDATE_SETTINGS = "request_status_update_settings"
    ACCEL_MEAS_AREA = "accel_meas_area"
    ACCEL_LOW_PASS = "accel_low_pass"
    ACCEL_SAMPLING_RATE = "accel_sampling_rate"
    ADJUST_OSZI_OUTPUT = "adjust_oszi_output"
    RESET_TABLE = "reset_table"
    #Die Einstellung INCREASE_ACCEL_RANGE darf nicht per Bluetooth aktiviert werden, die Variable wird daher nur zum Senden benötigt.
    INCREASE_ACCEL_RANGE = "increase_accel_range"
    
    def connect_bluetooth(self):
        """ Wartet bis die Handy App versucht eine Verbindung aufzubauen, die Verbindung wird
            automatisch aktiviert. Nach der erfolgreichen Verbindung wird auf einem externen Thread auf
            Nachrichten der Handy App gewartet """
        if self.has_connection is False:
            self.stop_discoverable() 
            # Initialize Bluetooth socket
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                        
            self.server_socket.bind(("", bluetooth.PORT_ANY))
            self.server_socket.listen(self.server_socket.getsockname()[1])
                                                
            self.update_connection_state.emit("Warte auf Verbindung...", False)
            QCoreApplication.processEvents()
            
            self.thread_wait_connection = threading.Thread(target=self._connect_bluetooth)
            self.thread_wait_connection.start()

    def _connect_bluetooth(self):
        """ Akzeptiert die Bluetooth Verbindung und beginnt die Daten von der Handy App zu empfangen
            desweiteren wird die UI geupdated, so dass der Nutzer bescheid weiß das die Verbindung steht """
        if self.has_connection is False:
            # Accept incoming connection
            self.client_socket, self.client_address = self.server_socket.accept()
            self.has_connection = True
            print(f"Verbunden zu: {self.client_address}")
            self.update_connection_state.emit(f"Verbunden zu: {self.client_address}", False)
       
            if self.receive_data is False:
                self.receive_data = True
                while(self.receive_data):
                    try:
                        # Receive data from the phone
                        data = self.client_socket.recv(1024)
                        if not data:
                            break
                        #print("Received:", data.decode())
                        self.received_data.emit(data.decode())
                    except Exception as e:
                        print(e)
                        self.stop_connection()
                
            
    def stop_connection(self, inform_phone=True):
        """ Informiert die Handy App das die Verbindung beendet werden soll, und beendet die Verbindung """
        if inform_phone:
            self.send_data_to_phone("StopConnection")        
        self.stop_receive_data()
        self.has_connection = False
        if hasattr(self, "server_socket"):
            try:
                self.server_socket.close()
            except Exception as e:
                print(e)
                
        if hasattr(self, "client_socket"):
            try:
                self.client_socket.close()
            except Exception as e:
                print(e)
        self.update_connection_state.emit("Verbindung beendet, Drücken zum Neuverbinden", True)
        
        
    def send_data_to_phone(self, text_to_send):
        """ Wenn die Handy App verbunden ist, sendet es den angegebenen text über Bluetooth an die Handy App.
            Wenn keine Verbindung besteht, passiert nichts."""
        if self.has_connection:
            try:
                self.client_socket.send(text_to_send)
            except:
                self.stop_connection(False)
            
            
    def stop_receive_data(self):
        """ Beendet das empfangen von Daten, nach dem ausführen der Methode kann noch ein weiterer Datensatz empfangen werden"""
        self.receive_data = False        

    def _run_terminal_command(self, command):
        """ Führt einen beliebigen Command im Terminal aus, der Output wird zurückgegeben """
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        #print(result.stdout)
        return result
    
    def make_discoverable(self):
        """ Aktiviert die Sichtbarkeit des Raspberry Pis für andere Geräte (Bluetooth) """
        result = self._run_terminal_command("bluetoothctl discoverable on").stdout
        #print(result)
        return ("succeeded" in result)
    
    def stop_discoverable(self):
        """ Deaktiviert die Sichtbarkeit des Raspberry Pis für andere Geräte (Bluetooth) """
        result = self._run_terminal_command("bluetoothctl discoverable off").stdout
        #print(result)
        return ("succeeded" in result)

