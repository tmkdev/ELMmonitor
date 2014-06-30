import serial
import re

class TouchControl():
	repress=re.compile("B([0-9])_1")

	def __init__(self, port):
		self.port = serial.Serial(port, 9600, timeout=0.05)

	
	def getlast(self):
		last = False
	
		for line in self.port:
			ui=self.repress.match(line)
			if ui:
				last = ui.group(1)

		return last

if __name__ == "__main__":
	mytouch = TouchControl('/dev/ttyUSB1')
	
	while True:
		last = mytouch.getlast()

		if last: print last
