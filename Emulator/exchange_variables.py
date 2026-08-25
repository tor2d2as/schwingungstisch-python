def init():
    #Diese Methode darf nur einmal im Programm aufgerufen werden.
    global motor_output
    motor_output = -2 #Ermöglicht es das der simulierte Motoroutput in m/s^2 an den simulierten Beschleunigungssensor übergeben werden kann.
