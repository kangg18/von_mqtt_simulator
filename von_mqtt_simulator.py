import sys
import glob
import serial
import serial.tools.list_ports
import _winreg as winreg
import itertools
import serial, time, datetime, optparse, signal
from time import gmtime, strftime
from Tkinter import *
import binascii
import tempfile, shutil
from Tkinter import Tk
from tkFileDialog import askopenfilename
from tkinter import messagebox
import sys
import os
import msvcrt as m
from shutil import copyfile
import struct
import requests
import urllib2
import hashlib

from datetime import datetime
try:
    import tkinter as tk  # for python 3
except:
    import Tkinter as tk  # for python 2
import pygubu

from pygubu.builder import ttkstdwidgets

import csv
import paho.mqtt.client as mqtt
import webbrowser
import threading

import jsonpickle
import folium

from numpy import arange, sin, pi
import numpy as np
from numpy.random import randn
import numpy

# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.mlab import normpdf
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation


class VONMqttProtocol:
	pass

VONMqttProtocol

VONMqttProtocol.MQTT_PUB_TYPE_JSON_TDR =1 
VONMqttProtocol.MQTT_PUB_TYPE_JSON_TRIP =2
VONMqttProtocol.MQTT_PUB_TYPE_JSON_GPS_HELLO =4  
VONMqttProtocol.MQTT_PUB_TYPE_JSON_NETWORK_HELLO =5

VONMqttProtocol.MQTT_PUB_TYPE_JSON_FW_REQUEST=6 
VONMqttProtocol.MQTT_PUB_TYPE_JSON_CARDB_REQUEST=7


VONMqttProtocol.MQTT_RPC_CMD_JSON_RESET ="reset"
VONMqttProtocol.MQTT_RPC_CMD_JSON_BEEP = "beep" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_SERIAL = "serial" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_TDR ="gettdr" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_TRIP ="gettrip" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_RUSAGE ="getrusage" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_STOPPUSH ="stoppush" 
VONMqttProtocol.MQTT_RPC_CMD_JSON_VINFO ="getVinfo" 
VONMqttProtocol.MQTT_RPC_CMD_FW_CHUNK ="sendfwchunk"
VONMqttProtocol.MQTT_RPC_CMD_CARDB_CHUNK ="sendcardbchunk"
VONMqttProtocol.MQTT_RPC_CMD_GET_SECURITY_LEVEL ="getSecuritylevel" 
VONMqttProtocol.MQTT_RPC_CMD_SET_SECURITY_LEVEL ="setSecuritylevel" 	
VONMqttProtocol.MQTT_RPC_CMD_CLEAR_ALL_DATA ="clearAllData" 	
VONMqttProtocol.MQTT_RPC_CMD_GET_GPS_KEY ="getGPSKey" 
VONMqttProtocol.MQTT_RPC_CMD_SEND_UPDATE_INFO ="sendUpdateInfo" 
VONMqttProtocol.MQTT_RPC_CMD_GET_DEVICE_INFO ="getDeviceInfo"

class MQTTLogViewr:
	def __init__(self, master):
		self.builder = builder = pygubu.Builder()
		
		
		builder.add_from_file('mqtt_log_viewer.ui')
		
		self.mainwindow = builder.get_object('Toplevel_1', master)
		
		# get objects
		self.logBox = builder.get_object('logBox', master)
		self.yscrollbar = builder.get_object('yscrollbar', master)
		
		# assign scrollbar to text widget
		#<property name="yscrollcommand">yscrollbar.set</property>
		#<property name="command">logBox.yview</property>
		
		self.logBox['yscrollcommand'] = self.yscrollbar.set
		self.yscrollbar['command'] = self.logBox.yview
		
		# set some text for test
		#for x in range(20):
		#	self.logBox.insert('end', '\nHello World!')
		builder.connect_callbacks(self)

	def pushlog(self ,tag , s ):
	
		self.logBox.insert('end', " tag: " + s )		
		


class MeanInterPolator:
	
	def __init__(self, from_value, to_value,iterateNum):
		self.movingValue=[]
		delta  = (to_value - from_value) / (iterateNum*1.0)
		#print "from_value, to_value ", from_value, to_value, iterateNum,delta
		for i in range(0,iterateNum):

			interPolValue = from_value + (delta*i)
			#print "MeanInterPolator interPolValue =  " ,interPolValue
			self.movingValue.append(interPolValue)
			 

	def getValue(self):
		if len(self.movingValue)>0:
				aValue = self.movingValue[0]
				self.movingValue.remove(aValue)
				return aValue
		return None

