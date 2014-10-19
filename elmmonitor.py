#!/usr/bin/env python

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import os
import pygame
import sys
from obd_utils import scanSerial
from collections import deque

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
    _SPEEDMPH=33

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

    scanpids = [  _SPEED, _SPEEDMPH, _RPM, _IAT, _COOLTEMP, _LOAD, _TIMING,  _MAF, _MAP, _TPS ]

    def __init__(self):
        self.port = None
        localtime = time.localtime(time.time())

        #Holders..
        self.o2vals = [0,0,0,0]
        self.values = {'load': 0, 'intakeair': 0, 'rpm': 0, 'manap': 0, 'coolant': 0, 'stft1': 0, 'stft2': 0, 'tps': 0, 'ltft2': 0, 'ltft1': 0,
                       'maf': 0, 'timing': 0, 'speed': 0}

        self.medcount=0
        self.lowcount=0



    def connect(self):
        #self.port = obd_io.OBDPort('/dev/pts/{0}'.format(portnumber), None, 2, 2)
        portnames = ['/dev/obd0', '/dev/obd1', '/dev/pts/2', '/dev/pts/3', '/dev/pts/4', '/dev/pts/1', '/dev/pts/9']


        for port in portnames:
            self.port = obd_io.OBDPort(port, None, 2, 2)
            if(self.port.State == 0):
                self.port.close()
                self.port = None
            else:
                break

        try:
            if(self.port):
                print "Connected to " + self.port.port.name
        except:
            pass

    def is_connected(self):
        return self.port


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

    def capture_data(self):
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


            self.medcount +=1
            self.lowcount +=1

            if self.medcount > 5: self.medcount = 0
            if self.lowcount > 13: self.lowcount = 0

            time.sleep(0.1)
            return self.values

        except KeyboardInterrupt:
            print("stopped")
            raise

