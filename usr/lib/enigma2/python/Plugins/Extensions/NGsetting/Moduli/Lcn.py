#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from enigma import eDVBDB, eServiceReference, eServiceCenter
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import re
import xml.etree.cElementTree


def Bouquet():
	for file in os.listdir('/etc/enigma2/'):
		if re.search('^userbouquet.*.tv', file):
			try:
				with open('/etc/enigma2/' + file, 'r') as f:
					x = f.read()
					if re.search('#NAME Digitale Terrestre', x, flags=re.IGNORECASE):
						return '/etc/enigma2/' + file
			except Exception as e:
				print(f"Errore durante la lettura del file {file}: {e}")
	return None


class LCN:
	service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 134) || (type == 195)'

	def __init__(self):
		self.dbfile = '/var/etc/enigma2/lcndb'
		self.bouquetfile = Bouquet()
		self.lcnlist = []
		self.markers = []
		self.e2services = []
		mdom = xml.etree.cElementTree.parse(resolveFilename(SCOPE_PLUGINS, 'Extensions/NGsetting/Moduli/NGsetting/rules.xml'))
		self.root = None
		for x in mdom.getroot():
			if x.tag == 'ruleset' and x.get('name') == 'Italy':
				self.root = x
				return

		return

	def addLcnToList(self, namespace, nid, tsid, sid, lcn, signal):
		if lcn == 0:
			return

		for x in self.lcnlist:
			if x[0] == lcn and x[1] == namespace and x[2] == nid and x[3] == tsid and x[4] == sid:
				return
		for i in range(len(self.lcnlist)):
			if self.lcnlist[i][0] == lcn:
				if self.lcnlist[i][5] > signal:
					self.addLcnToList(namespace, nid, tsid, sid, lcn + 16536, signal)
				else:
					znamespace, znid, ztsid, zsid, zsignal = self.lcnlist[i][1:6]
					self.lcnlist[i][1] = namespace
					self.lcnlist[i][2] = nid
					self.lcnlist[i][3] = tsid
					self.lcnlist[i][4] = sid
					self.lcnlist[i][5] = signal
					self.addLcnToList(znamespace, znid, ztsid, zsid, lcn + 16536, zsignal)
				return

			if self.lcnlist[i][0] > lcn:
				self.lcnlist.insert(i, [lcn, namespace, nid, tsid, sid, signal])
				return

		self.lcnlist.append([lcn, namespace, nid, tsid, sid, signal])

	def renumberLcn(self, range, rule):
		tmp = range.split("-")
		if len(tmp) != 2:
			return
		try:
			min_value = int(tmp[0])
			max_value = int(tmp[1])
		except ValueError:
			print(f"Errore: Il range '{range}' non è valido.")
			return
		for x in self.lcnlist:
			if min_value <= x[0] <= max_value:
				try:
					new_value = eval(rule)
					x[0] = new_value
				except Exception as e:
					print(e)

	def addMarker(self, position, text):
		self.markers.append([position, text])

	def read(self):
		self.readE2Services()
		try:
			with open(self.dbfile, 'r') as f:
				while True:
					line = f.readline()
					if line == '':
						break
					line = line.strip()
					if len(line) != 38:
						continue
					tmp = line.split(':')
					if len(tmp) != 6:
						continue
					self.addLcnToList(
						int(tmp[0], 16),
						int(tmp[1], 16),
						int(tmp[2], 16),
						int(tmp[3], 16),
						int(tmp[4]),
						int(tmp[5])
					)
		except Exception as e:
			print(e)
			return

		if self.root is not None:
			for x in self.root:
				if x.tag == 'rule' and x.get('type') == 'marker':
					self.addMarker(int(x.get('position')), x.text)
		self.markers.sort(key=lambda z: int(z[0]))
		return

	def readE2Services(self):
		self.e2services = []
		refstr = '%s ORDER BY name' % self.service_types_tv
		ref = eServiceReference(refstr)
		serviceHandler = eServiceCenter.getInstance()
		servicelist = serviceHandler.list(ref)
		if servicelist is not None:
			while True:
				service = servicelist.getNext()
				if not service.valid():
					break
				unsigned_orbpos = service.getUnsignedData(4) >> 16
				if unsigned_orbpos == 0xEEEE or unsigned_orbpos == 61166:
					self.e2services.append(service.toString())
		return

	def ClearDoubleMarker(self, UserBouquet):
		if os.path.exists(UserBouquet):
			try:
				with open(UserBouquet, 'r') as ReadFile:
					uBQ = ReadFile.readlines()
				LineMaker = []
				PosDelMaker = []
				x = 1
				for line in uBQ:
					if '#SERVICE 1:64:' in line:
						x += 1
						continue
					elif '#DESCRIPTION' in line:
						LineMaker.append(x)
					x += 1
				START = 0
				STOP = 0
				i = 0
				for xx in LineMaker:
					if i + 1 < len(LineMaker):
						START = LineMaker[i]
						STOP = LineMaker[i + 1]
						if STOP - START < 3:
							PosDelMaker.append(START)
							PosDelMaker.append(START + 1)
						if uBQ[START] == uBQ[STOP]:
							PosDelMaker.append(STOP)
							PosDelMaker.append(STOP + 1)
					i += 1
				PosDelMaker.reverse()
				for delmark in PosDelMaker:
					del uBQ[delmark - 1]

				with open(UserBouquet, 'w') as WriteFile:
					WriteFile.writelines(uBQ)
			except Exception as e:
				print("Errore durante la pulizia dei marker:", e)

	def writeBouquet(self):
		try:
			with open(self.bouquetfile, 'w') as f:
				f.write('#NAME Digitale Terrestre\n')
				for x in self.lcnlist:
					if len(self.markers) > 0:
						if x[0] > self.markers[0][0]:
							f.write('#SERVICE 1:64:0:0:0:0:0:0:0:0:\n')
							f.write('#DESCRIPTION ------- ' + self.markers[0][1] + ' -------\n')
							self.markers.remove(self.markers[0])
					refstr = '1:0:1:%x:%x:%x:%x:0:0:0:' % (x[4], x[3], x[2], x[1])
					refsplit = eServiceReference(refstr).toString().split(':')
					for tref in self.e2services:
						tmp = tref.split(':')
						if tmp[3] == refsplit[3] and tmp[4] == refsplit[4] and tmp[5] == refsplit[5] and tmp[6] == refsplit[6]:
							f.write('#SERVICE ' + tref + '\n')
							break
		except Exception as e:
			print(e)
		self.ClearDoubleMarker(self.bouquetfile)

	def reloadBouquets(self):
		eDVBDB.getInstance().reloadBouquets()
