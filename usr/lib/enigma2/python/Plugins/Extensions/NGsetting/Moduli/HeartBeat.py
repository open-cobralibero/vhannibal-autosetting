#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# HeartBeatService class
# credits @ livewinter

import os
import sys
import json
import uuid
import time
import logging

try:
	import urllib.request as urllib_request
	import urllib.error as urllib_error
except ImportError:
	import urllib2 as urllib_request
	import urllib2 as urllib_error

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
			logging.info("Creating new heartbeat info file.")
			self.createInfo()
			self.storeInfo()
			self.sendInfo()
		else:
			self.info = self.loadInfo()
			if self.vas_version != self.info["vas_version"]:
				logging.info("VAS version changed, updating info.")
				self.updateInfo()

	def loadInfo(self):
		try:
			with open(self.infoLocation, "r") as infofile:
				infofilejson = infofile.read()
				return json.loads(infofilejson)
		except Exception as e:
			logging.error("Failed to load info file: %s" % e)
			return {}

	def createInfo(self):
		uid = self.createUid()
		stb_model = getBoxType()
		firmware_version = os.popen("cat /etc/issue.net").read()
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
				if info and info.get("uid") != 0:
					return True
			except Exception as e:
				logging.warning("Failed to validate existing info: %s" % e)
		return False

	def updateInfo(self):
		self.info["vas_version"] = self.vas_version
		self.info["vas_upgraded"] = int(time.time())
		self.storeInfo()

	def storeInfo(self):
		try:
			with open(self.infoLocation, "w+") as infofile:
				infofile.write(json.dumps(self.info))
		except Exception as e:
			logging.error("Failed to store info: %s" % e)

	def sendInfo(self):
		try:
			url = "http://vas-heartbeat.livewinter.com/api/new-device"
			headers = {'Content-Type': 'application/json'}

			fileinfojson = self.loadInfo()
			fileinfojson["time_full"] = self.now
			fileinfojson["python_version"] = sys.version
			fileinfojson["system_date"] = os.popen("date").read().strip()
			data = json.dumps(fileinfojson).encode("utf-8")

			logging.info("Sending heartbeat: %s" % data)

			if sys.version_info[0] < 3:
				req = urllib_request.Request(url, data=data, headers=headers)
				response = urllib_request.urlopen(req)
				logging.info("Response: %s" % response.read())
			else:
				req = urllib_request.Request(url, data=data, headers=headers)
				with urllib_request.urlopen(req) as response:
					response_data = response.read()
					logging.info("Response: %s" % response_data)
		except urllib_error.URLError as e:
			logging.error("Failed to send data: %s" % e.reason)
		except Exception as e:
			logging.error("An error occurred during sendInfo: %s" % e)
