from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
import sys
import subprocess
from UI_Elements import Create_Elements
from Variables_UI import Variables_UI
from UI_Elements import HorizontalStroke

class Shutdown_UI:
    
    def __init__(self, Main, root_dir):
        self.root_dir = root_dir
        self.main = Main
        
        self.picture_path = root_dir + '/pictures/'
        
        self.create_Elements = Create_Elements()
        self.variables_UI = Variables_UI()
        
    def shutdown(self):
        """ Beendet den Schwingungstisch und fährt den Raspberry Pi herunter """
        self.main.goodbye()
        subprocess.call(["sh", f"{self.root_dir}/Library/shutdown.sh"])
        
    def start_desktop(self):
        """ Beendet den Schwingungstisch und schließt das Programm """
        self.main.goodbye()
        sys.exit()
        
    def create_shutdown_tab(self):
        #Erstelle Tab: Shutdown Page -------------------------
        container_shutdown_page = QWidget()
        shutdown_main_layout = QVBoxLayout(container_shutdown_page)
        
        #-------------------------------------------
        layout_desktop = QVBoxLayout()
        #------------------------------------------
        #Überschrift Desktop 
        layout_visibility_setting_1 = QHBoxLayout()
        layout_visibility_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Exit_Icon.png', 30))
        
        label_visibility_settigs = self.create_Elements.create_text_field("Programm beenden", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_1.addWidget(label_visibility_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_desktop.addLayout(layout_visibility_setting_1)
        
        layout_desktop.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Desktop öffnen
        layout_desktop_1 = QHBoxLayout()
        
        deco_textfield_openDesktop = self.create_Elements.create_text_field("Desktop öffnen", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_desktop_1.addWidget(deco_textfield_openDesktop, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_desktop = QPushButton()
        button_desktop.setMinimumWidth(200)
        button_desktop.setFont(self.variables_UI.font)
        button_desktop.setText("Desktop aufrufen")
        button_desktop.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_desktop.clicked.connect(self.start_desktop)
        layout_desktop_1.addWidget(button_desktop, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_desktop.addLayout(layout_desktop_1)
        
        deco_textfield_desktop_desc = self.create_Elements.create_text_field("Stoppt den Motor und schließt danach das Programm.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_desktop.addWidget(deco_textfield_desktop_desc)
        
        #-------------------------------------------
        layout_shutdown = QVBoxLayout()
        #------------------------------------------
        #Überschrift Herunterfahren 
        layout_visibility_setting_1 = QHBoxLayout()
        layout_visibility_setting_1.addWidget(self.create_Elements.create_image(self.picture_path + '/Ausschalten_Icon.png', 30))
        
        label_visibility_settigs = self.create_Elements.create_text_field("Schwingungstisch herunterfahren", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_1.addWidget(label_visibility_settigs, alignment=Qt.AlignmentFlag.AlignLeft)
        
        layout_shutdown.addLayout(layout_visibility_setting_1)
        
        layout_shutdown.addWidget(HorizontalStroke(color=self.variables_UI.color_text_dark))
        
        #Herunterfahren
        layout_visibility_setting_3 = QHBoxLayout()
        
        deco_textfield_turn_off_visibility = self.create_Elements.create_text_field("Den Schwingungstisch herunterfahren", self.variables_UI.font, 20, text_color=self.variables_UI.color_text_light, color=self.variables_UI.color_background_light)
        layout_visibility_setting_3.addWidget(deco_textfield_turn_off_visibility, alignment=Qt.AlignmentFlag.AlignLeft)
        
        button_shutdown = QPushButton()
        button_shutdown.setMinimumWidth(200)
        button_shutdown.setFont(self.variables_UI.font)
        button_shutdown.setText("Herunterfahren")
        button_shutdown.setStyleSheet(f"color: {self.variables_UI.color_text_light};")
        button_shutdown.clicked.connect(self.shutdown)
        layout_visibility_setting_3.addWidget(button_shutdown, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout_shutdown.addLayout(layout_visibility_setting_3)
        
        deco_textfield_visibility_off_desc = self.create_Elements.create_text_field("Stoppt den Motor und fährt danach den Schwingungstisch herunter.", self.variables_UI.font_small, text_color=self.variables_UI.color_text_dark, color=self.variables_UI.color_background_light, is_explanation=True)
        layout_shutdown.addWidget(deco_textfield_visibility_off_desc)
        
        #-----------------------------------------------------------------
        
        shutdown_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_desktop, color=self.variables_UI.color_background_light))
        shutdown_main_layout.addWidget(self.create_Elements.set_layout_background_color(layout_shutdown, color=self.variables_UI.color_background_light))
        
        return container_shutdown_page