class VehicleSimulator:

	def __init__(self,upperapp,tripinfo,driveSecList, periodic,fastfw_factor):
		self.tripInfo = tripinfo
	 	self.driveSecList = driveSecList
	 	self.driveSecIndex = 0
	 	self.sleepTime = periodic 
	 	self.periodic = periodic
	 	self.stop = False
		self.upperapp  = upperapp
		self.fastfw_factor = fastfw_factor
	def goNextSlice(self):
		if (len(self.driveSecList)-self.driveSecIndex) <= 2 :
				return None 
		else:
			self.driveSecIndex = self.driveSecIndex +1
			return   self.driveSecList[self.driveSecIndex], self.driveSecList[self.driveSecIndex+1] 


	def doLoop(self):

		self.progressTime = 0 



		self.upperapp.updateUIState(True)

		while self.stop==False:
			a = self.goNextSlice() 
			if a ==None:
				break 
		
			
			self.ahead = a[0]
			self.next = a[1]
			#build 	MeanInterPolator array 
			
			print "self.ahead ", self.ahead 
			print  "self.next ", self.next 


			time_gap = self.next.ts - self.ahead.ts   
			self.iteratorNum = int((time_gap/self.periodic)/self.fastfw_factor) 

			if self.iteratorNum ==0 :
				self.iteratorNum=1

			print "time_gap", time_gap,"self.iteratorNum " , self.iteratorNum
			rpmArray  = MeanInterPolator(self.ahead.rpm,self.next.rpm,self.iteratorNum)
			
			speedArray = MeanInterPolator(self.ahead.speed, self.next.speed,self.iteratorNum)
			latArray  =MeanInterPolator(self.ahead.lat, self.next.lat,self.iteratorNum)
			lonArray  =MeanInterPolator(self.ahead.lon, self.next.lon,self.iteratorNum)
			
			distancerray  =MeanInterPolator(self.ahead.distance, self.next.distance,self.iteratorNum)
			fcArray  =MeanInterPolator(self.ahead.fc, self.next.fc,self.iteratorNum)
			tpsArray  =MeanInterPolator(self.ahead.tps, self.next.tps,self.iteratorNum)
			engLoadArray  =MeanInterPolator(self.ahead.engload, self.next.engload,self.iteratorNum)
			engTempArray  =MeanInterPolator(self.ahead.engTemp, self.next.engTemp,self.iteratorNum)
			fuelSrray  =MeanInterPolator(self.ahead.fuelS, self.next.fuelS,self.iteratorNum)
			bVoltArray  =MeanInterPolator(self.ahead.bVolt, self.next.bVolt,self.iteratorNum)

			courseArray  =MeanInterPolator(self.ahead.course, self.next.course,self.iteratorNum)
			axArray  =MeanInterPolator(self.ahead.acc_xy, self.next.acc_xy,self.iteratorNum)
			asArray  =MeanInterPolator(self.ahead.yaw_rot, self.next.yaw_rot,self.iteratorNum)
			

			normDriveSec=   self.driveSecList[self.driveSecIndex-1]

			for x in range(0,self.iteratorNum):
				aDrvisec  = DriveSecMarshall()
				aDrvisec.ts =int(time.time())
				aDrvisec.tid= normDriveSec.tid
				aDrvisec.rpm= int(rpmArray.getValue())
				
				aDrvisec.speed=int(speedArray.getValue())
				aDrvisec.lat=int(latArray.getValue())
				aDrvisec.lon=int(lonArray.getValue())
				
				aDrvisec.distance=int(distancerray.getValue())
				aDrvisec.fc=int(fcArray.getValue())
				aDrvisec.tps=int(tpsArray.getValue())
				aDrvisec.engload=int(engLoadArray.getValue())
				aDrvisec.engTemp=int(engTempArray.getValue())
				aDrvisec.fuelS=int(fuelSrray.getValue())
				aDrvisec.bVolt=int(bVoltArray.getValue())
		
				aDrvisec.course=int(courseArray.getValue())
				aDrvisec.gVal=normDriveSec.gVal
				aDrvisec.acc_xy=int(axArray.getValue())
				aDrvisec.yaw_rot=int(asArray.getValue())
				
				aDrvisec.s_mark=0
				


				#print self.app

				if hasattr(self.upperapp,'drawDynamics'):
				 	print "self.progressTime ",self.progressTime, "aDrvisec.speed " , aDrvisec.speed
					self.upperapp.drawDynamics.push_speed_point(self.progressTime,aDrvisec.speed)
				

				self.upperapp.save_gps_line_and_marker_html((aDrvisec.lat/100000.0,aDrvisec.lon/100000.0))
		


					
				if  x == (self.iteratorNum-1) :
					  aDrvisec.s_mark= normDriveSec.s_mark

				self.progressTime = self.progressTime  + self.sleepTime*self.fastfw_factor

				time.sleep(self.sleepTime)
			


				self.upperapp.updateUITime(self.progressTime)


				aDriveSecJosn = JsonMQTTMarshall()
				aDriveSecJosn.ts = aDrvisec.ts 
				aDriveSecJosn.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_TDR 
				aDriveSecJosn.payload = aDrvisec

				frozen = jsonpickle.encode(aDriveSecJosn,unpicklable=False)
				print  "frozen " , frozen

				if hasattr(self.upperapp,'theMQTT'):
					if self.upperapp.isSendable_TDR():
						self.upperapp.theMQTT.publish(frozen)
					else:
						print "No isSendable_TDR Cleint"
				else:
					print "No Mqtt Cleint"
			
				 
			print 	"self.driveSecIndex" , self.driveSecIndex ,"len(self.driveSecList) ",len(self.driveSecList)
			if  self.driveSecIndex+2 == (len(self.driveSecList)):
					aTrip = TripMarshall()
					
					
					aTrip.tid =self.tripInfo.tid 
					aTrip.stime =self.tripInfo.stime 
					aTrip.etime=self.tripInfo.etime 
					aTrip.iTime=self.tripInfo.iTime 
					aTrip.rTime=self.tripInfo.rTime 
					aTrip.fCutTime=self.tripInfo.fCutTime 
					aTrip.ecoTime=self.tripInfo.ecoTime 
					aTrip.accelTime=self.tripInfo.accelTime 
					aTrip.oSpeedTime=self.tripInfo.oSpeedTime 
					aTrip.warmTime=self.tripInfo.warmTime 

					#sudden mark 
					aTrip.sudden_mark_accel=self.tripInfo.sudden_mark_accel 
					aTrip.sudden_mark_decel=self.tripInfo.sudden_mark_decel 
					
					#fc
					aTrip.fcMass=self.tripInfo.fcMass 
					aTrip.fcEffi=self.tripInfo.fcEffi 

					#speed 
					aTrip.avgSpeed=self.tripInfo.avgSpeed 
					aTrip.maxSpeed=self.tripInfo.maxSpeed 
					aTrip.max_accel=self.tripInfo.max_accel 
					aTrip.max_decel=self.tripInfo.max_decel 
					aTrip.max_rot=self.tripInfo.max_rot 

					#co2
					aTrip.co2PerKm=self.tripInfo.co2PerKm 
					aTrip.co2Mass=self.tripInfo.co2Mass 

					aTrip.dtcType =self.tripInfo.dtcType 
					aTrip.dtcCode =self.tripInfo.dtcCode 
					
					#vehicle 
					aTrip.engTempMax=self.tripInfo.engTempMax
					aTrip.tpsMax=self.tripInfo.tpsMax

					#gps 
					aTrip.h_lat=self.tripInfo.h_lat 
					aTrip.h_lon=self.tripInfo.h_lon 
					aTrip.t_lat=self.tripInfo.t_lat 
					aTrip.t_lon=self.tripInfo.t_lon

					aTripJson = JsonMQTTMarshall()
					aTripJson.ts = aDrvisec.ts 
					aTripJson.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_TRIP 
					aTripJson.payload = aTrip
					frozen = jsonpickle.encode(aTripJson,unpicklable=False)
					print  "frozen " , frozen
					if hasattr(self.upperapp,'theMQTT'):
						if self.upperapp.isSendable_Trip():
							self.upperapp.theMQTT.publish(frozen)
						else:
							print "No isSendable_Trip Cleint"
					else:
						print "No Mqtt Cleint"
			


			if self.stop == True:
					print "Scn Stop "
					break 
		
		print "Scn Stop ======"
		self.upperapp.updateUIState(False)


