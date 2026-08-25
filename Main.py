import sys
import os
import json

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6 import QtGui, QtCore
from ConfigManager import ConfigManager

root_dir = os.path.dirname(__file__)
lib_path = os.path.join(root_dir, "Library")
if lib_path not in sys.path:
    sys.path.append(lib_path)
    
UI_path = os.path.join(root_dir, "UI")
if UI_path not in sys.path:
    sys.path.append(UI_path)
    
#---------------------------------------------------------------------------------------------
#Der Emulator ist dazu da, um den Code am Computer testen zu können, wenn nötig, auf dem Raspberry Pi ausklammern.
Emulator_path = os.path.join(root_dir, "Emulator")
if Emulator_path not in sys.path:
    sys.path.append(Emulator_path)
#---------------------------------------------------------------------------------------------

from Motor_Steuerung import Motor_Steuerung
from Mpu6050 import Mpu6050

from Variables_UI import Variables_UI
from Main_UI import Main_UI
from Bluetooth_UI import Bluetooth_UI
from Settings_UI import Settings_UI
from Shutdown_UI import Shutdown_UI
from Kalibrate_UI import Kalibrate_UI

from Bluetooth_Module import Bluetooth_Module

class Main(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        config_settings_file = root_dir + "/config.xml"
        config_motor_file = root_dir + "/Library/config_motor.xml"
        
        #Initialisiere die Config für die Einstellungen (erstelle eine, wenn noch nicht vorhanden).
        config_Manager_settings = ConfigManager(config_settings_file)
        #Wenn die Config noch nicht existiert, erstelle eine Standardversion
        if os.path.exists(config_settings_file):
            if os.path.getsize(config_settings_file) == 0:
                config_Manager_settings.reset_setting_config()
        else:
            config_Manager_settings.reset_setting_config()
            
        #Initialisiere die Config für den Motor (erstelle eine, wenn noch nicht vorhanden).
        config_Manager_motor = ConfigManager(config_motor_file)
        #Wenn die Config noch nicht existiert, erstelle eine Standardversion
        if os.path.exists(config_motor_file):
            if os.path.getsize(config_motor_file) == 0:
                config_Manager_motor.reset_motor_config()
        else:
            config_Manager_motor.reset_motor_config()
        
        self.bluetooth_module = Bluetooth_Module()
        self.bluetooth_module.received_data.connect(self.received_data)
        
        #Der Wert fit_oszi_out wird hier initialisiert, da er bereits bei der Initialisierung von Mpu6050 verwendet wird!
        if "True" == config_Manager_settings.read_value_from_xml_config("fit_oszi_out"):
            enable_fit_oszi_out = True  
        else:
            enable_fit_oszi_out = False
        
        self.mpu6050 = Mpu6050(0x68, self.bluetooth_module, enable_fit_oszi_out)
        
        #Initiere die Motor_Steuerung.
        motor_steuerung = Motor_Steuerung(config_Manager_motor, root_dir)
        
        #Initiere die UIs
        self.tabs = QTabWidget()
        #self.showMaximized()
        self.showFullScreen()
        
        self.tabs.tabBar().setStyleSheet("QTabBar::tab { height: 150px; font-size: 50px; }")
        
        self.main_UI = Main_UI(root_dir, self.bluetooth_module, self.mpu6050, motor_steuerung)
        self.bluetooth_UI = Bluetooth_UI(root_dir, self.bluetooth_module, self.tabs)
        self.settings_UI = Settings_UI(root_dir, self.bluetooth_module, self.mpu6050, self.main_UI, config_Manager_settings)
        self.shutdown_UI = Shutdown_UI(self, root_dir)
        self.kalibrate_UI = Kalibrate_UI(root_dir, config_Manager_motor, self.mpu6050, motor_steuerung, self.main_UI, self.settings_UI)
        
        #Erstelle die UI und initiiere das QTabWidget.--------------------------------------
        self.setWindowTitle("Schwingungstisch")
        self.setGeometry(100, 100, 1024, 600)
        
        self.tabs.setStyleSheet(f"background-color: {Variables_UI.color_background_dark}; color: {Variables_UI.color_text_dark};")
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        
        #self.tabs.setStyleSheet("QTabBar::tab { color: #AAAAAA}, background-color")
        self.tabs.addTab(self.main_UI.create_main_tab(), QtGui.QIcon(root_dir + '/pictures/Home.png'), " Home")
        self.tabs.addTab(self.settings_UI.create_setting_tab(), QtGui.QIcon(root_dir + '/pictures/Settings.png'), " Einstellungen")
        self.tabs.addTab(self.bluetooth_UI.create_bluetooth_tab(), QtGui.QIcon(root_dir + '/pictures/Bluetooth.png'), " Bluetooth")
        self.tabs.addTab(self.shutdown_UI.create_shutdown_tab(), QtGui.QIcon(root_dir + '/pictures/Ausschalten_Icon.png'), " Herunterfahren/Desktop öffnen")
        self.tabs.addTab(self.kalibrate_UI.create_kalibration_tab(), QtGui.QIcon(root_dir + '/pictures/Kalibration_Icon.png'), " Kalibrierung")
        
        self.tabs.setIconSize(QtCore.QSize(50, 50))
        
        self.tabs.currentChanged.connect(self.tab_changed)
        #tabs.setTabEnabled(0, False)
        #---------------------------------------------------
        self.setCentralWidget(self.tabs)
    
    def goodbye(self):
        """ Diese Methode wird aufgerufen, wenn die UI geschlossen wird. Diese stellt sicher, 
            dass der Motor stoppt und alle Ressourcen (z.B. GPIO-Ports) freigegeben werden."""
        print("Releasing resources...")
        self.main_UI.turn_off_table(shutdown_table=True)
        #Stop Reading detect device open
        self.main_UI.incGeber.stop_reading()
        #Stop Oszi Output
        print("Alles erledigt, Goodbye.")
        
    def tab_changed(self, id):
        """ Hier können Events registriert werden, wenn ein neues Tab aufgerufen wird. """
        print("Neues Tab geöffnet:", id)
        if (id == 1): #id: 1 = Einstellungsseite
            if self.kalibrate_UI.settings_UI_need_update:
                #Wenn die Einstellungen für den Beschleunigungssensor von der Kalibrate_UI geupdated werden,
                #kann nicht sichergestellt werden, dass die Settings_UI richtig geupdated wird. Daher werden in der
                #Kalibrate_UI nur die Config-Werte und die Einstellungen des Beschleunigungssensors aktualisiert,
                #deswegen wird die Settings_UI dann erst hier aktualisiert.
                self.kalibrate_UI.settings_UI_need_update = False
                self.settings_UI.update_UI()
            else:
                #Der Schalter switch_enable_higher_accel kann auch von der Main_UI aktualisiert werden,
                #die Settings_UI wird aber nicht zuverlässig aktualisiert. Daher wird diese hier aktualisiert.
                self.settings_UI.switch_enable_higher_accel.setChecked(self.mpu6050.enable_higher_max_accel)                
        
    def received_data(self, data):
        """ Hier werden die Daten, welche von der Handy App kommen ausgewertet und die entsprechenden Aktionen ausgeführt. """
        try:
            if "}{" in data:
                return
            print("received data from bluetooth: ", data)
            #Daten, die für die Main_UI bestimmt sind
            if data == self.bluetooth_module.REQUEST_STATUS_UPDATE_MAIN:
                self.tabs.setCurrentIndex(0)
                self.bluetooth_module.stop_discoverable()
                self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\",\"%s\":\"%s\",\"%s\":\"%s\"}" % (self.bluetooth_module.TABLE_STATE, self.main_UI.switch_enable_table.isChecked(),
                                                                                                            self.bluetooth_module.OSZI_STATE, self.main_UI.switch_enable_oszi.isChecked(),
                                                                                                            self.bluetooth_module.UPDATE_SET_ACCEL, self.main_UI.slider_accel_set.value()))
            elif self.bluetooth_module.TABLE_STATE in data:
                #Wenn der Schalter auf der UI verändert wird, dann wird automatisch die dazugehörige Aktion ausgeführt, so als ob der Nutzer diese gedrückt hätte.
                tmp = json.loads(data)[self.bluetooth_module.TABLE_STATE] == "true"
                
                self.main_UI.switch_enable_table.setChecked(tmp)
                self.main_UI.change_table_state(tmp)
                self.settings_UI.switch_enable_higher_accel.setChecked(self.mpu6050.enable_higher_max_accel)
                    
            elif self.bluetooth_module.OSZI_STATE in data:
                tmp = json.loads(data)[self.bluetooth_module.OSZI_STATE] == "true"
                
                self.main_UI.switch_enable_oszi.setChecked(tmp)
                self.main_UI.change_oszi_state(tmp)
                    
            elif self.bluetooth_module.UPDATE_SET_ACCEL in data:
                self.main_UI.slider_accel_set.setValue(int(json.loads(data)[self.bluetooth_module.UPDATE_SET_ACCEL]))
                
            #Daten, die für die Settings_UI bestimmt sind
            elif data == self.bluetooth_module.REQUEST_STATUS_UPDATE_SETTINGS:
                #self.tabs.setCurrentIndex(1)
                self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\",\"%s\":\"%s\",\"%s\":\"%s\",\"%s\":\"%s\"}" % (self.bluetooth_module.ACCEL_MEAS_AREA, self.settings_UI.combo_box_meas_area_accel.currentIndex(),
                                                                                                                          self.bluetooth_module.ACCEL_LOW_PASS, self.settings_UI.combo_box_lowpass.currentIndex(),
                                                                                                                          self.bluetooth_module.ACCEL_SAMPLING_RATE, self.settings_UI.slider_sampling_rate.value(),
                                                                                                                          self.bluetooth_module.ADJUST_OSZI_OUTPUT, self.settings_UI.switch_change_oszi_out.isChecked()))
            elif self.bluetooth_module.ACCEL_MEAS_AREA in data:
                tmp = int(json.loads(data)[self.bluetooth_module.ACCEL_MEAS_AREA])
                self.settings_UI.combo_box_meas_area_accel.setCurrentIndex(tmp)
            
            elif self.bluetooth_module.ACCEL_LOW_PASS in data:
                tmp = int(json.loads(data)[self.bluetooth_module.ACCEL_LOW_PASS])
                self.settings_UI.combo_box_lowpass.setCurrentIndex(tmp)
                
            elif self.bluetooth_module.ACCEL_SAMPLING_RATE in data:
                self.settings_UI.slider_sampling_rate.setValue(int(json.loads(data)[self.bluetooth_module.ACCEL_SAMPLING_RATE]))
                
            elif self.bluetooth_module.ADJUST_OSZI_OUTPUT in data:
                tmp = json.loads(data)[self.bluetooth_module.ADJUST_OSZI_OUTPUT] == "true"
                self.settings_UI.enable_fit_oszi(tmp)
                self.settings_UI.switch_change_oszi_out.setChecked(tmp)
                
            elif self.bluetooth_module.RESET_TABLE in data:
                self.settings_UI.reset_setting()
                
        except Exception as e:
            print(e)
            
         
app = QApplication(sys.argv)

window = Main()
window.show()
app.lastWindowClosed.connect(window.goodbye)

app.exec()
