#!/usr/bin/env python

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import sys

class serialPlot:
  def __init__(self, serialPort, serialBaud, plotLength, dataNumBytes):
    self.port = serialPort
    self.baud = serialBaud
    self.dataNumBytes = dataNumBytes
    self.rawData = bytearray(dataNumBytes)
    self.data = collections.deque([], maxlen=plotLength)
    self.isRun = True
    self.isReceiving = False
    self.thread = None
    self.plotTimer = 0
    self.previousTimer = 0

    print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
    try:
      self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
      print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
    except:
      sys.exit("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')

  def readSerialStart(self):
    if self.thread == None:
      self.thread = Thread(target=self.backgroundThread)
      self.thread.start()
      # Block till we start receiving values
      while self.isReceiving != True:
        time.sleep(0.1)

  def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
    currentTimer = time.perf_counter()
    self.plotTimer = int((currentTimer - self.previousTimer) * 1000)  # the first timer reading will be erroneous
    self.previousTimer = currentTimer
    timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
    value = struct.unpack('f', self.rawData)[0]
    self.data.append(value)  # we get the latest data point and append it to our array
    lines.set_data(range(len(self.data)), self.data)
    lineValueText.set_text('[' + lineLabel + '] = ' + str(value))

  def backgroundThread(self):  # retrieve data continuously
    time.sleep(1.0)  # give some buffer time for retrieving data
    self.serialConnection.reset_input_buffer()
    while (self.isRun):
      self.serialConnection.readinto(self.rawData)
      self.isReceiving = True

  def close(self):
    self.isRun = False
    self.thread.join()
    self.serialConnection.close()
    print('Disconnected')

def main():
  portName = '/dev/ttyS3'
  baudRate = 38400
  maxPlotLength = 100
  dataNumBytes = 4  # number of bytes of 1 data point, Arduino float = 4 bytes
  s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)   # initializes all required variables
  s.readSerialStart()                                               # starts background thread

  # plotting starts below
  pltInterval = 50    # Period at which the plot animation updates [ms]
  xmin, xmax = (0, maxPlotLength)
  ymin, ymax = (-5, 5)
  fig = plt.figure()
  ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))  # extra range for y values
  ax.set_title('ESP32 + MPU 6050 Read')
  ax.set_xlabel("time")
  ax.set_ylabel("X Acceleration")
  lineLabel = 'a'
  lines = ax.plot([], [], label=lineLabel)[0]
  lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)  # position text
  timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
  anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)
  plt.legend(loc="upper left")
  plt.show()

  s.close()

if __name__ == '__main__':
  main()