class DrawDynamics:
	


	def __init__(self, master):
	
		#1: Create a builder
		self.builder = builder = pygubu.Builder()
	
		#2: Load an ui file
		builder.add_from_file('von_mqtt_simulator_dynamics.ui')
		self.mainwindow = builder.get_object('Toplevel_1', master)
		self.LabelSpeed =  builder.get_object('LabelSpeed', self.mainwindow)
		self.LabelAccel =  builder.get_object('LabelAccel', self.mainwindow)
		self.LabelAngularSpeed =  builder.get_object('LabelAngularSpeed', self.mainwindow)

		self.fig_speed = Figure(figsize=(9, 3), dpi=100)
		self.fig_accel = Figure(figsize=(9, 3), dpi=100)
		self.fig_as = Figure(figsize=(9, 3), dpi=100)
		
		self.ax_speed = self.fig_speed.add_subplot(111)
		self.ax_accel = self.fig_accel.add_subplot(111)
		self.ax_as = self.fig_as.add_subplot(111)
		self.speedRealtime = [] 
		
		
	def drawTest(self):	
		x = np.arange(0, 2*np.pi, 0.01)

		line1, = self.ax_speed.plot(x, np.sin(x))
		line2, = self.ax_accel.plot(x, np.sin(x))
		line3, = self.ax_as.plot(x, np.sin(x))
		
		self.canvas_speed = FigureCanvasTkAgg(self.fig_speed, self.LabelSpeed)
		self.canvas_speed.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		self.canvas_speed.show()


		self.canvas_accel = FigureCanvasTkAgg(self.fig_accel, self.LabelAccel)
		self.canvas_accel.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		self.canvas_accel.show()
		
		
		self.canvas_as = FigureCanvasTkAgg(self.fig_as, self.LabelAngularSpeed)
		self.canvas_as.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		self.canvas_as.show()
	
	def push_speed_point(self,time,speed):
		print "push_speed_point ", time, speed
		self.speedRealtime = (time,speed)
	def update_speed_point(self,n):
		#print "update_speed_point ", self.speedRealtime[0], self.speedRealtime[1]
		self.speedpoint.set_data(self.speedRealtime[0],self.speedRealtime[1])
		return self.speedpoint
		
	def drawDynmaics(self,timeArray,speedArray,acceArray,AngularSpeedArray,updateInterval):
	


		
		self.timeArray = timeArray
		self.speedArray = speedArray

		print "drawDynmaics" , timeArray
		self.ax_speed.set_title('Speed')
		self.ax_speed.set_ylabel('Km/s')
		self.ax_speed.set_xlim((timeArray[0],timeArray[-1]))
		self.speedpoint, = self.ax_speed.plot(timeArray[0], speedArray[0], 'o')
		self.speedRealtime = (timeArray[0], speedArray[0])
		line1, = self.ax_speed.plot(timeArray, speedArray)
		self.canvas_speed = FigureCanvasTkAgg(self.fig_speed, self.LabelSpeed)
		self.canvas_speed.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		ani=animation.FuncAnimation(self.fig_speed, self.update_speed_point, updateInterval)


		self.canvas_speed.show()

		self.index =0
				
		self.ax_accel.set_title('Accelration ')
		self.ax_accel.set_ylabel('G')
		self.ax_accel.set_xlim((timeArray[0],timeArray[-1]))
		line2, = self.ax_accel.plot(timeArray, acceArray)
		self.canvas_accel = FigureCanvasTkAgg(self.fig_accel, self.LabelAccel)
		self.canvas_accel.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		self.canvas_accel.show()
		

		self.ax_as.set_title('AnularSpeed')
		self.ax_as.set_ylabel('deg/s')
		self.ax_as.set_xlim((timeArray[0],timeArray[-1]))
		line3, = self.ax_as.plot(timeArray, AngularSpeedArray)
		self.canvas_as = FigureCanvasTkAgg(self.fig_as, self.LabelAngularSpeed)
		self.canvas_as.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
		self.canvas_as.show()
		


class MQTTClient:

	#gKoCfu9KBbdNRPBRIV1u
	#Na8OgKvsIPLkq5oUqUXB
	#zviaMOywlHeBYJD5kD0u
	def __init__(self,app):
		
		self.sendingTopic = 'v1/devices/me/telemetry'
		self.rpcReqTopic = 'v1/devices/me/rpc/request/+'
		self.rpcResTopic = 'v1/devices/me/rpc/response/'
		self.updateInterval = 20
		self.serverAddress = '223.39.121.158'
		self.userName = ' '
		self.userPwd = ' '
		self.securityLEvel = 0
		self.client_id = "A000001"
		self.uppaerapp = app
		self.isConneced = False
	
	def do_connect(self) :
		self.mqttc = mqtt.Client(client_id = self.client_id)
		self.mqttc.on_message = self.on_message
		self.mqttc.on_connect = self.on_connect
		self.mqttc.on_publish = self.on_publish
		self.mqttc.on_subscribe = self.on_subscribe
		self.mqttc.loop_start()
		self.mqttc.username_pw_set('gKoCfu9KBbdNRPBRIV1u',password=None)
		self.mqttc.connect(self.serverAddress, 1883, self.updateInterval)
		self.mqttc.subscribe(self.rpcResTopic, 0)
	def publish(self,payload):
		if self.isConneced == True:
			self.mqttc.publish(self.rpcResTopic,payload)
			if hasattr(self.uppaerapp, 'mqttLogViwer'):
					self.uppaerapp.mqttLogViwer.pushlog("pub "  , self.sendingTopic + "   payload : " +  payload +"\r\n" )

	def response(self,reqid,payload):
		if self.isConneced == True:
			self.mqttc.publish(self.rpcResTopic+str(reqid) ,payload)
			if hasattr(self.uppaerapp, 'mqttLogViwer'):
					self.uppaerapp.mqttLogViwer.pushlog("response "  , self.rpcResTopic+reqid  + "   payload : " +  payload +"\r\n" )

	def on_connect(self,mqttc, obj, flags, rc):
		print("on_connect rc: " + str(rc))
		self.isConneced = True
	def on_message(self,mqttc, obj, msg):
		print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
		if hasattr(self.uppaerapp, 'mqttLogViwer'):
					self.uppaerapp.mqttLogViwer.pushlog("sub "  , self.rpcReqTopic +  "   payload : " + payload +"\r\n" )

	def on_publish(self,mqttc, obj, mid):
		print("mid: " + str(mid))
	def on_subscribe(self,mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))
	def on_log(self,mqttc, obj, level, string):
		print(string)	
	def __del__(self):	
		self.mqttc.disconnect()

