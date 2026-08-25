from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from UI_Elements import Create_Elements
from Variables_UI import Variables_UI
from UI_Elements import HorizontalStroke

class Bluetooth_UI:
    
    def __init__(self, root_dir, bluetooth_module, tabs):
        """ Initialisiert verschiedene Module, welche für die Bluetooth UI benötigt werden
            bluetooth_module = Das initialisierte Bluetooth Module
            tabs = Die Tabs in der UI """
        self.picture_path = root_dir + '/pictures/'
        
        self.bluetooth_module = bluetooth_module
        self.bluetooth_module.update_connection_state.connect(self.update_connection_state)
        
        self.tabs = tabs
        
        self.create_Elements = Create_Elements()
        self.variables_UI = Variables_UI()
        
    def update_connection_state(self, message, change_tab):
        #print(message, change_tab)
        """Diese Methode ändert den Text auf dem Button: Connect in der Bluetooth UI auf den Text in message.
           Wenn change_tab True ist, wird zudem automatisch die Bluetooth-UI aufgerufen."""
        if change_tab:
            self.tabs.setCurrentIndex(2)
        self.button_connect_bluetooth.setText(message)
    
    def create_bluetooth_tab(self):
        #Create Tab: Bluetooth Page -------------------------
        container_bluetooth_page = QWidget()
        bluetooth_main_layout = QVBoxLayout(container_bluetooth_page)
        
        #-------------------------------------------
        layout_visibility = QVBoxLayout()
        #------------------------------------------
        #Header Visibility
        layout_visibility_setting_1 = QHBoxLayout()
        layout_visibility_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Bluetooth_connect_Icon.png', 50))
        
        label_visibility_settigs = self.create_Elements.create_text_field("Bluetooth Sichtbarkeit", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_1.addWidget(label_visibility_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_visibility.addLayout(layout_visibility_setting_1)
        
        layout_visibility.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Bluetooth Sichtbarkeit-einschalten
        layout_visibility_setting_2 = QHBoxLayout()
        
        deco_textfield_turn_on_visibility = self.create_Elements.create_text_field("Schwingungstisch sichtbar machen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_2.addWidget(deco_textfield_turn_on_visibility, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_make_bluetooth_discoverable = QPushButton()
        button_make_bluetooth_discoverable.setMinimumWidth(200)
        button_make_bluetooth_discoverable.setFont(self.variables_UI.font)
        button_make_bluetooth_discoverable.setText("Sichtbarkeit-einschalten")
        button_make_bluetooth_discoverable.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_make_bluetooth_discoverable.clicked.connect(self.bluetooth_module.make_discoverable)
        layout_visibility_setting_2.addWidget(button_make_bluetooth_discoverable, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_visibility.addLayout(layout_visibility_setting_2)
        
        deco_textfield_visibility_desc = self.create_Elements.create_text_field("Hiermit wird der Schwingungstisch für andere Bluetooth-Geräte sichtbar.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_visibility.addWidget(deco_textfield_visibility_desc)
        
        #Bluetooth Sichtbarkeit-ausschalten
        layout_visibility_setting_3 = QHBoxLayout()
        
        deco_textfield_turn_off_visibility = self.create_Elements.create_text_field("Schwingungstisch unsichtbar machen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_3.addWidget(deco_textfield_turn_off_visibility, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_stop_bluetooth_discoverable = QPushButton()
        button_stop_bluetooth_discoverable.setMinimumWidth(200)
        button_stop_bluetooth_discoverable.setFont(self.variables_UI.font)
        button_stop_bluetooth_discoverable.setText("Sichtbarkeit-ausschalten")
        button_stop_bluetooth_discoverable.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_stop_bluetooth_discoverable.clicked.connect(self.bluetooth_module.stop_discoverable)
        layout_visibility_setting_3.addWidget(button_stop_bluetooth_discoverable, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_visibility.addLayout(layout_visibility_setting_3)
        
        deco_textfield_visibility_off_desc = self.create_Elements.create_text_field("Hiermit wird der Schwingungstisch für andere Bluetooth-Geräte unsichtbar.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_visibility.addWidget(deco_textfield_visibility_off_desc)
        
        #-------------------------------------------
        layout_connect = QVBoxLayout()
        #------------------------------------------
        #Header Handy App
        layout_connect_setting_1 = QHBoxLayout()
        layout_connect_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Handy_Icon.png', 30))
        
        label_connect_settigs = self.create_Elements.create_text_field("Handy App", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_connect_setting_1.addWidget(label_connect_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_connect.addLayout(layout_connect_setting_1)
        
        layout_connect.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Button Verbinde zur Handy App
        layout_connect_setting_2 = QHBoxLayout()
        
        deco_textfield_connect = self.create_Elements.create_text_field("Verbinde zur Handy-App", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_connect_setting_2.addWidget(deco_textfield_connect, alignment=Qt.AlignmentFlag.AlignLeft)
        
        self.button_connect_bluetooth = QPushButton()
        self.button_connect_bluetooth.setMinimumWidth(200)
        self.button_connect_bluetooth.setFont(self.variables_UI.font_small)
        self.button_connect_bluetooth.setText("zur Handy-App verbinden")
        self.button_connect_bluetooth.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        self.button_connect_bluetooth.clicked.connect(self.bluetooth_module.connect_bluetooth)
        layout_connect_setting_2.addWidget(self.button_connect_bluetooth, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_connect.addLayout(layout_connect_setting_2)
        
        deco_textfield_connect_desc = self.create_Elements.create_text_field("Deaktiviert die Sichtbarkeit des Tisches und wartet auf eine Verbindungsanfrage der Handy App.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_connect.addWidget(deco_textfield_connect_desc)
        
        
        #-----------------------------------------------------------------
        #button_make_bluetooth_discoverable = QPushButton("Schwingungstisch für andere Bluetooth-Geräte sichtbar machen")
        #button_make_bluetooth_discoverable.clicked.connect(self.bluetooth_module.make_discoverable)
        #button_make_bluetooth_discoverable.setMinimumHeight(100)
        #bluetooth_main_layout.addWidget(button_make_bluetooth_discoverable)
        
        #button_stop_bluetooth_discoverable = QPushButton("Schwingungstisch für andere Bluetooth-Geräte unsichtbar machen")
        #button_stop_bluetooth_discoverable.clicked.connect(self.bluetooth_module.stop_discoverable)
        #button_stop_bluetooth_discoverable.setMinimumHeight(100)
        #bluetooth_main_layout.addWidget(button_stop_bluetooth_discoverable)
        
        #self.button_connect_bluetooth = QPushButton("Verbinde zur Handy-App")
        #self.button_connect_bluetooth.clicked.connect(self.bluetooth_module.connect_bluetooth)
        #self.button_connect_bluetooth.setMinimumHeight(100)
        #bluetooth_main_layout.addWidget(self.button_connect_bluetooth)
        #-----------------------------------------------------------------
        
        bluetooth_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_visibility, color=self.variables_UI.color_background_light))
        bluetooth_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_connect, color=self.variables_UI.color_background_light))

        return container_bluetooth_page
