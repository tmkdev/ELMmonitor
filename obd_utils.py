import serial
import platform

def scanSerial():
    """scan for available ports. return a list of serial names"""
    available = []
    #for i in range(4):
    #  try: #scan standart ttyS*
    #    s = serial.Serial(i)
    #    available.append(s.portstr)
    #    s.close()   # explicit close 'cause of delayed GC in java
    #  except serial.SerialException:
    #    pass
    #for i in range(4):
    #  try: #scan USB ttyACM
    #    s = serial.Serial("/dev/ttyACM"+str(i))
    #    available.append(s.portstr)
    #    s.close()   # explicit close 'cause of delayed GC in java
    #  except serial.SerialException:
    #    pass
    for i in range(8):
      try: #scan pts
        s = serial.Serial("/dev/ttyUSB"+str(i))
        available.append(s.portstr)
        s.close()   # explicit close 'cause of delayed GC in java
      except serial.SerialException:
        pass
    for i in range(8):
      try: #scan pts
        s = serial.Serial("/dev/pts/"+str(i))
        available.append(s.portstr)
        s.close()   # explicit close 'cause of delayed GC in java
      except serial.SerialException:
        pass
    #for i in range(4):
    #  try:
    #    s = serial.Serial("/dev/ttyUSB"+str(i))
    #    available.append(s.portstr)
    #    s.close()   # explicit close 'cause of delayed GC in java
    #  except serial.SerialException:
    #    pass
    #for i in range(4):
    #  try:
    #    s = serial.Serial("/dev/ttyd"+str(i))
    #    available.append(s.portstr)
    #    s.close()   # explicit close 'cause of delayed GC in java
    #  except serial.SerialException:
    #    pass
        
    return available