class Gauges(object):
    UPEVENT = 1
    DOWNEVENT = 2

    def __init__(self, obd, adxl):
        self.obd = obd
        self.adxl345 = adxl
        self.startTime = -1
        self.lastdrag = 0

        self.gs = { 'minx': 0, 'maxx': 0, 'miny': 0, 'maxy': 0 }
        self.glist = deque([], 10)
        self.o2b1s1list = deque([], 320)
        self.o2b1s2list = deque([], 320)
        self.o2b2s1list = deque([], 320)
        self.o2b2s2list = deque([], 320)

        self._hugger = (245, 124, 51)

        self.face = pygame.image.load('gauges/bg.png')
        self.scanpidindex = 0



    def gtoc(self, gpoint):
        return ( int(  (gpoint[0]/2.0)*100  )+160, int(  (gpoint[1]/2.0)*100  )+120 )

    def o2toc(self, voltage):
        return int( ( 1.275 - voltage ) * (240/1.275) )

    def nodata2zeros(self, value):
        if value == "NODATA":
            return (0,0)
        return value

    def o2graph(self, event=None):
        (name, value1, unit) = self.obd.port.sensor(self.obd._O2B1S1)
        (name, value2, unit) = self.obd.port.sensor(self.obd._O2B1S2)
        (name, value3, unit) = self.obd.port.sensor(self.obd._O2B2S1)
        (name, value4, unit) = self.obd.port.sensor(self.obd._O2B2S2)

        value1 = self.nodata2zeros(value1)
        value2 = self.nodata2zeros(value2)
        value3 = self.nodata2zeros(value3)
        value4 = self.nodata2zeros(value4)

        self.o2b1s1list.append(self.o2toc(value1[0]))
        self.o2b1s2list.append(self.o2toc(value2[0]))
        self.o2b2s1list.append(self.o2toc(value3[0]))
        self.o2b2s2list.append(self.o2toc(value4[0]))

        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0,0,0))

        rich = self.o2toc(0.8)
        mid = self.o2toc(0.45)
        lean = self.o2toc(0.1)

        background.blit( self._renderstring("0.8V", (0,0,128)), (5,rich-20) )
        background.blit( self._renderstring("0.45V", (128,128,128)), (5,mid-20) )
        background.blit( self._renderstring("0.1V", (128,0,0)), (5,lean-20) )

        pygame.draw.line(background, (128,128,128), (0,mid), (320,mid), 2)
        pygame.draw.line(background, (128,0,0), (0,lean), (320,lean), 2)
        pygame.draw.line(background, (0,0,128), (0,rich), (320,rich), 2)

        background.blit( self._renderstring("B1S1: {0:.2f}V".format(value1[0]), self._hugger), (5,5) )
        background.blit( self._renderstring("B1S2: {0:.2f}V".format(value2[0]), (255,0,0)), (5,25) )
        background.blit( self._renderstring("B2S1: {0:.2f}V".format(value3[0]), (0,0,255)), (165,5) )
        background.blit( self._renderstring("B2S2: {0:.2f}V".format(value4[0]), (255,0,255)), (165,25) )


        if len(self.o2b1s1list) > 1:
            pygame.draw.lines(background, self._hugger, False, list(enumerate(self.o2b1s1list)), 2 )
        if len(self.o2b1s2list) > 1:
            pygame.draw.lines(background, (255,0,0), False, list(enumerate(self.o2b1s2list)) , 2 )
        if len(self.o2b2s1list) > 1:
            pygame.draw.lines(background, (0,0,255), False, list(enumerate(self.o2b2s1list)) , 2 )
        if len(self.o2b2s2list) > 1:
            pygame.draw.lines(background, (255,0,255), False, list(enumerate(self.o2b2s2list)) , 2 )

        screen.blit(background, (0, 0))
        pygame.display.flip()


    def gmeter(self, event=None):
        outputs = ['','']
        axes = self.adxl345.getAxes(True)
        y = axes['z']
        x = axes['x']

        y = ( y - 0.408 ) / 0.9135

        self.glist.append( self.gtoc( (x,y) ) )

        self.gs['minx'] = min(self.gs['minx'], x)
        self.gs['maxx'] = max(self.gs['maxx'], x)
        self.gs['miny'] = min(self.gs['miny'], y)
        self.gs['maxy'] = max(self.gs['maxy'], y)

        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0,0,0))

        pygame.draw.circle(background, (255,255,255), (160,120), 50, 3)
        pygame.draw.circle(background, (128,128,128), (160,120), 12, 1)
        pygame.draw.circle(background, (128,128,128), (160,120), 25, 1)
        pygame.draw.circle(background, (128,128,128), (160,120), 38, 1)
        pygame.draw.circle(background, (64,64,64), (160,120), 62, 1)
        pygame.draw.circle(background, (64,64,64), (160,120), 75, 1)
        pygame.draw.circle(background, (64,64,64), (160,120), 88, 1)
        pygame.draw.circle(background, self._hugger, (160,120), 100, 2)

        pygame.draw.circle(background, (255,255,0), (int(self.gs['minx']/2.0*100)+160, 120), 3)
        pygame.draw.circle(background, (255,255,0), (int(self.gs['maxx']/2.0*100)+160, 120), 3)
        pygame.draw.circle(background, (255,255,0), (160, int(self.gs['miny']/2.0*100)+120), 3)
        pygame.draw.circle(background, (255,255,0), (160, int(self.gs['maxy']/2.0*100)+120), 3)

        if len(self.glist) > 1:
            pygame.draw.lines(background, self._hugger, False, self.glist)

        pygame.draw.circle(background, (255,255,255), self.gtoc( (x,y) ), 6)
        pygame.draw.circle(background, (255,0,0), self.gtoc( (x,y) ), 4)

        pygame.draw.line(background, (255,0,0), ( int(  (x/2.0)*100  )+160, int(  (y/2.0)*100  )+120 ), (160,120), 3)

        background.blit( self._renderstring("X: {0:.2f}".format(x), (255,255,255)), (10,210) )
        background.blit( self._renderstring("Y: {0:.2f}".format(y), (255,255,255)), (250,210) )
        background.blit( self._renderstring("{0:.2f}".format(self.gs['minx']), (255,255,255)), (10,110) )
        background.blit( self._renderstring("{0:.2f}".format(self.gs['maxx']), (255,255,255)), (270,110) )
        background.blit( self._renderstring("{0:.2f}".format(self.gs['miny']), (255,255,255)), (140,1) )
        background.blit( self._renderstring("{0:.2f}".format(self.gs['maxy']), (255,255,255)), (140,220) )


        screen.blit(background, (0, 0))
        pygame.display.flip()


        time.sleep(0.2)

    def biggauge(self, event=None):
        if event == self.UPEVENT:
            self.scanpidindex += 1
        if event == self.DOWNEVENT:
            self.scanpidindex -= 1

        self.scanpidindex %= len(self.obd.scanpids)

        (name, value, unit) = self.obd.port.sensor(self.obd.scanpids[self.scanpidindex])

        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.blit( self.face, (0,0) )

        smallfont = pygame.font.Font(None,35)
        font = pygame.font.Font(None,60)

        speed = smallfont.render(name.strip(), 1, (255,255,255) )
        speedrect = speed.get_rect()
        speedrect.centerx = screen.get_rect().centerx
        speedrect.centery = 100

        background.blit(speed, speedrect)

        if value == "NODATA":
            svalue = font.render("NO DATA", 1, (255,255,255) )
        else:
            svalue = font.render("{0:.0f} {1}".format(value, unit), 1, (255,255,255) )

        svaluerect = svalue.get_rect()
        svaluerect.centerx = screen.get_rect().centerx
        svaluerect.centery = 150

        background.blit( svalue, svaluerect )

        screen.blit(background, (0, 0))
        pygame.display.flip()


        time.sleep(0.1)

    def milage(self, event=None):
        (name, speed, unit) = self.obd.port.sensor(self.obd._SPEED)
        (name, maf, unit) = self.obd.port.sensor(self.obd._MAF)

        if speed != "NODATA" and maf != "NODATA" and maf > 0:
            speedmiles = int(speed * 0.621371)
            mpg = int(7.107 * speed / maf)
        else:
            speedmiles = "NODATA"
            mpg = "NODATA"

        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.blit( self.face, (0,0) )

        font = pygame.font.Font(None,60)

        speed = font.render("{0}mph".format(speedmiles), 1, (255,255,255) )
        speedrect = speed.get_rect()
        speedrect.centerx = screen.get_rect().centerx
        speedrect.centery = 60

        background.blit(speed, speedrect)

        if mpg < 15:
            color = (255,64,64)
        else:
            color = (64,255,64)

        svalue = font.render("{0}mpg".format(mpg), 1, color )
        svaluerect = svalue.get_rect()
        svaluerect.centerx = screen.get_rect().centerx
        svaluerect.centery = 120

        background.blit( svalue, svaluerect )

        svalue = font.render("{0}mpg".format(mpg), 1, color )
        svaluerect = svalue.get_rect()
        svaluerect.centerx = screen.get_rect().centerx
        svaluerect.centery = 170

        background.blit( svalue, svaluerect )


        screen.blit(background, (0, 0))
        pygame.display.flip()


        time.sleep(0.1)

    def maindisplay(self, event=None):
        vals = self.obd.capture_data()

        self.renderpygame(vals)

    def renderpygame(self, data):
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((0,0,0))


        speedcolor = (255,0,0) if data['speed'] > 125 else (255,255,255)

        background.blit( self._rendertext("Speed", str(data['speed']), "KPH", speedcolor), (10,0) )
        background.blit( self._rendertext("Tach", str(data['rpm']), "RPM", (255,102,0) if data['rpm'] > 5000 else (255,255,255)), (160,0) )
        background.blit( self._rendertext("Coolant", str(data['coolant']), "C", (255,255,255)), (10,48) )
        background.blit( self._rendertext("Intake Air Temp", str(data['intakeair']), "C", (255,255,255)), (160,48) )
        background.blit( self._rendertext("STFT Bank1", "{:.1f}".format( self.nodata2zeros( data['stft1'] ) ), "%", (255,255,255)), (10,96) )
        background.blit( self._rendertext("STFT Bank2", "{:.1f}".format( self.nodata2zeros( data['stft2'] ) ), "%", (255,255,255)), (160,96) )
        background.blit( self._rendertext("LTFT Bank1", "{:.1f}".format( self.nodata2zeros( data['ltft1'] ) ), "%", (255,255,255)), (10,144) )
        background.blit( self._rendertext("LTFT Bank2", "{:.1f}".format( self.nodata2zeros( data['ltft2'] ) ), "%", (255,255,255)), (160,144) )
        background.blit( self._rendertext("Timing", str(data['timing']), "Deg", (255,255,255)), (10,192) )
        background.blit( self._rendertext("Throttle Pos", self._floatText(data['tps']), "%", (255,255,255)), (160,192) )

        screen.blit(background, (0, 0))

        pygame.display.flip()

    def dragTime(self, event):
        outputs = ['', '']

        try:
            (name, value, unit) = self.obd.port.sensor(self.obd._SPEED)
            if value == 0:
                self.startTime = time.time()
                outputs[0] = "Ready!"
            if value > 0 and value < 96 and self.startTime > 0:
                outputs[0]="ET: {0:.1f}s".format(time.time() - self.startTime, value)

            if self.startTime == -1 and value != 0:
                outputs[0] = "Stop to Reset"

            if self.startTime > 0 and value > 96:
                self.lastdrag = time.time() - self.startTime
                self.startTime = -1

            outputs[1] = "{0:.1f}".format(self.lastdrag)

            background = pygame.Surface(screen.get_size())
            background = background.convert()
            background.fill((0,0,0))


            background.blit( self._rendertext(name.strip(), str(value), unit, (255,255,255)), (10,48) )
            background.blit( self._rendertext("Message", outputs[0], "", (255,255,255)), (10,96) )
            background.blit( self._rendertext("Last ET", outputs[1], "S", (255,255,255)), (160,96) )

            screen.blit(background, (0, 0))
            pygame.display.flip()

            time.sleep(0.1)

        except:
            print "Error in dragtime module"
            raise


    def _floatText(self, float):
        if float == "NODATA":
            return float
        else:
            return "{0:.1f}".format(float)

    def _rendertext(self, name, value, unit, color):
        gauge = pygame.Surface( (150,48) )
        gauge = gauge.convert()
        gauge.fill((0,0,0))

        pygame.draw.line(gauge, (128,128,128), [0, 25], [150,25], 2)

        font = pygame.font.Font(None,28)

        text = font.render(value, 1, color )
        gauge.blit(text, (4,3) )

        text = font.render(unit, 1, color )
        gauge.blit(text, (100,3) )

        text = font.render(name, 1, (128,128,128) )
        gauge.blit(text, (4, 26))

        pygame.draw.rect(gauge, (255,255,255), [0,0, 150,48], 1)

        return gauge

    def _renderstring(self, string, color):
        font = pygame.font.Font(None,28)
        text = font.render(string, 1, color )

        return text


