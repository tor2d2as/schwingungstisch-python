from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

import threading

from UI_Elements import Create_Elements
from Variables_UI import Variables_UI

from UI_Elements import My_Switch
from UI_Elements import HorizontalStroke

class Settings_UI:
    
    def __init__(self, root_dir, bluetooth_module, mpu6050, main_UI, configManager):
        """ Initialisiert verschiedene Module, welche für die Settings UI benötigt werden
            root_dir = Das root Verzeichnis des Projekts """
        self.picture_path = root_dir + '/pictures/'
        self.config_file = root_dir + "/config.xml"
        self.bluetooth_module = bluetooth_module
        self.mpu6050 = mpu6050
        self.main_UI = main_UI
        
        self.create_Elements = Create_Elements()
        self.variables_UI = Variables_UI()
        
        self.configManager = configManager
        
        self.load_config_values()
        
        #Schreibe die Werte in die Register des MPU6050
        self.on_accel_range_change(self.actual_accel_meas_area, write_to_config=False)
        self.on_lowpass_change(self.actual_accel_low_pass, write_to_config=False)
        self._slider_set_sampling_rate_changed(self.actual_accel_sampling_rate, write_to_config=False, skip_check=True)
    
    #Methoden welche aufgerufen werden, wenn der Nutzer mit einem Element im Einstellungs-tab interagiert
    def on_accel_range_change(self, id, write_to_config=True):
        """ Wird aufgerufen wenn der Nutzer mit der combo_box_meas_area_accel interagiert
            Hier wird der Messbereich des Beschleunigungssensors (MPU6050) angepasst.
            Der Wert wird auch in der Config aktualisiert, sofern write_to_config auf True ist.
            Für den Wert write_to_config False anzugeben, macht z.B. Sinn wenn der Wert nur in die Register des MPU6050 geschrieben werden soll
            und von der Config ausgelesen wurde."""
        
        print("Accel range:", id)
        self.actual_accel_meas_area = id
        if write_to_config:
            self.configManager.write_single_value_to_xml("accel_meas_area", id)
            
        if(id == 0):
            self.mpu6050.set_accel_range(self.mpu6050.ACCEL_RANGE_2G)
        elif(id == 1):
            self.mpu6050.set_accel_range(self.mpu6050.ACCEL_RANGE_4G)
        elif(id == 2):
            self.mpu6050.set_accel_range(self.mpu6050.ACCEL_RANGE_8G)
        elif(id == 3):
            self.mpu6050.set_accel_range(self.mpu6050.ACCEL_RANGE_16G)
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.ACCEL_MEAS_AREA, id))
        
    def on_lowpass_change(self, id, write_to_config=True):
        """ Wird aufgerufen wenn der Nutzer mit der combo_box_lowpass interagiert
            Hier wird der Lowpass filter angepasst, den der Beschleunigungssensors (MPU6050) verwenden soll.
            Der Wert wird auch in der Config aktualisiert, sofern write_to_config auf True ist.
            Für den Wert write_to_config False anzugeben, macht z.B. Sinn wenn der Wert nur in die Register des MPU6050 geschrieben werden soll
            und von der Config ausgelesen wurde. """
        
        print("Accel Lowpass:", id)
        self.actual_accel_low_pass = id
        if write_to_config:
            self.configManager.write_single_value_to_xml("accel_low_pass", id)
            
        if(id == 0):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_256)
        elif(id == 1):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_188)
        elif(id == 2):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_98)
        elif(id == 3):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_42)
        elif(id == 4):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_20)
        elif(id == 5):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_10)
        elif(id == 6):
            self.mpu6050.set_filter_range(self.mpu6050.FILTER_BW_5)
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.ACCEL_LOW_PASS, id))
            
    def enable_fit_oszi(self, new_value):
        """ Definiert ob der Oszilloskop Output auf 1 g / 1,5 g oder den Messbereich angepasst werden soll """
        self.configManager.write_single_value_to_xml("fit_oszi_out", new_value)
        self.mpu6050.enable_fit_oszi_out = new_value
        self.mpu6050.change_adjust_oszi_out()
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.ADJUST_OSZI_OUTPUT, new_value))
            

    def slider_set_sampling_rate_changed(self, value):
        """ Wird aufgerufen wenn der Nutzer mit der slider_sampling_rate interagiert.
            Die UI wird sofort auf den neuen Wert gesetzt. Updates an den MPU6050
            und das speichern in der Config findet mit 0,3 Sekunden verzögerung statt.
            Diese Verzögerung ist als Filter implementiert, so das nur der finale Wert an die Config/MPU6050 gesendet wird.
            value = Die neue Abtastrate """
        #The user only wants to see the sampling rate (to better fit with the slider, the value will be inverted)
        value = 255 - value
        actual_sampling_rate = self.calculate_sampling_rate(value)
        self.textfield_sampling_rate.setText(self.variables_UI.text_sample_rate.format(actual_sampling_rate))
        self.textfield_sampling_rate.setAlignment(Qt.AlignmentFlag.AlignRight)
        #The MPU6050 needs the sample_rate_divider
        self.tmp_accel_sampling_rate = value
        threading.Timer(0.3, self._slider_set_sampling_rate_changed, args=[value]).start()
        
    def _slider_set_sampling_rate_changed(self, value_to_check, write_to_config=True, skip_check=False):
        """ Es sendet die neu eingestellte Abtastrate an den MPU6050 und die Handy App.
            Der Wert wird auch in der Config aktualisiert, sofern write_to_config auf True ist.
            Für den Wert write_to_config False anzugeben, macht z.B. Sinn wenn der Wert nur in die Register des MPU6050 geschrieben werden soll
            und von der Config ausgelesen wurde. """
        if skip_check or (value_to_check is self.tmp_accel_sampling_rate):
            self.actual_accel_sampling_rate = value_to_check
            self.mpu6050.set_sample_rate_divider(value_to_check)
            if write_to_config:
                self.configManager.write_single_value_to_xml("accel_sampling_rate", value_to_check)
            print("The new sampling rate is: ", value_to_check)
            self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.ACCEL_SAMPLING_RATE, 255 - value_to_check))
            
    #------------------------------------------------------------------
    def calculate_sampling_rate(self, value):
        """ Hier wird die aktuelle Abtastrate in die Einheit 1/s umgerechnet """
        return round(1000 / (1 + value), 1)
    
    def load_config_values(self):
        """ Hier werden alle Einstellungen aus der Config geladen und in die Variablen gespeichert.
            Es werden KEINE Einstellungen auf der UI geupdatet. """
        self.actual_accel_meas_area = int(self.configManager.read_value_from_xml_config("accel_meas_area")) # 0 to 3
        self.actual_accel_low_pass = int(self.configManager.read_value_from_xml_config("accel_low_pass")) # 0 to 6
        self.actual_accel_sampling_rate = int(self.configManager.read_value_from_xml_config("accel_sampling_rate")) # 0 to 255
        self.mpu6050.enable_higher_max_accel = False #This value will always be initialized with False and wont be handled by the config
        if "True" == self.configManager.read_value_from_xml_config("fit_oszi_out"):
            self.mpu6050.enable_fit_oszi_out = True  
        else:
            self.mpu6050.enable_fit_oszi_out = False
            
    def update_UI(self):
        """ Aktualisert alle Einstellungen der Settings_UI auf der Oberfäche, es wird direkt aus der Config gelesen. """
        self.load_config_values()
        #Setzt die Werte auf der UI (Was dasselbe Update der Befehle an der Hardware auslöst, so als wäre es direkt vom Nutzer geändert worden, mit ausnahme von MySwitch attributen)
        self.combo_box_meas_area_accel.setCurrentIndex(self.actual_accel_meas_area)
        
        self.combo_box_lowpass.setCurrentIndex(self.actual_accel_low_pass)
        
        self.slider_sampling_rate.setValue(255 - self.actual_accel_sampling_rate)
        self.textfield_sampling_rate.setText(self.variables_UI.text_sample_rate.format(self.calculate_sampling_rate(self.actual_accel_sampling_rate)))
        self.textfield_sampling_rate.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.switch_enable_higher_accel.setChecked(self.mpu6050.enable_higher_max_accel)
        self.main_UI.increase_accel_range(self.mpu6050.enable_higher_max_accel)
        
        self.switch_change_oszi_out.setChecked(self.mpu6050.enable_fit_oszi_out)
        self.enable_fit_oszi(self.mpu6050.enable_fit_oszi_out)
        
        
    def reset_setting(self):
        """ Es setzt alle Einstellungen auf den empfohlenen Wert zurück. Wenn der Tisch nicht schwingt, wird zudem
            der MPU6050 intern zurückgesetzt."""
        print("Das Gerät wird zurückgesetzt")
        if self.main_UI.actual_accel == 0:
            #Der MPU6050 soll nur resettet werden wenn der Tisch schwingt, dies soll eine Fehlkalibration verhindern
            self.mpu6050.reset_mpu6050()
            print("MPU6050 wurde resettet")
        else:
            print("MPU6050 wurde nicht resettet")
        self.configManager.reset_setting_config()
        self.update_UI()
        
        
            
    #Erstellt das Einstellungstab -------------------------------------------------------------------
    def create_setting_tab(self):
        """ Erstellt das Tab für die Settings UI """
        container_setting_page = QWidget()
        settings_main_layout = QVBoxLayout(container_setting_page)
        
        #Erstelle den Abschnitt für die Beschleunigungsmessung +++++++++++++++++++++++++++++++++++++++++++++++
        layout_accel_setting = QVBoxLayout()
        #Überschrift der Einstellungen für die Beschleunigungsmessung
        layout_accel_setting_1 = QHBoxLayout()
        layout_accel_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + "/Beschleunigung_Icon_Einstellung.png", 50))
        
        deco_textfield_settings_accel = self.create_Elements.create_text_field("Einstellungen des Beschleunigungssensors", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_setting_1.addWidget(deco_textfield_settings_accel, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_accel_setting.addLayout(layout_accel_setting_1)
        
        layout_accel_setting.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Einstellungen für den Messbereich des Beschleunigungssensors
        layout_accel_setting_2 = QHBoxLayout()
        
        deco_textfield_meas_area_accel = self.create_Elements.create_text_field("Messbereich des Beschleunigungssensors", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_setting_2.addWidget(deco_textfield_meas_area_accel, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.combo_box_meas_area_accel = QComboBox()
        self.combo_box_meas_area_accel.addItems(["2 g", "4 g", "8 g", "16 g"])
        self.combo_box_meas_area_accel.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        self.combo_box_meas_area_accel.setMinimumWidth(200)
        #self.combo_box_meas_area_accel.setMinimumHeight(40)
        self.combo_box_meas_area_accel.setFont(self.variables_UI.font)
        self.combo_box_meas_area_accel.setCurrentIndex(self.actual_accel_meas_area)
        self.combo_box_meas_area_accel.currentIndexChanged.connect(self.on_accel_range_change)
        layout_accel_setting_2.addWidget(self.combo_box_meas_area_accel, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_accel_setting.addLayout(layout_accel_setting_2)
        
        deco_textfield_desc_meas_area_accel = self.create_Elements.create_text_field("Hiermit kann der Messbereich des Beschleunigungssensors geändert werden.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_accel_setting.addWidget(deco_textfield_desc_meas_area_accel)
        
        #Einstellungen für den Tiefpassfilter des Beschleunigungssensors
        layout_accel_setting_3 = QHBoxLayout()
        
        deco_textfield_lowpass = self.create_Elements.create_text_field("Tiefpassfilter einstellen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_setting_3.addWidget(deco_textfield_lowpass, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.combo_box_lowpass = QComboBox()
        self.combo_box_lowpass.addItems(["260 Hz (0 ms)", "184 Hz (2 ms)", "94 Hz (3 ms)", "44 Hz (4,9 ms)", "21 Hz (8,5 ms)", "10 Hz (13,8 ms)", "5 Hz (19 ms)"])
        self.combo_box_lowpass.setMinimumWidth(200)
        #self.combo_box_lowpass.setMinimumHeight(70)
        self.combo_box_lowpass.setFont(self.variables_UI.font)
        self.combo_box_lowpass.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        self.combo_box_lowpass.setCurrentIndex(self.actual_accel_low_pass)
        self.combo_box_lowpass.currentIndexChanged.connect(self.on_lowpass_change)
        layout_accel_setting_3.addWidget(self.combo_box_lowpass, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_accel_setting.addLayout(layout_accel_setting_3)
        
        deco_textfield_lowpass_desc = self.create_Elements.create_text_field("Durch die Aktivierung des Tiefpassfilters wird die gemessene Beschleunigung über mehrere Werte gemittelt, "
                                                                    "wodurch das Signal weniger schwankt. Änderungen der Beschleunigung werden dafür langsamer erkannt.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_accel_setting.addWidget(deco_textfield_lowpass_desc)
        
        #Einstellungen für die Abtastrate
        layout_accel_setting_4 = QHBoxLayout()
        
        deco_lowpass_sampling_rate = self.create_Elements.create_text_field("Abtastrate", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_setting_4.addWidget(deco_lowpass_sampling_rate, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_sampling_rate = self.create_Elements.create_text_field(self.variables_UI.text_sample_rate.format(self.calculate_sampling_rate(self.actual_accel_sampling_rate)), self.variables_UI.font, 55, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        self.textfield_sampling_rate.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_accel_setting_4.addWidget(self.textfield_sampling_rate, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_accel_setting.addLayout(layout_accel_setting_4)
        
        layout_accel_setting_5 = QHBoxLayout()
        layout_accel_setting_5.addWidget(self.create_Elements.create_image(self.picture_path + '/Abtastrate_low.png', 80))
        
        self.slider_sampling_rate = self.create_Elements.create_slider(0, 255)
        self.slider_sampling_rate.setValue(255 - self.actual_accel_sampling_rate)
        self.slider_sampling_rate.valueChanged.connect(self.slider_set_sampling_rate_changed)
        layout_accel_setting_5.addWidget(self.slider_sampling_rate)
        
        layout_accel_setting_5.addWidget(self.create_Elements.create_image(self.picture_path + '/Abtastrate_hoch.png', 80))
        
        layout_accel_setting.addLayout(layout_accel_setting_5)
        
        deco_textfield_sampling_rate_desc = self.create_Elements.create_text_field("Hier kann eingestellt werden, wie oft die Beschleunigung pro Sekunde gemessen werden soll. Durch eine höhere "
                                                                    "Abtastrate werden mehr Werte pro Sekunde ausgelesen.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_accel_setting.addWidget(deco_textfield_sampling_rate_desc)
        
        #Erstelle den Abschnitt für die Ausgabeeinstellungen des Tisches +++++++++++++++++++++++++++++++++++++++++++++++
        layout_accel_set_setting = QVBoxLayout()
        #Überschrift für die Ausgabeeinstellungen
        layout_accel_set_setting_1 = QHBoxLayout()
        layout_accel_set_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Settings_Output_Icon.png', 50))
        
        deco_textfield_header_accel_settigs = self.create_Elements.create_text_field("Ausgabe Einstellungen des Tisches", self.variables_UI.font, 40, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_set_setting_1.addWidget(deco_textfield_header_accel_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_accel_set_setting.addLayout(layout_accel_set_setting_1)
        
        layout_accel_set_setting.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))       
        
        #Stellt die maximale Beschleunigung des Tisches ein
        layout_accel_set_setting_2 = QHBoxLayout()
        
        deco_textfield_increase_accel = self.create_Elements.create_text_field("Max. Beschleunigung auf 14,72 m/s\u00B2 (1,5 g) erhöhen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_accel_set_setting_2.addWidget(deco_textfield_increase_accel, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.switch_enable_higher_accel = My_Switch()
        self.switch_enable_higher_accel.from_My_Switch_changed.connect(self.main_UI.increase_accel_range)
        self.switch_enable_higher_accel.setChecked(self.mpu6050.enable_higher_max_accel) 
        
        layout_accel_set_setting_2.addWidget(self.switch_enable_higher_accel, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_accel_set_setting.addLayout(layout_accel_set_setting_2)
        
        deco_textfield_higher_accel_desc = self.create_Elements.create_text_field("Die Option ist beim Starten des Programms immer deaktiviert. Hiermit kann die maximale Beschleunigung des Tisches auf 14,72 m/s\u00B2 (1,5 g) erhöht werden. "
                                                                    "Es können dann nur noch leichte Objekte beschleunigt werden.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_accel_set_setting.addWidget(deco_textfield_higher_accel_desc)
        
        #Stellt den Output des MCP4921 ein (Soll es auf den gesamten Messbereich skalieren, oder nur auf 1 g / 1,5 g)
        layout_oszi_output_1_5 = QHBoxLayout()
        
        deco_textfield_set_oszi_out = self.create_Elements.create_text_field("Optimierung des Oszilloskop Output auf 1 g/1,5 g", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_oszi_output_1_5.addWidget(deco_textfield_set_oszi_out, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.switch_change_oszi_out = My_Switch()
        self.switch_change_oszi_out.from_My_Switch_changed.connect(self.enable_fit_oszi)
        self.switch_change_oszi_out.setChecked(self.mpu6050.enable_fit_oszi_out) 
        
        layout_oszi_output_1_5.addWidget(self.switch_change_oszi_out, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_accel_set_setting.addLayout(layout_oszi_output_1_5)
        
        deco_textfield_set_oszi_desc = self.create_Elements.create_text_field("Angeschaltet: Der Output des Oszilloskops wird auf 1 g / 1,5 g angepasst; " +
                                                                              "Ausgeschaltet: Der Output des Oszilloskops wird auf den eingestellten Messbereich des Beschleunigungssensors angepasst.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_accel_set_setting.addWidget(deco_textfield_set_oszi_desc)
        
        #Erstelle den Bereich für die Reset-Einstellungen +++++++++++++++++++++++++++++++++++++++++++++++
        layout_reset_setting = QVBoxLayout()
        #Überschrift Reset
        layout_reset_setting_1 = QHBoxLayout()
        layout_reset_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Reset_icon.png', 30))
        
        label_security_settigs = self.create_Elements.create_text_field("Reset", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_reset_setting_1.addWidget(label_security_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_reset_setting.addLayout(layout_reset_setting_1)
        
        layout_reset_setting.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Standardeinstellungen Widerherstellen
        layout_reset_setting_2 = QHBoxLayout()
        
        deco_textfield_reset_device = self.create_Elements.create_text_field("Standardeinstellungen wiederherstellen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_reset_setting_2.addWidget(deco_textfield_reset_device, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_reset_device = QPushButton()
        button_reset_device.setMinimumWidth(200)
        button_reset_device.setFont(self.variables_UI.font)
        button_reset_device.setText("Reset")
        button_reset_device.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_reset_device.clicked.connect(self.reset_setting)
        layout_reset_setting_2.addWidget(button_reset_device, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_reset_setting.addLayout(layout_reset_setting_2)
        
        deco_textfield_reset_desc = self.create_Elements.create_text_field("Hiermit können die empfohlenen Standardeinstellungen wiederhergestellt werden. Ebenso wird der Beschleunigungssensor (MPU6050), wenn die Beschleunigung 0 ist, intern zurückgesetzt.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_reset_setting.addWidget(deco_textfield_reset_desc)
        

        #Füge die Hintergrundfarben der einzelnen Layouts hinzu.
        settings_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_accel_setting, color=self.variables_UI.color_background_light))
        settings_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_accel_set_setting, color=self.variables_UI.color_background_light))
        settings_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_reset_setting, color=self.variables_UI.color_background_light))

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(".QScrollBar {width: 50px;}")
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_setting_page)
        
        return scroll_area
