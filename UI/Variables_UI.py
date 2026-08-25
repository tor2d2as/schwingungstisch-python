from PyQt6.QtGui import QFont

class Variables_UI:
    font = QFont()
    font.setPointSize(32)
        
    font_big = QFont()
    font_big.setPointSize(80)
        
    font_small = QFont()
    font_small.setPointSize(27)
        
    text_accel = "{0} m/s\u00B2"
    text_sample_rate = "{0} 1/s"
    step_oszi_output = "{0} mV"
        
        
    color_background_dark = "#4A4A4A"
    color_background_light = "#595959"
    color_text_dark = "#BBBBBB"
    color_text_light = "#FFFFFF"