if __name__ == "__main__":
    debug = False
    if sys.argv[1] == 'debug':
        debug = True

    if debug:
        from adxlmock import ADXL345

    if not debug:
        from adxl345 import ADXL345
        os.putenv('SDL_VIDEODRIVER', 'fbcon')
        os.putenv('SDL_FBDEV'      , '/dev/fb1')
        os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
        os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

    myADXL = ADXL345()

    pygame.init()
    screen = pygame.display.set_mode((320, 240))

    o = OBD_Capture()
    o.connect()
    time.sleep(2)

    try:
        if not o.is_connected():
            print "ELM Not connected - exiting now"
            exit(1)
    except:
        pass

    mygauges = Gauges(o, myADXL)

    displays = [ mygauges.maindisplay, mygauges.dragTime, mygauges.gmeter, mygauges.biggauge, mygauges.o2graph, mygauges.milage ]
    curdisplay = 3

    try:
        while True:
            gaugeevent = None

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    print event.pos
                    if event.pos[0] < 110:
                        curdisplay -= 1
                    elif event.pos[0] > 210:
                        curdisplay += 1
                    else:
                        if event.pos[1] < 160:
                            gaugeevent = Gauges.UPEVENT
                        else:
                            gaugeevent = Gauges.DOWNEVENT

                    if event.type == pygame.QUIT:
                        done = True

                curdisplay %= len(displays)

            displays[curdisplay](event=gaugeevent)

    except KeyboardInterrupt:
        print "Bye.. "