class ResultMarshall(object): 
	def __init__(self):
		self.results="0"
		self.additionalInfo={}


class NetworkHelloMarshall(object): 
	def __init__(self):
		self.network_id=0
		self.fw_version=0
		self.complied_version=0
		self.cardb_name=0
		self.obd2_supported_result=0



class JsonMQTTMarshall(object):
	def __init__(self):
		self.ts  =0 
		self.type  =0 
		self.payload =None

class GPSHelloMarshall(object): 
	def __init__(self):
		self.lat=0
		self.lon=0
		self.time_zone_shift=0

	
class FWRequestMarshall(object): 
	def __init__(self):
		self.network_id=0
		self.device_id=0
		self.fw_version=0
		self.complied_version=0
		self.cardb_name=0
		self.obd2_supported_result=0

class CarDBRequest(object): 
	def __init__(self):
		self.network_id=0
		self.device_id=0
		self.cardb_name=0
		self.obd2_supported_result=0


class DriveSecMarshall(object): 
	def __init__(self):
		self.ts =0
		self.tid=0
		self.rpm=0
		self.speed=0
		self.distance=0
		self.fc=0
		self.tps=0
		self.engload=0
		self.engTemp=0
		self.fuelS=0
		self.bVolt=0
		self.lat=0
		self.lon=0
		self.course=0
		self.gVal=0
		self.acc_xy=0
		self.yaw_rot=0
		self.s_mark=0
		self.encoded=0
	def __str__(self):
		s = ""
		s = s + str(self.ts) + ": " 
		s = s + str(self.tid) + ": " 
		s = s + str(self.rpm) + ": " 
		s = s + str(self.speed) + ": " 
		s = s + str(self.distance) + ": " 
		s = s + str(self.tps) + ": " 
		s = s + str(self.engload) + ": " 
		s = s + str(self.engTemp) + ": " 
		s = s + str(self.fuelS) + ": " 
		s = s + str(self.bVolt) + ": " 
		s = s + str(self.lat) + ": " 
		s = s + str(self.lon) + ": " 
		s = s + str(self.course) + ": " 
		s = s + str(self.gVal) + ": " 
		s = s + str(self.acc_xy) + ": " 
		s = s + str(self.yaw_rot) + ": " 
		s = s + str(self.s_mark) + ": " 
		return s 

class RUsageMarshall(object): 
	def __init__(self):
		self.stime =0
		self.etime =0
		self.sent=0
		self.receved=0
		#time 
class VehicleInfo(object): 
	def __init__(self):
		self.modelcode =0
		self.cylNo =0
		self.vol =0
		self.fuel =0
		self.hybrid=0
		self.vin =""
		#time 

class TripMarshall(object): 
	def __init__(self):
		#time 
		self.tid =0
		self.stime =0
		self.etime=0
		self.iTime=0
		self.rTime=0
		self.fCutTime=0
		self.ecoTime=0
		self.accelTime=0
		self.oSpeedTime=0
		self.warmTime=0
		self.distance=0

		#sudden mark 
		self.sudden_mark_accel=0
		self.sudden_mark_decel=0
		self.sudden_mark_rot=0
		self.max_accel=0
		self.max_decel=0
		self.max_rot=0

		#fc
		self.fcMass=0
		self.fcEffi=0

		#speed 
		self.avgSpeed=0
		self.maxSpeed=0

		#co2
		self.co2PerKm=0
		self.co2Mass=0

		self.dtcType =0
		self.dtcCode =0
		
		#vehicle 
		self.engTempMax=0
		self.tpsMax=0

		#gps 
		self.h_lat=0
		self.h_lon=0
		self.t_lat=0
		self.t_lon=0

class DriveSecManager:
	drvSecList=[]
	def __init__(self):
		pass
	
	def loadFromFile(self, path):
		self.drvSecList=[]
		f = open(path, 'r')
		rdr = csv.reader(f)
		for line in rdr:
			print line[0]
			if (line[0].isdigit()) == True:
				drvSec = DriveSecMarshall()
				drvSec.ts= int(line[0])
				drvSec.tid=int(line[1])
				drvSec.rpm=int(line[2])
				drvSec.speed=int(line[3])
				drvSec.distance=int(line[4])
				drvSec.fc=int(line[5])
				drvSec.tps=int(line[6])
				drvSec.engload=int(line[7])
				drvSec.engTemp=int(line[8])
				drvSec.fuelS=int(line[9])
				drvSec.bVolt=int(line[10])
				drvSec.lat=int(line[11])
				drvSec.lon=int(line[12])
				drvSec.course=int(line[13])
				drvSec.gVal=int(line[14])
				drvSec.acc_xy=float(line[15])
				drvSec.yaw_rot=float(line[16])
				drvSec.s_mark=int(line[17])
				#print(line)
				self.drvSecList.append(drvSec)
		
		f.close() 
		return 	self.drvSecList			
		pass
		



class TripInfo(TripMarshall):
	id =0
	start_time =0
	end_time =0
	duration = 0
	distance=0
	fuel_consumption=0


	sudden_mark_point = [] 
	gps_shadow_zone_point = []
	geo_location_list=[]
	drvSecList=[]
	timeArray = [] 
	speedArray=[]
	accelArray=[]
	asArray=[]
	def __init__(self):
		TripMarshall.__init__(self)
		pass

	def __str__(self):
		s =  'start_time  %d, end_time %d , distance %d \r\n ' % (self.start_time, self.end_time, self.distance)
		s =  s +  "sudden_mark_point:" + str(self.sudden_mark_point) + "\r\n"
		s =  s +  "gps_shadow_zone_point:" + str(self.gps_shadow_zone_point) + "\r\n"
		
		return s

