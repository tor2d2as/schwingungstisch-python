from PyQt6.QtGui import QColor, QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QPushButton, QTextEdit, QLabel, QSizePolicy, QFrame, QSlider
from PyQt6.QtCore import QSize, Qt, QRect
from PyQt6 import QtGui
import PyQt6.QtCore as QtCore
from PyQt6.QtCore import pyqtSignal
        
class My_Switch(QPushButton):
    """ Für jeden Switch auf der UI muss eine Neue Instanz von My_Switch erstellt werden.
        Über das PyQt Signal kann ein Notifier erstellt werden, der eine Methode aufruft wenn sich der Zustand des Switches ändert"""
    actual_state = False
    from_My_Switch_changed = pyqtSignal(bool)
    
    def __init__(self, parent = None, text_on="ON", text_off="OFF", color_on=Qt.GlobalColor.green, color_off=Qt.GlobalColor.red):
        super().__init__(parent)
        self.text_on = text_on
        self.text_off = text_off
        self.color_on = color_on
        self.color_off = color_off
        
        self.setCheckable(True)
        self.setMinimumWidth(200)
        self.setMinimumHeight(60)
        
        font_slider = QFont()
        font_slider.setPointSize(27)
        self.setFont(font_slider)
        
    def paintEvent(self, event):
        """ Wird von der PyQt6 aufgerufen und definiert wie der MySwitch neu gezeichnet werden soll."""
        if self.isChecked():
            label = self.text_on
            bg_color = self.color_on
            if not self.actual_state:
                self.from_My_Switch_changed.emit(True)
                #self.notify_changes.from_My_Switch_changed(self.id, True)
        else:
            label = self.text_off
            bg_color = self.color_off
            if self.actual_state:
                self.from_My_Switch_changed.emit(False)
                #self.notify_changes.from_My_Switch_changed(self.id, False)
            
        self.actual_state = self.isChecked()
        radius = 20
        width = 100
        center = self.rect().center()

        painter = QtGui.QPainter(self)
        painter.translate(center)
        painter.setBrush(QColor(0,0,0))

        pen = QtGui.QPen(Qt.GlobalColor.black)
        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawRoundedRect(QRect(-width, -radius, 2*width, 2*radius), radius, radius)
        painter.setBrush(QtGui.QBrush(bg_color))
        sw_rect = QRect(-radius, -radius, width + radius, 2*radius)
        if not self.isChecked():
            sw_rect.moveLeft(-width)
        painter.drawRoundedRect(sw_rect, radius, radius)
        painter.drawText(sw_rect, Qt.AlignmentFlag.AlignCenter, label)
        
class HorizontalStroke(QFrame):
    def __init__(self, color, thickness=10):
        """ Es fügt einen Horizontalen Strich auf der UI hinzu (reines Deko Element)
        color = kann die Farbe von diesem Angepasst werden.
        Thickness = Es kann die Dicke des Balkens festgelegt werden, der Standardwert ist 10"""
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setLineWidth(thickness)
        self.setStyleSheet(f"QFrame{{border: 2px solid {color};}}")
        
class Create_Elements():
    def set_layout_background_color(self, layout, color):
        """ Es packt das Layout in ein Widget und passt die Hintergrundfarbe von diesem mit dem Argument color an."""
        layout_widget = QWidget()
        layout_widget.setLayout(layout)
        layout_widget.setStyleSheet(f"background-color: {color};")
        return layout_widget
    
    def create_image(self, path_to_image, width):
        """ Es packt das angegebene Bild in path_to_image in ein QLabel, welches dann auf der UI als Widget eingebunden werden kann.
            width: Die Breite die das Bild auf der UI haben soll """
        label = QLabel()
        #print(path_to_image)
        pixmap = QPixmap(path_to_image)
        label.resize(width, label.height())
        label.setPixmap(pixmap.scaled(label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio))
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        return label
    
    def create_slider(self, range_start, range_end):
        """ Es erstellt einen Slider welcher auf der UI als Widget eingebunden werden kann. """
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(range_start, range_end)
        slider.setSingleStep(1)
        slider.setTickInterval(1)
        slider.setStyleSheet("""
                            QSlider {min-height: 60px; max-height: 60px}
                            QSlider::groove:horizontal {
                                height: 5px;
                                background: solid #FF0000;
                            }
                            QSlider::add-page:horizontal{
                                background: solid #555555
                            }
                            QSlider::sub-page:horizontal{
                                background: solid #4854C7
                            }
                            QSlider::handle:horizontal {
                                background: solid #AAAAAA;
                                border: 1px solid #5c5c5c;
                                width: 80px; 
                                height: 70px; 
                                margin: -30px 0; 
                                border-radius: 15px;
                            }
                            """)
        return slider
    
    def create_text_field(self, text, font=None, padding=20, text_color=None, color=None, is_explanation=False):
        """ Erstellt ein Textfeld mit den gegebenen Spezifikationen """
        text_edit = QTextEdit(text)
        text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if font is not None:
            text_edit.setFont(font)
        if not is_explanation:
            self.adjust_text_field_size(text_edit, padding)
        else:
            text_height = int(text_edit.fontMetrics().boundingRect(text_edit.toPlainText()).height())*2 + 10
            text_edit.setMinimumHeight(text_height)
            text_edit.setMaximumHeight(text_height)
        text_edit.setStyleSheet("border: none; background-color: {0}; color: {1}".format(color, text_color))
        return text_edit
        
    def adjust_text_field_size(self, textfield, padding=10):
        """Diese Methode passt die Größe des Textfelds an dessen Inhalt an und deaktiviert die Scrollbars. """
        text_height = int(textfield.fontMetrics().boundingRect(textfield.toPlainText()).height()) + 10
        text_width = int(textfield.fontMetrics().boundingRect(textfield.toPlainText()).width() + padding)  # Add some padding
        textfield.setMinimumSize(QSize(text_width, text_height))
        textfield.setMaximumSize(QSize(text_width, text_height))
        
        
