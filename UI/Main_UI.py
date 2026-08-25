from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
import threading

from Variables_UI import Variables_UI

from UI_Elements import Create_Elements
from UI_Elements import My_Switch

from IncGeber import IncGeber
     
class Main_UI:
    
    actual_accel = 0
    table_state = False #Aktualisiere die Variable table_state nur in den Methoden turn_on_table() und turn_off_table() und nirgendwo sonst.
    NORMAL_MAX_ACCEL = 98
    HIGHER_MAX_ACCEL = 147
    DIVIDER = 10 #Teilt die aktuelle Beschleunigung, so dass diese auf der UI korrekt angezeigt wird (im Hintergrund wird mit Integern gearbeitet).
    STEP_SIZE_INCREMENTGEBER = 0.1
        
    def __init__(self, root_dir, bluetooth_module, mpu6050, motor_steuerung):
        """ Initialisiert verschiedene Module, welche für die Main UI benötigt werden.
            root_dir = Das root Verzeichnis des Projekts """
        self.picture_path = root_dir + '/pictures/'
        self.bluetooth_module = bluetooth_module
        self.mpu6050 = mpu6050
        self.mpu6050.update_accel_UI.connect(self.from_mpu6050_periodic)
        
        self.motor_steuerung = motor_steuerung
        
        self.create_Elements = Create_Elements()
        
        self.variables_UI = Variables_UI()
        
        self.incGeber = IncGeber()
        self.incGeber.incGeber_moved.connect(self.from_incremental_changed_value)
        self.incGeber.incGeber_pressed.connect(self.from_incremental_button_pressed)
        self.incGeber.start_reading()
    
    def turn_on_table(self):
        """ Wenn der Tisch nocht nicht an ist, wird der Tisch angeschaltet. Ansonsten passiert nichts. """
        if not self.table_state:
            self.table_state = True
            self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.TABLE_STATE, self.table_state))
            #self.increase_accel_range(False)
            self.switch_enable_table.setChecked(True)
            self.mpu6050.start_data_periodic()
            print("Der Tisch wurde angeschaltet")
        
    def turn_off_table(self, shutdown_table=False):
        """ Die Methode schaltet den Tisch aus """       
        #Die Bluetooth Verbindung zum Handy kann auch nach dem Beenden des Programms mit dem Raspberry Pi bestehen bleiben, deswegen muss diese beim Beenden des Skripts mit beendet werden. 
        if shutdown_table:
            self.motor_steuerung.shutdown_motor()
            self.bluetooth_module.stop_connection()
        else:
            self._slider_set_accel_changed(0, True)
        self.increase_accel_range(False)
        self.table_state = False
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.TABLE_STATE, self.table_state))
            
        self.switch_enable_table.setChecked(False)
        self.switch_enable_oszi.setChecked(False)
        self.mpu6050.stop_oszi_out()
        self.mpu6050.stop_data_periodic()
        #self.textfield_accel_set.setText(self.variables_UI.text_accel.format(0.0))
        self.textfield_accel_is.setText(self.variables_UI.text_accel.format(0.0))
        self.textfield_accel_is.setAlignment(Qt.AlignmentFlag.AlignRight)
            
        self.slider_accel_set.setValue(0)
            
        print("Der Tisch wurde ausgeschaltet")
    
    #Methoden welche von den UI-Elementen aufgerufen werden -------------------------------------------------------
    def change_table_state(self, new_state):
        """ Die Methode wird aufgerufen wenn der an/aus Schalter für den TISCH auf der UI gedrückt wird.
            new_state: true = Der Tisch wird aktiviert
                       false = Der Tisch wird ausgeschaltet"""
        if new_state:
            self.turn_on_table()  
        else:
            self.turn_off_table()
    
    def change_oszi_state(self, new_state):
        """ Die Methode wird aufgerufen wenn der an/aus Schalter für den OSZILLOSKOP AUSGANG auf der UI gedrückt wird.
            new_state: true = Der Osziloskopausgang wird aktiviert
                       false = Der Osziloskopausgang wird ausgeschaltet"""
        if new_state:
            self.turn_on_table()
            self.mpu6050.start_oszi_out()
        else:
            self.mpu6050.stop_oszi_out()
                
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.OSZI_STATE, self.switch_enable_oszi.isChecked()))
    
    #Methods to handle the slider for the accelaration ------------------------------
    def slider_set_accel_changed(self, value):
        """ Wird aufgerufen wenn der Slider zur Einstellung der Beschleunigung bewegt wird.
            Die UI wird sofort auf den neuen Wert gesetzt. Updates an die Steuerung werden
            mit einer Verzögerung an die Steuerung gesendet. Diese Verzögerung ist als Filter
            implementiert, so dass nur die vom Nutzer gewünschten Werte an den Motor gesendet werden und
            keine Zwischenwerte (diese entstehen z.B. wenn am Incrementgeber gedreht wird).
            value = Der neue Beschleunigungswert"""
        self.actual_accel = value / self.DIVIDER
        self.textfield_accel_set.setText(self.variables_UI.text_accel.format(self.actual_accel))
        threading.Timer(0.3, self._slider_set_accel_changed, args=[self.actual_accel]).start()
        
    def _slider_set_accel_changed(self, value_to_check, check_value=False):
        """ Schickt den neuen Wert der Steuerung sofort an den Motor. Ebenfalls wird der Tisch bei Bedarf
            eingeschaltet.
            value_to_check = Der Wert der gesetzt werden soll
            check_value true = Der neue Wert wird immer gesetzt
                        false = Der Wert wird nur gesetzt wenn er mit self.actual_accel übereinstimmt
                        (dies verhindert, das wenn der Slider geändert wird die Werte sofort übernommen werden). """
        if (value_to_check is self.actual_accel) or (check_value):
            
            self.motor_steuerung.set_motor_new_accel(value_to_check, max_Value=self.mpu6050.enable_higher_max_accel)
            
            #Schaltet den Tisch ein, sofern dieser noch nicht an ist
            if value_to_check != 0:
                self.turn_on_table()
            
            #Sendet die aktualisierten Daten per Bluetooth an die Handy App
            self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.UPDATE_SET_ACCEL, value_to_check*self.DIVIDER))
            
    def increase_accel_range(self, enable_higher):
        """ Wird von der Einstellungsseite aufgerufen.
            Stellt ein ob die Beschleunigung bis 1g oder 1,5g erhöht werden kann.
            Wenn die max. Beschleunigung von 1,5 g auf 1 g verringert wird und der eingestellte Wert
            für die Beschleunigung > 1 g ist, wird diese auf 1 g runtergestellt """
        self.mpu6050.enable_higher_max_accel = enable_higher
        if enable_higher:
            self.slider_accel_set.setRange(0, self.HIGHER_MAX_ACCEL)
        else:
            self.slider_accel_set.setRange(0, self.NORMAL_MAX_ACCEL)
        self.mpu6050.change_adjust_oszi_out()
        self.bluetooth_module.send_data_to_phone("{\"%s\":\"%s\"}" % (self.bluetooth_module.INCREASE_ACCEL_RANGE, enable_higher))
    
    #Method which are called by the Hardware APIs ------------------------------------------
    def from_mpu6050_periodic(self, y_accel):
        """ Die Methode zeigt die vom MPU6050 gemessene Beschleunigung an. Sie wird ca. 4x pro sekunde aufgerufen.
            y_accel: Die gemessene Beschleunigung """
        self.textfield_accel_is.setText(self.variables_UI.text_accel.format(y_accel))
        self.textfield_accel_is.setAlignment(Qt.AlignmentFlag.AlignRight)
        
    def from_incremental_changed_value(self, direction):
        """ Die Methode wird aufgerufen, wenn der Nutzer am Incrementalgeber dreht.
            Sie sorgt dafür das die Werte auf der UI Ausgegeben werden, ebenso dass die aktuelle Beschleunigung
            nicht über das eingestellte Limit geht.
            direction: true = Die Beschleunigung wird erhöht
                       false = Die Beschleunigung wird veringert """
        need_update = False
        #Checked ob das 1 g oder 1,5 g limit aktiv ist
        if self.mpu6050.enable_higher_max_accel:
            max_val = self.HIGHER_MAX_ACCEL
        else:
            max_val = self.NORMAL_MAX_ACCEL
            
        #Ermittelt ob die Beschleunigung größer oder kleiner werden soll, es beachtet dabei die Limits (0 g & 1 g/1,5 g)
        if direction == True:
            if self.actual_accel < max_val/self.DIVIDER:
                self.actual_accel = round(self.actual_accel + self.STEP_SIZE_INCREMENTGEBER, 1)
                need_update = True
        else:
            if self.actual_accel > 0:
                self.actual_accel = round(self.actual_accel - self.STEP_SIZE_INCREMENTGEBER, 1)
                need_update = True
                
        #Wenn nötig, wird die UI aktualisiert
        if need_update:
            #self.textfield_accel_set.setText(self.variables_UI.text_accel.format(self.actual_accel))
            self.slider_accel_set.setValue(int(self.actual_accel * self.DIVIDER))
            #Rufe die Methode self.slider_set_accel_changed() nicht auf, diese wird automatisch aufgerufen, wenn der Slider aktualisiert wird. 
            
    def from_incremental_button_pressed(self):
        """ Diese Methode wird aufgerufen wenn der Incrementgeber gedrückt wird, sie hat derzeit keine Funktion """
        print("Button was pressed")
    

    #------------------------------------------------------------------------
    def create_main_tab(self):
        """ Erstellt das Tab für die Main UI """
        container_main_page = QWidget()
        main_layout = QVBoxLayout(container_main_page)
        
        #Aktiviere / Deaktiviere den Schwingunstisch
        layout_double1 = QHBoxLayout()
        
        deco_textfield_table_state = self.create_Elements.create_text_field("Schwingungstisch aktivieren", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_dark)
        layout_double1.addWidget(deco_textfield_table_state, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.switch_enable_table = My_Switch()
        self.switch_enable_table.from_My_Switch_changed.connect(self.change_table_state)
        self.switch_enable_table.setChecked(False)        
        
        layout_double1.addWidget(self.switch_enable_table, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(layout_double1)
        #Zeige die aktuelle Beschleunigung
        deco_textfield_accel_is = self.create_Elements.create_text_field("Die aktuelle Beschleunigung ist", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_dark)
        main_layout.addWidget(deco_textfield_accel_is, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_accel_is = self.create_Elements.create_text_field(self.variables_UI.text_accel.format(0.0), self.variables_UI.font_big, 180, f"{self.variables_UI.color_text_dark}", color=self.variables_UI.color_background_dark)
        self.textfield_accel_is.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.textfield_accel_is, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        #Erstelle den Slider für die maximale Beschleunigung mit Dekoration
        layout_double2 = QHBoxLayout()
        
        layout_double2.addWidget(self.create_Elements.create_image(self.picture_path + 'Beschleunigung_Icon_langsamer.png', 40))
        
        self.slider_accel_set = self.create_Elements.create_slider(0, self.NORMAL_MAX_ACCEL)
        self.slider_accel_set.valueChanged.connect(self.slider_set_accel_changed)
        layout_double2.addWidget(self.slider_accel_set)
        
        layout_double2.addWidget(self.create_Elements.create_image(self.picture_path + 'Beschleunigung_Icon_schneller.png', 40))
        
        main_layout.addLayout(layout_double2)
        
        #Einstellung der maximalen Beschleunigung
        layout_double3 = QHBoxLayout()
        
        deco_textfield_accel_set = self.create_Elements.create_text_field("Die maximale Beschleunigung ist", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_dark)
        layout_double3.addWidget(deco_textfield_accel_set, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.textfield_accel_set = self.create_Elements.create_text_field(self.variables_UI.text_accel.format(0.0), self.variables_UI.font, 40, self.variables_UI.color_text_dark, color=self.variables_UI.color_background_dark)
        layout_double3.addWidget(self.textfield_accel_set, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(layout_double3)
        
        #Aktiviere / Deaktiviere den Oszilloskop-Output
        layout_double5 = QHBoxLayout()
        deco_textfield_enable_oszi = self.create_Elements.create_text_field("Oszilloskop Output aktivieren", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_dark)
        layout_double5.addWidget(deco_textfield_enable_oszi, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.switch_enable_oszi = My_Switch()
        self.switch_enable_oszi.from_My_Switch_changed.connect(self.change_oszi_state)
        self.switch_enable_oszi.setChecked(False)
        
        layout_double5.addWidget(self.switch_enable_oszi, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(layout_double5)
        
        return container_main_page