class Scenario:
	tripList=[]

	def __init__(self):
		pass
		
		
	def pick_trip(self,drvSecList):
		# find trip
		driving_start_time = 0
		driving_end_time = 0
		index = 0
		startDriveSec = drvSecList[0]
		strt_id = startDriveSec.tid 
		print "driving start_time", startDriveSec.ts
		
	
		tripInfo = TripInfo()
		tripInfo.drvSecList.append(startDriveSec)	
		


		speedMax = 0
		aceel_max = 0
		decel_max = 10
		rot_max = 0
		engTempMax = 0 
		tpsMax = 0 
		

		for driveSec in drvSecList:
			#print driveSec	
			index=index+1		
				
			driving_end_time = driveSec.ts
			if strt_id != driveSec.tid:
				print "driving_end_time", driveSec.ts
				drvSecList.remove(driveSec)						
				break 		
			
			tripInfo.distance = tripInfo.distance+ driveSec.distance
			tripInfo.fcMass= tripInfo.fcMass+ driveSec.fc
			
			
			tripInfo.id = driveSec.tid
			
			if driveSec.s_mark !=0:
				tripInfo.sudden_mark_point.append((driveSec.ts,driveSec.lat,driveSec.lon,driveSec.s_mark  ))
			
			if driveSec.gVal ==0:
				tripInfo.gps_shadow_zone_point.append((driveSec.ts,driveSec.lat,driveSec.lon ))	

			if driveSec.gVal ==1:
				tripInfo.geo_location_list.append((driveSec.ts,driveSec.lat,driveSec.lon ))
			
			tripInfo.drvSecList.append(driveSec)

			tripInfo.timeArray.append(driveSec.ts-startDriveSec.ts)
			print "driveSec.ts", driveSec.ts, " startDriveSec.ts", startDriveSec.ts, " diff",driveSec.ts-startDriveSec.ts
			tripInfo.speedArray.append(driveSec.speed)		
			tripInfo.accelArray.append(driveSec.acc_xy)		
			tripInfo.asArray.append(driveSec.yaw_rot)		
			tripInfo.end_time = driveSec.ts 
			speedMax = max([speedMax,driveSec.speed])

			if driveSec.acc_xy> 0:
				aceel_max = max([aceel_max,driveSec.acc_xy])

			if driveSec.acc_xy < 0:
				decel_max = min([decel_max,driveSec.acc_xy])

			rot_max = max([rot_max,driveSec.yaw_rot])

			engTempMax = max([engTempMax,driveSec.engTemp])
			tpsMax = max([tpsMax,driveSec.tps])

			if tripInfo.sudden_mark_point ==1 :
				tripInfo.sudden_mark_accel = tripInfo.sudden_mark_accel+1
			if tripInfo.sudden_mark_point ==2 :
				tripInfo.sudden_mark_decel = tripInfo.sudden_mark_decel+1
			if tripInfo.sudden_mark_point ==3 :
				tripInfo.sudden_mark_rot = tripInfo.sudden_mark_rot+1

		for aa in range(0, index):
			drvSecList.pop()
		
		#aalysiz  
		
		
		tripInfo.start_time = startDriveSec.ts
	
		




		tripInfo.tid =strt_id
		tripInfo.stime =startDriveSec.ts
		tripInfo.etime=driveSec.ts
		tripInfo.duration = tripInfo.etime - tripInfo.stime 

		tripInfo.iTime=0    # implmented in Real Device 
		tripInfo.rTime=0    # implmented in Real Device 
		tripInfo.fCutTime=0 # implmented in Real Device 
		tripInfo.ecoTime=0  # implmented in Real Device 
		tripInfo.accelTime=0 # implmented in Real Device 
		tripInfo.oSpeedTime=0 # implmented in Real Device 
		tripInfo.warmTime=0 # implmented in Real Device 

		#sudden mark 
		
		#fc

		tripInfo.fcMass=tripInfo.fcMass
		tripInfo.fcMass=tripInfo.fcMass/(tripInfo.duration*1.0)

		#speed 
		tripInfo.distance = driveSec.distance
		tripInfo.avgSpeed=driveSec.distance/tripInfo.duration*1.0
		tripInfo.maxSpeed=speedMax
		tripInfo.max_accel = aceel_max
		tripInfo.decel_max = decel_max
		tripInfo.max_rot =rot_max

		tripInfo.engTempMax = engTempMax
		tripInfo.tpsMax = tpsMax
		#co2
		tripInfo.co2PerKm=0 # implmented in Real Device 
		tripInfo.co2Mass=0  # implmented in Real Device 

		tripInfo.dtcType ='e' # implmented in Real Device 
		tripInfo.dtcCode = 'P0101'  # implmented in Real Device 
		
		#vehicle 
		tripInfo.engTempMax=0

		#gps 
		aStartPos = tripInfo.geo_location_list[0]
		aEndPos= tripInfo.geo_location_list[-1]
	
		tripInfo.h_lat=aStartPos[1]
		tripInfo.h_lon=aStartPos[2]
		tripInfo.t_lat=aEndPos[1]
		tripInfo.t_lon=aEndPos[2]

		
		print "drvSecList len", len(drvSecList)
		print  "tripInfo", tripInfo
		
		
		return tripInfo 
		
	
	def analyze(self,drvSecList):
		
		print "drvSecList len", len(drvSecList)
		tripInfoList = []
		while len(drvSecList)!=0:
			tripInfo = self.pick_trip(drvSecList)
			tripInfoList.append(tripInfo)		
					
		return 	tripInfoList	
		pass



