import random

class ADXL345(object):
	def __init__(self):
		self.address = 0x53

	def getAxes(self, dummy):
		return { 'x': random.random()*2.0-1.0, 'y': random.random()*2.0-1.0, 'z': random.random()*2.0-1.0 }

 

