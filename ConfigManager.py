import xml.etree.ElementTree as ET

class ConfigManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def _write_to_xml_config(self, config_data):
        """
        Schreibe config_data in die XML-Datei die in file_path hinterlegt ist.

        Parameter:
            config_data (dict): Dictionary das die Konfigurationsdaten enthält.
        """
        root = ET.Element("config")

        for key, value in config_data.items():
            element = ET.SubElement(root, key)
            element.text = str(value)

        tree = ET.ElementTree(root)
        with open(self.file_path, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)

    def write_single_value_to_xml(self, key, value):
        """
        Schreibt einen einzelnen Wert in die XML-Datei die in file_path hinterlegt ist.

        Parameter:
            key (str): Key in der Config-Datei
            value: Der Wert der in die Config-Datei geschrieben werden soll.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        for element in root.findall(key):
            element.text = str(value)
        tree.write(self.file_path, encoding="utf-8", xml_declaration=True)

    def _read_config(self):
        """
        Liest alle Daten aus der XML-Datei die in file_path hinterlegt ist und gibt diese als dict zurück.
        """
        config_data = {}
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        for child in root:
            config_data[child.tag] = child.text
        return config_data

    def read_value_from_xml_config(self, key):
        """
        Liest einen bestimmten Wert aus der XML-Datei die in file_path hinterlegt ist und gibt diesen zurück, None wenn es den Wert nicht gibt.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        for child in root:
            if child.tag == key:
                return child.text

        return None
    
    def reset_setting_config(self):
        #Standard config
        config_data = {
            "accel_meas_area": 0,
            "accel_low_pass": 5,
            "accel_sampling_rate": 0,
            #"increase_max_accel": False, #Dieser Wert wird immer mit False initialisiert und nicht in der Config gespeichert.
            "fit_oszi_out": True,
        }
        self._write_to_xml_config(config_data)
        
    def reset_motor_config(self):
        #Standard config
        config_data = {
            "a_98": 9.71344967806038e-09,
            "b_98": 0.00861568027523539,
            "c_98": -665.93193139330820874,
            "rundung_98":1000,
            "offset_98": 0,
            
            "a_147": 9.71344967806038e-09,
            "b_147": 0.00861568027523539,
            "c_147": -665.93193139330820874,
            "rundung_147":1000,
            "offset_147": 0
        }
        self._write_to_xml_config(config_data)