class Application:
	ser=None
	dvp=0
	filename=0 
	
	def __init__(self, master):
	
		#1: Create a builder
		self.master = master 
		self.builder = builder = pygubu.Builder()
	
		#2: Load an ui file
		builder.add_from_file('./von_mqtt_simulator.ui')
		#3: Create the widget using a master as parent
		self.mainwindow = builder.get_object('von_mqtt_simulator_dlg', master)
		


		builder.connect_callbacks(self)
		
		self.ChkTDR = builder.get_object('ChkTDR', self.mainwindow)
		self.ChkTrip = builder.get_object('ChkTrip', self.mainwindow)
		self.ChkTDR.select()
		self.ChkTrip.select()

		self.comboProtocol = builder.get_object('comboProtocol', self.mainwindow)
		self.comboProtocol['values'] =["skt_v1"]
		self.comboProtocol.current(0)
		
		self.comboAuthMethod = builder.get_object('comboAuthMethod', self.mainwindow)
		self.comboAuthMethod['values'] =["skt_without_password"]
		self.comboAuthMethod.current(0)

		
		#aa = "{\"method\":\"reset\",\"params\":{\"Immediate\":\"true\"}}"
		#print aa
		#thawed = jsonpickle.decode(aa)
		#print (thawed['params'])['Immediate']

	def isSendable_TDR(self): 
		builder = self.builder
		#print "builder.get_variable()" , builder.get_variable('varTDR').get()
		if int(builder.get_variable('varTDR').get())==1:
			return True 
		else:
			return False
		 

	def isSendable_Trip(self): 
		builder = self.builder
		if int(builder.get_variable('varTrip').get())==1:
			return True 
		return False

	


	def on_connect_mqtt_clicked(self):
		#frozen = jsonpickle.encode(DriveSecMarshall(),unpicklable=False)
		#print frozen
		builder = self.builder
		self.txtServerAddress = builder.get_object('txtServerAddress', self.mainwindow).get()
		self.txtUserID = builder.get_object('txtUserID', self.mainwindow).get() 
		self.txtPushTocken = builder.get_object('txtPushTocken', self.mainwindow).get() 
		self.txtSubToken = builder.get_object('txtSubToken', self.mainwindow).get() 
		self.txtRespToken =  builder.get_object('txtRespToken', self.mainwindow).get() 
		self.txtRespToken =  builder.get_object('txtRespToken', self.mainwindow).get() 
		self.txtDeviceSerail =  builder.get_object('txtDeviceSerail', self.mainwindow).get()


		self.theMQTT = MQTTClient(self)

		self.theMQTT.sendingTopic = self.txtPushTocken
		self.theMQTT.rpcReqTopic = self.txtSubToken
		self.theMQTT.rpcResTopic = self.txtRespToken
		self.theMQTT.serverAddress = self.txtServerAddress
		self.client_id = self.txtDeviceSerail 

		self.theMQTT.do_connect()


	def tripChoosed(self, object):
		builder = self.builder
		id =  self.comboTripList.get()
		
		ATrip = 0 
		for trip  in self.tripInfoList:
			if trip.id == int(id):
				ATrip = trip
				break 
				
		
		self.txtTotalProgressTime = builder.get_object('txtTotalProgressTime', self.mainwindow)
		self.txtSimulState = builder.get_object('txtSimulState', self.mainwindow)
		
		self.txtStartTime = builder.get_object('txtStartTime', self.mainwindow)
		self.txtStartTime.delete(0, END)
		self.txtStartTime.insert(0, ATrip.start_time)
		
		
	
		
		
		
		
		#ATrip.distance

		aStartPos = ATrip.geo_location_list[0]
		aEndPos= ATrip.geo_location_list[-1]
	
		
		self.txtEndtime = builder.get_object('txtEndtime', self.mainwindow)
		self.txtEndtime.delete(0, END)
		self.txtEndtime.insert(0, ATrip.end_time)
		
		self.txtDuration = builder.get_object('txtDuration', self.mainwindow)
		self.txtDuration.delete(0, END)
		self.txtDuration.insert(0, ATrip.duration)
		
		print aStartPos
		s = str(aStartPos[1]) +  ','+ str(aStartPos[2])
		
		self.txtStartPos = builder.get_object('txtStartPos', self.mainwindow)
		self.txtStartPos.delete(0, END)
		self.txtStartPos.insert(0, s)
		
		s = str(aEndPos[1]) +  ','+ str(aEndPos[2])
		self.txtEndPos = builder.get_object('txtEndPos', self.mainwindow)
		self.txtEndPos.delete(0, END)
		self.txtEndPos.insert(0, s)
		
		
		self.txtFCO = builder.get_object('txtFCO', self.mainwindow)
		self.txtFCO.delete(0, END)
		self.txtFCO.insert(0, ATrip.fuel_consumption)
		
		
		
		self.txtDistance = builder.get_object('txtDistance', self.mainwindow)
		self.txtDistance.delete(0, END)
		self.txtDistance.insert(0, ATrip.distance)
		
		

		self.txtEngineTemp = builder.get_object('txtEngineTemp', self.mainwindow)
		self.txtEngineTemp.delete(0, END)
		self.txtEngineTemp.insert(0, ATrip.engTempMax)
		

		self.txtMaxThrottlePosition = builder.get_object('txtMaxThrottlePosition', self.mainwindow)
		self.txtMaxThrottlePosition.delete(0, END)
		self.txtMaxThrottlePosition.insert(0, ATrip.tpsMax)

		
		
		self.txtMaxThrottlePosition = builder.get_object('txtMaxThrottlePosition', self.mainwindow)

		self.txtMaxThrottlePosition.delete(0, END)
		self.txtMaxThrottlePosition.insert(0, ATrip.maxSpeed)


		self.txtMaxAccel = builder.get_object('txtMaxAccel', self.mainwindow)	
		self.txtMaxAccel.delete(0, END)
		self.txtMaxAccel.insert(0, ATrip.max_accel)

		self.txtMaxDeccel = builder.get_object('txtMaxDeccel', self.mainwindow)	
		self.txtMaxDeccel.delete(0, END)
		self.txtMaxDeccel.insert(0, ATrip.max_decel)

		self.txtMaxAS = builder.get_object('txtMaxAS', self.mainwindow)	
		self.txtMaxAS.delete(0, END)
		self.txtMaxAS.insert(0, ATrip.max_rot)
	
		pass
		
	
	def update_sc_result(self, tripInfoList):
		
		builder = self.builder
		self.comboTripList = builder.get_object('comboTripList', self.mainwindow)
		
		tripListName=[]
		for trip  in self.tripInfoList:
			tripListName.append(trip.id)
		
		self.comboTripList['values'] = tripListName
		
		self.comboTripList.bind('<<ComboboxSelected>>', self.tripChoosed)

		
		self.comboTripList.current(0)
		self.tripChoosed(None)
	
		
		pass
	
	def	on_quit_button_clicked(self):
		if hasattr(self,'vs'):
			self.vs.stop = True
		root.destroy()
		exit()
    	pass

	def on_scn_stop_button_clicked(self):
		
		self.vs.stop = True 

	def on_scn_start_button_clicked(self):


		id =  self.comboTripList.get()
		
		ATrip = 0 
		for trip  in self.tripInfoList:
			if trip.id == int(id):
				ATrip = trip
				break 

	
		builder = self.builder
		self.txtSendingInterval = builder.get_object('txtSendingInterval', self.mainwindow).get()
		self.txtFFTimes = builder.get_object('txtFFTimes', self.mainwindow).get()
		flInterval = float(self.txtSendingInterval )
		ffw = int(self.txtFFTimes )
		self.vs =  VehicleSimulator(self,ATrip,ATrip.drvSecList,flInterval,ffw)
		self.vs.stop = False
		t = threading.Thread(target=self.vs.doLoop)
		t.start()


	def on_view_dynamics_button_clicked(self):
		

		self.drawDynamics = DrawDynamics(root) 


		id =  self.comboTripList.get()
		
		ATrip = 0 
		for trip  in self.tripInfoList:
			if trip.id == int(id):
				ATrip = trip
				break 

		self.dynamicUpdateInterval = 1000
		self.drawDynamics.drawDynmaics(ATrip.timeArray,ATrip.speedArray,ATrip.accelArray,ATrip.asArray,
			self.dynamicUpdateInterval)

		pass


	def on_view_mqtt_event_clicked(self):

		self.mqttLogViwer = MQTTLogViewr(root) 


		pass


	def save_gps_line_and_marker_html(self, geolocaltion):
		id =  self.comboTripList.get()
		
		ATrip = 0 
		for trip  in self.tripInfoList:
			if trip.id == int(id):
				ATrip = trip
				break 

		coordinates=[]
		
		for geoLoc in ATrip.geo_location_list:
			lat = geoLoc[1]/100000.0
			lon = geoLoc[2]/100000.0
			coordinates.append([lat,lon])

		#print coordinates

		#print "save_gps_line_and_marker_html geolocations", geolocaltion
		if geolocaltion==None:
			geolocaltion=(0,0)
			geoLoc = ATrip.geo_location_list[0]
			lat = geoLoc[1]/100000.0
			lon = geoLoc[2]/100000.0
			geolocaltion= (lat,lon)


		# Create the map and add the line
		m = folium.Map(location=[geolocaltion[0], geolocaltion[1]], zoom_start=14)
		my_PolyLine=folium.PolyLine(locations=coordinates,weight=5)
		
		folium.CircleMarker(location=[geolocaltion[0], geolocaltion[1]], radius=20,
                    popup='Laurelhurst Park', color='#3186cc',
                    fill_color='#3186cc').add_to(m)
		m.add_child(my_PolyLine)
		m.save('line_example_newer.html')

		pass

	def on_view_gps_track_clicked(self):

		self.save_gps_line_and_marker_html(None)
 		webbrowser.open('outerFrame.html')
		pass
		
	def on_scn_select_button_clicked(self):
		dsecMgr = DriveSecManager()
		scenario = Scenario() 
		
		builder = self.builder
		fwPath=None
		if fwPath ==None:
			Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
			fwPath = askopenfilename() # show an "Open" dialog box and return the path to the selected file
			print(fwPath)
			text= builder.get_object('txtScenarioPath', self.mainwindow)
			text.delete(0, END)
			text.insert(0, fwPath)
			
		drvSecList = dsecMgr.loadFromFile(fwPath)
		self.tripInfoList =  scenario.analyze(drvSecList)
		self.update_sc_result(self.tripInfoList)
		
		
	

		pass


	def updateUITime(self,progressTime):

		builder = self.builder
		self.txtTotalProgressTime = builder.get_object('txtTotalProgressTime', self.mainwindow)
		
		self.txtTotalProgressTime.delete(0, END)
		self.txtTotalProgressTime.insert(0, progressTime)
	
		pass

	def updateUIState(self,actState):

		builder = self.builder
		self.txtSimulState = builder.get_object('txtSimulState', self.mainwindow)
		if actState == False:
			self.txtSimulState.delete(0, END)
			self.txtSimulState.insert(0, "stopped")
		if actState == True:
			self.txtSimulState.delete(0, END)
			self.txtSimulState.insert(0, "started")
		pass

	def on_send_gps_hello_button_clicked(self):
		jSon = JsonMQTTMarshall()
		gpsHello = GPSHelloMarshall() 

		jSon.ts = int(time.time()) 

		gpsHello.lat=3754839
		gpsHello.lon=12710136
		gpsHello.time_zone_shift=9*60

		jSon.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_GPS_HELLO
		jSon.payload = gpsHello


		frozen = jsonpickle.encode(jSon,unpicklable=False)
		print  "frozen " , frozen

		if hasattr(self,'theMQTT'):
			self.theMQTT.publish(frozen)
		pass


	def on_send_network_hello_button_clicked(self):
		jSon = JsonMQTTMarshall()
		Hello = GPSHelloMarshall() 

		jSon.ts = int(time.time()) 

		Hello.network_id="A000001"
		Hello.fw_version="vonsimul-01.01"
		Hello.complied_version="2017/01/06"
		Hello.cardb_name="CombinedFileEncrypt 10001 PERMANENT DTC"
		Hello.obd2_supported_result="FF01FF01"

		jSon.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_NETWORK_HELLO
		jSon.payload = Hello
		frozen = jsonpickle.encode(jSon,unpicklable=False)
		print  "frozen " , frozen

		if hasattr(self,'theMQTT'):
			self.theMQTT.publish(frozen)
		pass

		

	def on_send_fw_request_button_clicked(self):
		jSon = JsonMQTTMarshall()
		req = GPSHelloMarshall() 


		req.network_id="A000001"
		req.device_id="A000001"
		req.fw_version="vonsimul-01.01"
		req.complied_version="2017/01/06"
		req.cardb_name="CombinedFileEncrypt 10001 PERMANENT DTC"
		req.obd2_supported_result="FF01FF01"

		jSon.ts = int(time.time()) 

		

		jSon.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_FW_REQUEST
		jSon.payload = req
		frozen = jsonpickle.encode(jSon,unpicklable=False)
		print  "frozen " , frozen

		if hasattr(self,'theMQTT'):
			self.theMQTT.publish(frozen)
		pass

		pass

	def on_send_cardb_request_button_clicked(self):
		jSon = JsonMQTTMarshall()
		req = CarDBRequest() 


		req.network_id="A000001"
		req.device_id="A000001"
		req.cardb_name="CombinedFileEncrypt 10001 PERMANENT DTC"
		req.obd2_supported_result="FF01FF01"

		jSon.ts = int(time.time()) 

		jSon.type =VONMqttProtocol.MQTT_PUB_TYPE_JSON_FW_REQUEST
		jSon.payload = req
		frozen = jsonpickle.encode(jSon,unpicklable=False)
		print  "frozen " , frozen

		if hasattr(self,'theMQTT'):
			self.theMQTT.publish(frozen)
		pass

		
	
	def on_from_server_reset_button_clicked(self):

		aa = "{\"method\":\"reset\",\"params\":{\"Immediate\":\"true\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
		

		response_id = '1' 
		aREsult = ResultMarshall()
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_RESET:
			self.theMQTT.response(response_id,resp)
		

	'''
	VONMqttProtocol.MQTT_RPC_CMD_JSON_RESET ="reset"
	VONMqttProtocol.MQTT_RPC_CMD_JSON_BEEP = "beep" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_SERIAL = "serial" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_TDR ="gettdr" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_TRIP ="gettrip" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_RUSAGE ="getrusage" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_STOPPUSH ="stoppush" 
	VONMqttProtocol.MQTT_RPC_CMD_JSON_VINFO ="getVinfo" 
	VONMqttProtocol.MQTT_RPC_CMD_FW_CHUNK ="sendfwchunk"
	VONMqttProtocol.MQTT_RPC_CMD_CARDB_CHUNK ="sendcardbchunk"
	VONMqttProtocol.MQTT_RPC_CMD_GET_SECURITY_LEVEL ="getSecuritylevel" 
	VONMqttProtocol.MQTT_RPC_CMD_SET_SECURITY_LEVEL ="setSecuritylevel" 	
	VONMqttProtocol.MQTT_RPC_CMD_CLEAR_ALL_DATA ="clearAllData" 	
	VONMqttProtocol.MQTT_RPC_CMD_GET_GPS_KEY ="getGPSKey" 
	VONMqttProtocol.MQTT_RPC_CMD_SEND_UPDATE_INFO ="sendUpdateInfo" 
	VONMqttProtocol.MQTT_RPC_CMD_GET_DEVICE_INFO ="getDeviceInfo"
	'''

		
	def on_from_server_beep_button_clicked(self):

		aa = "{\"method\":\"beep\"}"
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_BEEP:
			self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_serial_button_clicked(self):

		aa = "{\"method\":\"serial\"}"
		print aa
		thawed = jsonpickle.decode(aa)
		
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['serial']="A00001"
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_SERIAL:
			self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_gettdr_button_clicked(self):

		aa = "{\"method\":\"gettdr\",\"params\":{\"lastoffset\":\"-1\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
	

		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['tdr']=DriveSecMarshall()
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_TDR:
			self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_gettrip_button_clicked(self):

		aa = "{\"method\":\"gettrip\",\"params\":{\"lastoffset\":\"-1\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
		
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['trip']=TripMarshall()
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp


		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_TRIP:
			self.theMQTT.response(response_id,resp)



		pass



	def on_from_server_getrusage_button_clicked(self):

		aa = "{\"method\":\"getrusage\",\"params\":{\"from\":\"2016-07-31\",\"to\":\"2017-07-31\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
	

		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['rusage']=RUsageMarshall()
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_RUSAGE:
			self.theMQTT.response(response_id,resp)



		pass



	def on_from_server_stoppush_button_clicked(self):

		aa = "{\"method\":\"stoppush\"}"
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_STOPPUSH:
			self.theMQTT.response(response_id,resp)



		pass
	def on_from_server_getVinfo_button_clicked(self):

		aa = "{\"method\":\"getVinfo\"}"
		print aa
		thawed = jsonpickle.decode(aa)
	
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['vinfo']=VehicleInfo()
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_JSON_VINFO:
				self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_sendfwchunk_button_clicked(self):

		aa = "{\"method\":\"sendfwchunk\",\"params\":{\"total_size\":512348,\"chunk_size\":128,\"chunk_index\":1,\"payload\":\"MFIXX23\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
	

		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_FW_CHUNK:
			self.theMQTT.response(response_id,resp)



		pass
	def on_from_server_sendcardbchunk_button_clicked(self):

		
		aa = "{\"method\":\"sendcardbchunk\",\"params\":{\"total_size\":512348,\"chunk_size\":128,\"chunk_index\":1,\"payload\":\"MFIXX23\"}}"
		
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_CARDB_CHUNK:
			self.theMQTT.response(response_id,resp)



		pass


	def on_from_server_getSecuritylevel_button_clicked(self):

		aa = "{\"method\":\"getSecuritylevel\"}"
		print aa
		sampleResponse={}
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse['level']=1
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_GET_SECURITY_LEVEL:
			self.theMQTT.response(response_id,resp)



		pass


	def on_from_server_setSecuritylevel_button_clicked(self):

		aa = "{\"method\":\"setSecuritylevel\",\"params\":{\"level\":\"1\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_SET_SECURITY_LEVEL:
			self.theMQTT.response(response_id,resp)



		pass


	def on_from_server_clearAllData_button_clicked(self):

		aa = "{\"method\":\"clearAllData\"}"
		print aa
		thawed = jsonpickle.decode(aa)
		
		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp

		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_CLEAR_ALL_DATA:
			self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_getGPSKey_button_clicked(self):

		aa = "{\"method\":\"getGPSKey\"}"
		print aa
		thawed = jsonpickle.decode(aa)
		sampleResponse ={}
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse['gpskey']="AXSDM4354545DFDFDFDFDFDFDF"
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_GET_GPS_KEY:
			self.theMQTT.response(response_id,resp)



		pass

	def on_from_server_sendUpdateInfo_button_clicked(self):

		aa = "{\"method\":\"sendUpdateInfo\",\"params\":{\"type\":\"fw\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		aREsult.additionalInfo = ""
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_SEND_UPDATE_INFO:
			print thawed['params']



		pass

	def on_from_server_getdevice_info_button_clicked(self):

		aa = "{\"method\":\"getdeviceinfo\",\"params\":{\"type\":\"fw\"}}"
		print aa
		thawed = jsonpickle.decode(aa)
		response_id = '1' 
		aREsult = ResultMarshall()
		sampleResponse={}
		sampleResponse['device']=NetworkHelloMarshall()
		aREsult.additionalInfo = sampleResponse
		resp = jsonpickle.encode(aREsult,unpicklable=False)
		print resp
	
		if thawed['method'] == VONMqttProtocol.MQTT_RPC_CMD_SEND_UPDATE_INFO:
			print thawed['params']



		pass	

if __name__ == '__main__':
	ROOT_PATH = os.path.dirname(os.path.abspath(__file__))   
	os.chdir(ROOT_PATH)
	root = tk.Tk()
	app = Application(root)
	root.mainloop()