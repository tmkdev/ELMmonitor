#!/usr/bin/env python

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import sqlite3
import os
import adafruitlcd
from adxl345 import ADXL345
from button import TouchControl
import pygame

from obd_utils import scanSerial

class OBD_Capture():
    _FUEL_STATUS=3
    _LOAD=4
    _COOLTEMP=5
    _STFT1=6
    _LTFT1=7
    _STFT2=8
    _LTFT2=9
    _FUELPRES=10
    _MAP=11
    _RPM=12
    _SPEED=13
    _TIMING=14
    _IAT=15
    _MAF=16
    _TPS=17
    _SECONDARYAIR=18
    _O2B1S1=20
    _O2B1S2=21
    _O2B2S1=24
    _O2B2S2=25

    pidlist={ 'high': [    ("load", _LOAD),
                           ("rpm", _RPM),
                           ("speed", _SPEED),
                           ("maf", _MAF),
                           ("tps", _TPS),
                           ],
              'medium': [ ("manap", _MAP),
                          ("timing", _TIMING),
                          ("stft1", _STFT1),
                          ("stft2", _STFT2)
              ],
              'low': [   ("coolant", _COOLTEMP),
                         ("intakeair", _IAT),
                         ("ltft1", _LTFT1),
                         ("ltft2", _LTFT2)
              ]
    }
    o2pids = [ _O2B1S1, _O2B1S2, _O2B2S1, _O2B2S2, ]

    def __init__(self):
        self.port = None
        localtime = time.localtime(time.time())

        self.con = sqlite3.connect('obdlog.db')

        #Holders..
        self.o2vals = [0,0,0,0]
        self.values = {'load': 0, 'intakeair': 0, 'rpm': 0, 'manap': 0, 'coolant': 0, 'stft1': 0, 'stft2': 0, 'tps': 0, 'ltft2': 0, 'ltft1': 0,
                       'maf': 0, 'timing': 0, 'speed': 0}

        self.medcount=0
        self.lowcount=0
        self.starttime = -1
        self.lastdrag = 0


        self.gs = { 'minx': 0, 'maxx': 0, 'miny': 0, 'maxy': 0 }

        self.adxl345 = ADXL345()
        print "ADXL345 on address 0x%x:" % (self.adxl345.address)

        cur = self.con.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS obdlog (
                        tstamp INT,
                        load REAL,
                        cooltemp REAL,
                        stft1 REAL,
                        ltft1 REAL,
                        stft2 REAL,
                        ltft2 REAL,
                        map REAL,
                        rpm REAL,
                        speed REAL,
                        timing REAL,
                        iat REAL,
                        maf REAL,
                        tps REAL,
                        o2b1s1 REAL,
                        o2b1s2 REAL,
                        o2b2s1 REAL,
                        o2b2s2 REAL);""")

    def connect(self):
        self.port = obd_io.OBDPort('/dev/pts/3', None, 2, 2)

        if(self.port):
            print "Connected to " + self.port.port.name

    def is_connected(self):
        return self.port

    def renderoutput(self, outputs, color):
        #self.lcd.clear()
        self.lcd.setcolor(color)

        for row in enumerate(outputs):
            self.lcd.position( (1,row[0]+1) )
            self.lcd.write("{0:^16}".format(row[1]))

    def gmeter(self):
        outputs = ['','']
        axes = self.adxl345.getAxes(True)
        y = axes['z']
        x = axes['y']

	y = ( y - 0.408 ) / 0.9135

        self.gs['minx'] = min(self.gs['minx'], x)
        self.gs['maxx'] = max(self.gs['maxx'], x)
        self.gs['miny'] = min(self.gs['miny'], y)
        self.gs['maxy'] = max(self.gs['maxy'], y)

        #outputs[0]="{0:.2f} {1:+.2f} {2:.2f}".format(self.gs['minx'], x, self.gs['maxx'])
        #outputs[1]="{0:.2f} {1:+.2f} {2:.2f}".format(self.gs['miny'], y, self.gs['maxy'])

       	background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0,0,0))

	pygame.draw.circle(background, (255,255,255), (160,120), 50, 1)
	pygame.draw.circle(background, (128,128,128), (160,120), 100, 1)

	pygame.draw.circle(background, (255,255,0), (int(self.gs['minx']/2.0*100)+160, 120), 3)
	pygame.draw.circle(background, (255,255,0), (int(self.gs['maxx']/2.0*100)+160, 120), 3)

	pygame.draw.circle(background, (255,255,255), ( int(  (x/2.0)*100  )+160, int(  (y/2.0)*100  )+120 ), 6)
	pygame.draw.circle(background, (255,0,0), ( int(  (x/2.0)*100  )+160, int(  (y/2.0)*100  )+120 ), 4)


	pygame.draw.line(background, (255,0,0), ( int(  (x/2.0)*100  )+160, int(  (y/2.0)*100  )+120 ), (160,120), 3)


	background.blit( self._renderstring("Lat: {0:.2f}g".format(x), (255,255,255)), (5,5) )
	background.blit( self._renderstring("Long: {0:.2f}g".format(y), (255,255,255)), (5,30) )

        screen.blit(background, (0, 0))
        pygame.display.flip()

        time.sleep(0.2)

    def dragtime(self):
        outputs = ['', '']

        try:
            (name, value, unit) = self.port.sensor(self._SPEED)
            if value == 0:
                self.starttime = time.time()
                outputs[0] = "Ready for timing"
            if value > 0 and value < 96 and self.starttime > 0:
                outputs[0]="ET: {0:.1f}s".format(time.time() - self.starttime, value)

            if self.starttime == -1 and value != 0:
                outputs[0] = "Stop to Reset"

            if self.starttime > 0 and value > 96:
                self.lastdrag = time.time() - self.starttime
                self.starttime = -1

            outputs[1] = "{0:.1f}".format(self.lastdrag)

       	    background = pygame.Surface(screen.get_size())
            background = background.convert()
            background.fill((0,0,0))


            background.blit( self._rendertext(name.strip(), str(value), unit, (255,255,255)), (0,0) )
            background.blit( self._rendertext("Message", outputs[0], "", (255,255,255)), (0,48) )
            background.blit( self._rendertext("Last ET", outputs[1], "S", (255,255,255)), (160,48) )

            screen.blit(background, (0, 0))
            pygame.display.flip()

            time.sleep(0.1)

        except:
            print "Error in dragtime module"
            raise

    def o2scan(self):
        outputs = ['', '']

        try:
            for pid in enumerate(self.o2pids):
                (name, self.o2vals[pid[0]], unit) = self.port.sensor(pid[1])

            outputs[0] = "1 S1:{0:.1f} S2:{1:.1f}".format(self.o2vals[0], self.o2vals[1])
            outputs[1] = "2 S1:{0:.1f} S2:{1:.1f}".format(self.o2vals[2], self.o2vals[3])

            time.sleep(0.1)
            self.renderoutput(outputs, self.lcd._YELLOW)

        except:
            print "Error in o2scan.."
            raise

    def milage(self):
        outputs = ['', '']

        try:
            (name, speed, unit) = self.port.sensor(self._SPEED)
            (name, maf, unit) = self.port.sensor(self._MAF)
            (name, tps, unit) = self.port.sensor(self._TPS)

            speedmiles = int(speed * 0.621371)

            mpg = 7.107 * speed / maf

            outputs[0] = "MPG: {0:.1f}".format(mpg)
            outputs[1] = "{0:>3d}mph TPS:{1:.1f}%".format(speedmiles, tps)

            time.sleep(0.2)
            self.renderoutput(outputs, self.lcd._GREEN)

        except:
            print "Error in milage.."
            raise

    def info1(self):
        outputs = ['', '']
        color = self.lcd._MAGENTA

        try:
            (name, intakeair, unit) = self.port.sensor(self._IAT)
            (name, coolant, unit) = self.port.sensor(self._COOLTEMP)
            (name, maf, unit) = self.port.sensor(self._MAF)
            (name, manap, unit) = self.port.sensor(self._MAP)

            outputs[0] = "I:{0}C C:{1}C".format(intakeair, coolant)
            if intakeair > 75 or coolant > 95:
                color = self.lcd._RED

            outputs[1] = "MF:{0:.1f} MP:{1:.0f}".format(maf, manap)

            time.sleep(0.1)
            self.renderoutput(outputs, color)

        except:
            print "Error in milage.."
            raise

    def render(self, data):
        color = self.lcd._WHITE

        #{'load': 14.509803921568627, 'intakeair': -26, 'rpm': 5775, 'manap': 627.4131274131274, 'coolant': -27, 'stft1': 0.17, 'stft2': 0.18, 'tps': 16.07843137254902, 'ltft2': 0.095, 'ltft1': 0.085,
        #'maf': 12.71040084, 'timing': -48.0, 'speed': 37}
        outputs = ['', '']

        outputs[0] = "{0:>3d}kmh {1:>4d} RPM".format(data['speed'], data['rpm'])

        if data['intakeair'] > 75 or data['coolant'] > 95:
            outputs[1] = "I:{0}C C:{1}C".format(data['intakeair'], data['coolant'])
            color = self.lcd._RED
        elif abs(data['stft1']) > .12 or abs(data['stft2']) > .12:
            outputs[1] = "SF1:{0:.0%} SF2:{1:.0%}".format(data['stft1'], data['stft2'])
            color = self.lcd._YELLOW
        elif abs(data['ltft1']) > .10 or abs(data['ltft2']) > .10:
            outputs[1] = "LF1:{0:.0%} LF2:{1:.0%}".format(data['ltft1'], data['ltft2'])
            color = self.lcd._ORANGE
        elif data['load'] > 70:
            outputs[1] = "L:{0:.0f}% TP:{1:.0f}%".format(data['load'], data['tps'])
            color = self.lcd._CYAN
        else:
            outputs[1] = "TP:{0:.1f}% A:{1:.0f}D".format(data['tps'], data['timing'])

        self.renderoutput(outputs, color)

    def renderpygame(self, data):
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0,0,0))


        speedcolor = (255,0,0) if data['speed'] > 125 else (255,255,255)

        background.blit( self._rendertext("Speed", str(data['speed']), "KPH", speedcolor), (0,0) )
        background.blit( self._rendertext("Tach", str(data['rpm']), "RPM", (255,102,0) if data['rpm'] > 5000 else (255,255,255)), (160,0) )
        background.blit( self._rendertext("Coolant", str(data['coolant']), "C", (255,255,255)), (0,48) )
        background.blit( self._rendertext("Intake Air Temp", str(data['intakeair']), "C", (255,255,255)), (160,48) )
        background.blit( self._rendertext("STFT Bank1", str(data['stft1']), "%", (255,255,255)), (0,96) )
        background.blit( self._rendertext("STFT Bank2", str(data['stft2']), "%", (255,255,255)), (160,96) )
        background.blit( self._rendertext("LTFT Bank1", str(data['ltft1']), "%", (255,255,255)), (0,144) )
        background.blit( self._rendertext("LTFT Bank2", str(data['ltft2']), "%", (255,255,255)), (160,144) )
        background.blit( self._rendertext("Timing", str(data['timing']), "%", (255,255,255)), (0,192) )
        background.blit( self._rendertext("Throttle Pos", "{0:.1f}".format(data['tps']), "%", (255,255,255)), (160,192) )


        screen.blit(background, (0, 0))


        pygame.display.flip()

    def _rendertext(self, name, value, unit, color):
        gauge = pygame.Surface( (160,48) )
        gauge = gauge.convert()
        gauge.fill((0,0,0))

        pygame.draw.line(gauge, (128,128,128), [0, 25], [160,25], 2)

        font = pygame.font.Font(None,28)

        text = font.render(value, 1, color )
        gauge.blit(text, (4,3) )

        text = font.render(unit, 1, color )
        gauge.blit(text, (115,3) )

        text = font.render(name, 1, (128,128,128) )
        gauge.blit(text, (4, 26))

        pygame.draw.rect(gauge, (255,255,255), [0,0, 160,48], 1)

        return gauge

    def _renderstring(self, string, color):
        font = pygame.font.Font(None,28)
        text = font.render(string, 1, color )

	return text


    def capture_data(self):
        cur = self.con.cursor()
        #Loop until Ctrl C is pressed
        try:
            for pid in self.pidlist['high']:
                (name, value, unit) = self.port.sensor(pid[1])
                self.values[pid[0]] = value

            if self.medcount==0:
                for pid in self.pidlist['medium']:
                    (name, value, unit) = self.port.sensor(pid[1])
                    self.values[pid[0]] = value

            if self.lowcount==0:
                for pid in self.pidlist['low']:
                    (name, value, unit) = self.port.sensor(pid[1])
                    self.values[pid[0]] = value

            time.sleep(0.1)

            self.renderpygame(self.values)

            self.medcount +=1
            self.lowcount +=1

            if self.medcount > 5: self.medcount = 0
            if self.lowcount > 13: self.lowcount = 0

            #data =  (int(time.time()), load, cooltemp, stft1, ltft1, stft2, ltft2, manap, rpm, speed, timing, iat, maf, tps, o2b1s1, o2b1s2, o2b2s1, o2b2s2)
            #print data

            #sql = """INSERT INTO obdlog ( tstamp, load, cooltemp, stft1, ltft1, stft2, ltft2, map, rpm, speed, timing, iat, maf, tps, o2b1s1, o2b1s2, o2b2s1, o2b2s2 )
            #        VALUES
            #        ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? );"""

            #cur.execute(sql, data)
            #self.con.commit()

            #time.sleep(0.5)

        except KeyboardInterrupt:
            print("stopped")
            raise

if __name__ == "__main__":
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV'      , '/dev/fb1')
    os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
    os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

    pygame.init()
    screen = pygame.display.set_mode((320,240))

    o = OBD_Capture()
    o.connect()
    time.sleep(3)

    if not o.is_connected():
        print "ELM Not connected - exiting now"
        exit(0)

    displays = [ o.capture_data, o.dragtime, o.gmeter ]

    curdisplay = 0

    try:
        while True:
            bp = '0'
            if bp == '1':
                curdisplay += 1
                if curdisplay == len(displays): curdisplay = 0
            if bp == '4':
                curdisplay -= 1
                if curdisplay == -1 : curdisplay = len(displays)-1
            displays[curdisplay]()

	    for event in pygame.event.get():
        	if event.type == pygame.MOUSEBUTTONDOWN:
            	    print event.pos
        	if event.type == pygame.QUIT:
            	    done = True



    except KeyboardInterrupt:
        print "Bye.. "

