#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HeartBeatService class
# credits @ livewinter
import os
import sys
import urllib.request
import urllib.error
import json
import uuid
import time


try:
	from enigma import getBoxType
except ImportError:
	from boxbranding import getBoxType


class HeartBeatService():

	def __init__(self, version):
		self.info = {
			"uid": 0,
			"stb_model": 0,
			"firmware_version": 0,
			"vas_installed": 0,
			"vas_upgraded": 0,
			"vas_version": 0,
		}

		self.vas_version = version
		self.infoLocation = "/home/vas/info"

		if not self.infoExists():
			self.createInfo()
			self.storeInfo()
			self.sendInfo()
		else:
			self.info = self.loadInfo()
			if (self.vas_version != self.info["vas_version"]):
				self.updateInfo()

	def loadInfo(self):
		infofile = open(self.infoLocation, 'r')
		infofilejson = infofile.read()
		return json.loads(infofilejson)

	def createInfo(self):
		uid = self.createUid()
		stb_model = getBoxType()
		firmware_version = os.popen('cat /etc/issue.net').read()
		self.now = time.time()
		vas_installed = int(self.now)
		self.info["uid"] = str(uid)
		self.info["stb_model"] = stb_model
		self.info["firmware_version"] = firmware_version
		self.info["vas_installed"] = vas_installed
		self.info["vas_version"] = self.vas_version
		os.system("mkdir -p /home/vas/")

	def createUid(self):
		return uuid.uuid4()

	def infoExists(self):
		if os.path.exists(self.infoLocation):
			try:
				info = self.loadInfo()
				if info["uid"] != 0:
					return True
			except:
				pass
		return False

	def updateInfo(self):
		self.info["vas_version"] = self.vas_version
		self.info["vas_upgraded"] = int(time.time())
		self.storeInfo()

	def storeInfo(self):
		infofile = open(self.infoLocation, 'w+')
		infofile.write(json.dumps(self.info))

	def sendInfo(self):
		try:
			url = 'http://vas-heartbeat.livewinter.com/api/new-device'
			req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
			fileinfojson = self.loadInfo()
			fileinfojson['time_full'] = self.now
			fileinfojson['python_version'] = sys.version
			fileinfojson['system_date'] = os.popen('date').read().strip()
			fileinfojson = json.dumps(fileinfojson).encode('utf-8')
			print('MYDEBUGLOGLINE - fileinfojson API data = %s' % fileinfojson)
			with urllib.request.urlopen(req, data=fileinfojson) as response:
				response_data = response.read()
				print('Response: ', response_data)
		except urllib.error.URLError as e:
			print('Failed to send data:', e.reason)
		except Exception as e:
			print('An error occurred:', e)
