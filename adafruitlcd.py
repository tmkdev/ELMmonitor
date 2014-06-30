from serial import Serial
import time

class Adafruitlcd(Serial):
	_RED = (255,0,0)
	_GREEN = (0,255,0)
	_BLUE = (0,0,255)
	_YELLOW = (255,160,0)
	_ORANGE = (255,60,0)
	_CYAN = (0,255,255)
	_MAGENTA = (255,0,255)
	_WHITE = (255,160,215)

	def __init__(self, *args, **kwargs):
		Serial.__init__(self, *args, **kwargs)

	def sendcommand(self, command):
		self.write(chr(0xFE))
		self.write(chr(command))

	def clear(self):
		self.sendcommand(0x58)
		time.sleep(0.1)

	def setcolor(self, color):
		self.sendcommand(0xD0)
		self.write( chr(color[0]) )
		self.write( chr(color[1]) )
		self.write( chr(color[2]) )

	def backlighton(self):
		self.sendcommand(0x42)
		self.write(chr(0)) 
		time.sleep(0.1)

	def backlightoff(self):
		self.sendcommand(0x46)
		time.sleep(0.1)

	def autoscrolloff(self):
		self.sendcommand(0x52)
		time.sleep(0.1)

	def autoscrollon(self):
		self.sendcommand(0x51)
		time.sleep(0.1)

	def brightness(self, level):
		self.sendcommand(0x98)
		self.write( chr(level) )	
		time.sleep(0.1)

	def contrast(self, level):
		self.sendcommand(0x50)
		self.write( chr(level) )	
		time.sleep(0.1)

	def position(self, coords):
		self.sendcommand(0x47)
		self.write(chr(coords[0]))
		self.write(chr(coords[1]))

if __name__ == "__main__":
	ml = Adafruitlcd(port='/dev/ttyACM0')
	ml.clear()

	ml.setcolor( ml._ORANGE )
	ml.write("Hello!")

	ml.backlightoff()
	time.sleep(1)

	ml.backlighton()
	time.sleep(1)

	for i in xrange(0,255, 10):
		ml.brightness(i)

	ml.clear()
	ml.position( (1,1) )
	ml.write("Line 1")

	ml.position( (1,2) )
	ml.write("Line 2")

	time.sleep(0.1)

	for color in [ ml._RED, ml._ORANGE,  ml._GREEN, ml._BLUE, ml._YELLOW, ml._CYAN, ml._MAGENTA, ml._WHITE ]:
		ml.setcolor( color )
		time.sleep(2)

	ml.close()

