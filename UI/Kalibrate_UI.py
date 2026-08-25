from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

import threading

from Kalibration import Kalibration

from UI_Elements import Create_Elements
from Variables_UI import Variables_UI
from UI_Elements import My_Switch
from UI_Elements import HorizontalStroke

class Kalibrate_UI:
    
    startwert = 50000
    stepsize = 20000
    endwert = 1000000
    max_kalibrierung = False
    #Die Variablen linear_offset_1g und linear_offset_15g werden in der init Methode gesetzt
    DIVIDER = 10 #Teilt den linear_offset_1g und den linear_offset_15g, so das diese auf der UI korrekt angezeigt wird (Im Hintergrund wird mit Integern gearbeitet.)
    settings_UI_need_update = False
    
    def __init__(self, root_dir, config_Manager_motor, mpu6050, motor_steuerung, main_UI, settings_UI):
        self.settings_UI = settings_UI
        self.main_UI = main_UI
        self.motor_steuerung = motor_steuerung
        self.config_Manager_motor = config_Manager_motor
        self.kalibration = Kalibration(config_Manager_motor, mpu6050, motor_steuerung)
        self.kalibration.kalibration_finished.connect(self.set_text_button_start_kalibrate)
        
        self.picture_path = root_dir + '/pictures/'
        
        self.create_Elements = Create_Elements()
        self.variables_UI = Variables_UI()
        
        self.linear_offset_1g = float(self.config_Manager_motor.read_value_from_xml_config("offset_98"))
        self.linear_offset_15g = float(self.config_Manager_motor.read_value_from_xml_config("offset_147"))
        
    def set_accelaration_sensor(self):
        """ Setzt die Einstellungen des Beschleunigungssensors auf die idealen Werte und aktualisiert die Config für die Einstellungen des Beschleunigungssensors. """
        self.settings_UI_need_update = True
        self.settings_UI.on_accel_range_change(0)
        self.settings_UI.on_lowpass_change(5)
        self.settings_UI._slider_set_sampling_rate_changed(0, skip_check=True)
        
    def slider_startwert_changed(self, value):
        """ Hier wird der Startwert für die Messkurve festgelegt, ebenfalls wird der Wert auf der UI geändert.
            Damit der Nutzer diese festlegen einfach festlegen kann, wird auch der Motor mit einer Verzögerung von 0,3 sec. angestellt
            (Damit einzelne Zwischenwerte beim Bewegen des Sliders nicht übernommen werden, sondern nur der Endwert)."""
        self.textfield_startwert.setText(str(value))
        self.startwert = value
        self.textfield_startwert.setAlignment(Qt.AlignmentFlag.AlignRight)
        threading.Timer(0.3, self._set_startwert_accel, args=[self.startwert]).start()
        
    def _set_startwert_accel(self, value):
        """ Gibt die eingestellte Startwert Beschleunigung auf den Motor."""
        if(value is self.startwert):
            self.motor_steuerung.set_motor_new_pwm(self.startwert)
    
    def slider_stepsize_changed(self, value):
        """ Aktualisiert den Wert für die Schrittgröße auf der UI. """
        self.textfield_stepsize.setText(str(value))
        self.stepsize = value
        self.textfield_stepsize.setAlignment(Qt.AlignmentFlag.AlignRight)
        return
    
   # def slider_endwert_changed(self, value):
   #     """ Aktualisiert den Wert für den Endwert auf der UI. """
   #     self.textfield_endwert.setText(str(value))
   #     self.endwert = value
   #     self.textfield_endwert.setAlignment(Qt.AlignmentFlag.AlignRight)
   #     return
    
    def from_switch_max_kalibrierung(self, value):
        """ Erlaubt dem Nutzer, zu wählen, ob er die Kurve für 1 g oder 1,5 g kalibrieren möchte. """
        self.max_kalibrierung = value
        
    def start_kalibrate(self):
        """Startet die Kalibrierung auf einem externen Thread """
        if self.max_kalibrierung:
            self.slider_linear_offset_15g.setValue(0)
        else:
            self.slider_linear_offset_1g.setValue(0)
        threading.Thread(target=self.kalibration.start_kalibration, args=[self.startwert, self.stepsize, self.endwert, self.max_kalibrierung]).start()
                
    def set_text_button_start_kalibrate(self, text):
        self.button_start_kalibrate.setText(text)
        
    def slider_linear_offset_1g_changed(self, value):
        """ Aktualisiert den Wert für den Offset für die Kurve bis zu 1 g auf der UI.
            Sobald der Wert ausgewählt ist, wird dieser mit einer Verzögerung von 0,3 sec. in die Config geschrieben."""
        self.linear_offset_1g = value/self.DIVIDER
        self.textfield_linear_offset_1g.setText(self.variables_UI.text_accel.format(self.linear_offset_1g))
        self.textfield_linear_offset_1g.setAlignment(Qt.AlignmentFlag.AlignRight)
        threading.Timer(0.3, self._slider_linear_offset_1g_changed, args=[self.linear_offset_1g]).start()
        
    def _slider_linear_offset_1g_changed(self, value):
        """ Aktualisiert den Offset Wert für die Kurve bis zu 1 g in der Config. """
        if(value is self.linear_offset_1g):
            self.config_Manager_motor.write_single_value_to_xml("offset_98", value)
    
    def slider_linear_offset_15g_changed(self, value):
        """ Aktualisiert den Wert für den Offset für die Kurve bis zu 1,5 g auf der UI.
            Sobald der Wert ausgewählt ist, wird dieser mit einer Verzögerung von 0,3 sec. in die Config geschrieben."""
        self.linear_offset_15g = value/self.DIVIDER
        self.textfield_linear_offset_15g.setText(self.variables_UI.text_accel.format(self.linear_offset_15g))
        self.textfield_linear_offset_15g.setAlignment(Qt.AlignmentFlag.AlignRight)
        threading.Timer(0.3, self._slider_linear_offset_15g_changed, args=[self.linear_offset_15g]).start()
        
    def _slider_linear_offset_15g_changed(self, value):
        """ Aktualisiert den Offset Wert für die Kurve bis zu 1,5 g in der Config. """
        if(value is self.linear_offset_15g):
            self.config_Manager_motor.write_single_value_to_xml("offset_147", value)
        
    def create_kalibration_tab(self):
        #Create Tab: Kalibrierungs Seite -------------------------
        container_kalibrate_page = QWidget()
        kalibrate_main_layout = QVBoxLayout(container_kalibrate_page)
        
        #Create Reset Setting +++++++++++++++++++++++++++++++++++++++++++++++
        layout_vorbereitung = QVBoxLayout()
        #Header Vorbreitung
        layout_vorbereitung_1 = QHBoxLayout()
        layout_vorbereitung_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Vorbereitung_Icon.png', 30))
        
        label_vorbereitung = self.create_Elements.create_text_field("Vorbereitungen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_vorbereitung_1.addWidget(label_vorbereitung, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_vorbereitung.addLayout(layout_vorbereitung_1)
        
        layout_vorbereitung.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Tisch Ausschalten
        layout_vorbereitung_2 = QHBoxLayout()
        
        deco_textfield_table_off = self.create_Elements.create_text_field("Tisch ausschalten", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_vorbereitung_2.addWidget(deco_textfield_table_off, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_table_off = QPushButton()
        button_table_off.setMinimumWidth(200)
        button_table_off.setFont(self.variables_UI.font)
        button_table_off.setText("Tisch ausschalten")
        button_table_off.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_table_off.clicked.connect(self.main_UI.turn_off_table)
        layout_vorbereitung_2.addWidget(button_table_off, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_vorbereitung.addLayout(layout_vorbereitung_2)
        
        deco_textfield_table_off_desc = self.create_Elements.create_text_field("Bevor mit der Kalibration begonnen werden kann, muss der Tisch ausgeschaltet werden und der Motor still stehen.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_vorbereitung.addWidget(deco_textfield_table_off_desc)
        
        #Sensor Einstellen
        layout_vorbereitung_3 = QHBoxLayout()
        
        deco_textfield_table_off = self.create_Elements.create_text_field("Sensor einstellen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_vorbereitung_3.addWidget(deco_textfield_table_off, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_reset = QPushButton()
        button_reset.setMinimumWidth(200)
        button_reset.setFont(self.variables_UI.font)
        button_reset.setText("Sensor einstellen")
        button_reset.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_reset.clicked.connect(self.set_accelaration_sensor)
        layout_vorbereitung_3.addWidget(button_reset, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_vorbereitung.addLayout(layout_vorbereitung_3)
        
        deco_textfield_table_off_desc = self.create_Elements.create_text_field("Setzt die Einstellungen auf Default. Wenn andere Sensoreinstellungen gewünscht sind, diese in den Einstellungen auswählen und den Schritt überspringen.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_vorbereitung.addWidget(deco_textfield_table_off_desc)
        
        #-----------------------------------------------------------------
        layout_start_end_kalibration = QVBoxLayout()
        #Header Kalibrierungseinstellungen
        layout_start_end_kalibration_0 = QHBoxLayout()
        layout_start_end_kalibration_0.addWidget(self.create_Elements.create_image(self.picture_path + '/Kalibrierung_Setting_Icon.png', 30))
        
        label_einstellung_kalibrierung = self.create_Elements.create_text_field("Einstellung Kalibrierung", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_start_end_kalibration_0.addWidget(label_einstellung_kalibrierung, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_start_end_kalibration.addLayout(layout_start_end_kalibration_0)
        
        layout_start_end_kalibration.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        #Startwert anpassen ---------------------------------------------
        layout_kalibrate_1 = QHBoxLayout()
        
        deco_startwert = self.create_Elements.create_text_field("Startwert (Bitte nicht voll aufdrehen!)", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_1.addWidget(deco_startwert, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_startwert = self.create_Elements.create_text_field(f"{self.startwert}", self.variables_UI.font, 175, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        self.textfield_startwert.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_kalibrate_1.addWidget(self.textfield_startwert, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_start_end_kalibration.addLayout(layout_kalibrate_1)
        
        layout_kalibrate_2 = QHBoxLayout()
        layout_kalibrate_2.addWidget(self.create_Elements.create_image(self.picture_path + '/Startwert_Klein.png', 80))
        
        slider_startwert = self.create_Elements.create_slider(0, 1000000)
        slider_startwert.setValue(self.startwert)
        slider_startwert.valueChanged.connect(self.slider_startwert_changed)
        layout_kalibrate_2.addWidget(slider_startwert)
        
        layout_kalibrate_2.addWidget(self.create_Elements.create_image(self.picture_path + '/Startwert_gross.png', 80))
        
        layout_start_end_kalibration.addLayout(layout_kalibrate_2)
        
        deco_startwert_desc = self.create_Elements.create_text_field("Diesen Wert so einstellen, dass der Schwingungstisch sich so langsam wie möglich bewegt.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_start_end_kalibration.addWidget(deco_startwert_desc)
        
        #Schrittgröße anpassen ------------------------------------------------
        layout_kalibrate_3 = QHBoxLayout()
        
        deco_stepsize = self.create_Elements.create_text_field("Schrittgröße", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_3.addWidget(deco_stepsize, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_stepsize = self.create_Elements.create_text_field(f"{self.stepsize}", self.variables_UI.font, 175, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        self.textfield_stepsize.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_kalibrate_3.addWidget(self.textfield_stepsize, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_start_end_kalibration.addLayout(layout_kalibrate_3)
        
        layout_kalibrate_4 = QHBoxLayout()
        layout_kalibrate_4.addWidget(self.create_Elements.create_image(self.picture_path + '/Schrittgroese_fein.png', 80))
        
        slider_stepsize = self.create_Elements.create_slider(1, 50000)
        slider_stepsize.setValue(self.stepsize)
        slider_stepsize.valueChanged.connect(self.slider_stepsize_changed)
        layout_kalibrate_4.addWidget(slider_stepsize)
        
        layout_kalibrate_4.addWidget(self.create_Elements.create_image(self.picture_path + '/Schrittgroese_grob.png', 80))
        
        layout_start_end_kalibration.addLayout(layout_kalibrate_4)
        
        deco_stepsize_desc = self.create_Elements.create_text_field("Definiert in welchen Schritten gemessen werden soll, kleiner = genauer dafür dauert es aber länger.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_start_end_kalibration.addWidget(deco_stepsize_desc)
        
        #Endwert anpassen ------------------------------------------------
        #layout_kalibrate_5 = QHBoxLayout()
        
        #deco_endwert = self.create_Elements.create_text_field("Endwert", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        #layout_kalibrate_5.addWidget(deco_endwert, alignment=Qt.AlignmentFlag.AlignLeft)
        
        #self.textfield_endwert = self.create_Elements.create_text_field(f"{self.endwert}", self.variables_UI.font, 175, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        #self.textfield_endwert.setAlignment(Qt.AlignmentFlag.AlignRight)
        #layout_kalibrate_5.addWidget(self.textfield_endwert, alignment=Qt.AlignmentFlag.AlignRight)
        
        #layout_start_end_kalibration.addLayout(layout_kalibrate_5)
        
        #layout_kalibrate_6 = QHBoxLayout()
        #layout_kalibrate_6.addWidget(self.create_Elements.create_image(self.picture_path + '/Abtastrate_low.png', 80))
        
        #self.slider_endwert = self.create_Elements.create_slider(0, 1000000)
        #self.slider_endwert.setValue(self.endwert)
        #self.slider_endwert.valueChanged.connect(self.slider_endwert_changed)
        #layout_kalibrate_6.addWidget(self.slider_endwert)
        
        #layout_kalibrate_6.addWidget(self.create_Elements.create_image(self.picture_path + '/Abtastrate_hoch.png', 80))
        
        #layout_start_end_kalibration.addLayout(layout_kalibrate_6)
        
        #deco_endwert_desc = self.create_Elements.create_text_field("Der Wert muss größer sein, als der Startwert. Er dient dazu um ein versehentliches übersteuern des Tisches zu verhindern. (Deaktiviert = 1.000.000)", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        #layout_start_end_kalibration.addWidget(deco_endwert_desc)
        
        #-------------------------------------------------
        layout_begin_kalibration = QVBoxLayout()
        #Header Beginn Kalibrierung
        layout_begin_kalibration_0 = QHBoxLayout()
        layout_begin_kalibration_0.addWidget(self.create_Elements.create_image(self.picture_path + '/Beginn_Kalibrierung_Icon.png', 30))
        
        label_beginn_kali = self.create_Elements.create_text_field("Beginn der Kalibrierung", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_begin_kalibration_0.addWidget(label_beginn_kali, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_begin_kalibration.addLayout(layout_begin_kalibration_0)
        
        #deco_label_beginn_desc = self.create_Elements.create_text_field("Der Oszi-Ausgang sollte ca. einen geglätteten Sinus anzeigen. Dies kann überprüft werden, indem der Startwert erhöht und dann wieder zurückgesetzt wird.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        #layout_begin_kalibration.addWidget(deco_label_beginn_desc)
        
        layout_begin_kalibration.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        #auf welche Beschleunigung -----------------------
        layout_kalibrate_7 = QHBoxLayout()
        
        deco_textfield_max_kalibrierung = self.create_Elements.create_text_field("Auf 1 g/1,5 g kalibrieren", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_7.addWidget(deco_textfield_max_kalibrierung, alignment=Qt.AlignmentFlag.AlignLeft)
        
        switch_max_kalibrierung = My_Switch(text_on="1,5 g", text_off="1 g", color_on=Qt.GlobalColor.cyan, color_off=Qt.GlobalColor.yellow)
        switch_max_kalibrierung.from_My_Switch_changed.connect(self.from_switch_max_kalibrierung)
        switch_max_kalibrierung.setChecked(self.max_kalibrierung) 
        
        layout_kalibrate_7.addWidget(switch_max_kalibrierung, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_begin_kalibration.addLayout(layout_kalibrate_7)
        
        deco_textfield_max_kalibrierung_desc = self.create_Elements.create_text_field("Hiermit kann eingestellt werden, ob eine maximale Beschleunigung für 1 g oder 1,5 g kalibriert werden soll.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_begin_kalibration.addWidget(deco_textfield_max_kalibrierung_desc)
        
        #Starte Kalibrierung
        layout_kalibrate_8 = QHBoxLayout()
        
        deco_textfield_start_kalibrate = self.create_Elements.create_text_field("Kalibrierung starten", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_8.addWidget(deco_textfield_start_kalibrate, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.button_start_kalibrate = QPushButton()
        self.button_start_kalibrate.setMinimumWidth(200)
        self.button_start_kalibrate.setFont(self.variables_UI.font)
        self.button_start_kalibrate.setText("starte Kalibrierung")
        self.button_start_kalibrate.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        self.button_start_kalibrate.clicked.connect(self.start_kalibrate)
        layout_kalibrate_8.addWidget(self.button_start_kalibrate, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_begin_kalibration.addLayout(layout_kalibrate_8)
        
        deco_textfield_reset_desc = self.create_Elements.create_text_field("Hiermit wird der Kalibriervorgang gestartet. Der Button zeigt nach dem Start den Fortschritt an.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_begin_kalibration.addWidget(deco_textfield_reset_desc)
        
        #-------------------------------------------------
        layout_detail_anpassung = QVBoxLayout()
        #Header Detail Kalibrierung
        layout_detail_anpassung_0 = QHBoxLayout()
        layout_detail_anpassung_0.addWidget(self.create_Elements.create_image(self.picture_path + '/Fein_Kalibrierung_Icon.png', 30))
        
        label_post_kali = self.create_Elements.create_text_field("Detailanpassungen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_detail_anpassung_0.addWidget(label_post_kali, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_detail_anpassung.addLayout(layout_detail_anpassung_0)
        
        deco_label_post_kali_desc = self.create_Elements.create_text_field("Die Einstellungen sind nur im kalibrierten Zustand linear.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        layout_detail_anpassung.addWidget(deco_label_post_kali_desc)
        
        layout_detail_anpassung.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        #Linearer Offset 1 g -----------------------
        layout_kalibrate_9 = QHBoxLayout()
        
        deco_linear_offset_1g = self.create_Elements.create_text_field("linearer Offset 1g", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_9.addWidget(deco_linear_offset_1g, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_linear_offset_1g = self.create_Elements.create_text_field(self.variables_UI.text_accel.format(self.linear_offset_1g), self.variables_UI.font, 175, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        self.textfield_linear_offset_1g.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_kalibrate_9.addWidget(self.textfield_linear_offset_1g, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_detail_anpassung.addLayout(layout_kalibrate_9)
        
        layout_kalibrate_10 = QHBoxLayout()
        layout_kalibrate_10.addWidget(self.create_Elements.create_image(self.picture_path + '/negativ_offset_1g_Icon.png', 80))
        
        self.slider_linear_offset_1g = self.create_Elements.create_slider(-20, 20)
        self.slider_linear_offset_1g.setValue(int(self.linear_offset_1g*self.DIVIDER))
        self.slider_linear_offset_1g.valueChanged.connect(self.slider_linear_offset_1g_changed)
        layout_kalibrate_10.addWidget(self.slider_linear_offset_1g)
        
        layout_kalibrate_10.addWidget(self.create_Elements.create_image(self.picture_path + '/positiv_offset_1g_Icon.png', 80))
        
        layout_detail_anpassung.addLayout(layout_kalibrate_10)
        
        deco_linear_offset_1g_desc = self.create_Elements.create_text_field("Erlaubt es nach der Kalibrierung einen zusätzlichen Offset auf die Beschleunigungskurve für 1 g zu geben.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_detail_anpassung.addWidget(deco_linear_offset_1g_desc)
        
        #Linearer Offset 1.5 g -----------------------
        layout_kalibrate_11 = QHBoxLayout()
        
        deco_linear_offset_15g = self.create_Elements.create_text_field("linearer Offset 1,5g", self.variables_UI.font, 30, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_kalibrate_11.addWidget(deco_linear_offset_15g, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_linear_offset_15g = self.create_Elements.create_text_field(self.variables_UI.text_accel.format(self.linear_offset_15g), self.variables_UI.font, 175, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light)
        self.textfield_linear_offset_15g.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_kalibrate_11.addWidget(self.textfield_linear_offset_15g, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_detail_anpassung.addLayout(layout_kalibrate_11)
        
        layout_kalibrate_12 = QHBoxLayout()
        layout_kalibrate_12.addWidget(self.create_Elements.create_image(self.picture_path + '/negativ_offset_1,5g_Icon.png', 80))
        
        self.slider_linear_offset_15g = self.create_Elements.create_slider(-20, 20)
        self.slider_linear_offset_15g.setValue(int(self.linear_offset_15g*self.DIVIDER))
        self.slider_linear_offset_15g.valueChanged.connect(self.slider_linear_offset_15g_changed)
        layout_kalibrate_12.addWidget(self.slider_linear_offset_15g)
        
        layout_kalibrate_12.addWidget(self.create_Elements.create_image(self.picture_path + '/positiv_offset_1,5g_Icon.png', 80))
        
        layout_detail_anpassung.addLayout(layout_kalibrate_12)
        
        deco_linear_offset_15g_desc = self.create_Elements.create_text_field("Erlaubt es nach der Kalibrierung einen zusätzlichen Offset auf die Beschleunigungskurve für 1,5 g zu geben.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_detail_anpassung.addWidget(deco_linear_offset_15g_desc)
        
        #Adding background colors to the single layouts
        kalibrate_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_vorbereitung, color=self.variables_UI.color_background_light))
        kalibrate_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_start_end_kalibration, color=self.variables_UI.color_background_light))
        kalibrate_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_begin_kalibration, color=self.variables_UI.color_background_light))
        kalibrate_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_detail_anpassung, color=self.variables_UI.color_background_light))
        
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(".QScrollBar {width: 50px;}")
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_kalibrate_page)
                
        return scroll_area
