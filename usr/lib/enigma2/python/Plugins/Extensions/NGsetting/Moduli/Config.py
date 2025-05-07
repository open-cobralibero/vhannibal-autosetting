#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# recoded @ lululla 20250507

import os
import sys
from random import choice
from datetime import datetime
from re import compile, DOTALL

from . import logger

Samanta = ''
PY3 = sys.version_info.major >= 3
if PY3:
	from urllib.request import urlopen, Request
else:
	from urllib2 import urlopen, Request

DirFolder = os.path.dirname(sys.modules[__name__].__file__)
if not os.path.exists(DirFolder + '/NGsetting'):
	os.system('mkdir ' + DirFolder + '/NGsetting')
if not os.path.exists(DirFolder + '/NGsetting/Temp'):
	os.system('mkdir ' + DirFolder + '/NGsetting/Temp')

try:
	import dinaconvertdate
except:
	Samanta = "dina"


std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}


ListAgent = [
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15',
	'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14',
	'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
	'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
]


def RequestAgent():
	RandomAgent = choice(ListAgent)
	return RandomAgent


def make_request(url):
	try:
		import requests
		link = requests.get(url, headers={'User-Agent': RequestAgent()}).text
		return link
	except ImportError:
		req = Request(url)
		req.add_header('User-Agent', 'E2 Plugin Vhannibal')
		response = urlopen(req, None, 7)
		link = response.read().decode('utf-8')
		response.close()
		return link
	return


def ConverDate(data):
	return datetime.strptime(data, "%y%m%d").strftime('%d-%m-%Y')


def ConverDate_noyear(data):
	date = datetime.strptime(data, "%y%m%d")
	return date.strftime("%d/%m")


def TestDsl():
	try:
		import socket
		socket.setdefaulttimeout(0.5)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
		return True
	except:
		return False


def DownloadSetting():
	try:
		logger.info("Scaricamento lista setting da vhannibal.net...")
		html = make_request('http://www.vhannibal.net/asd.php')

		# Usa espressioni regolari per estrarre i dati
		pattern = compile(r'<tr.*?>.*?<td.*?><a.*?href="(.*?)".*?>(.*?)</a>.*?</td>.*?<td.*?>(.*?)</td>', DOTALL)
		matches = pattern.findall(html)

		list = []
		base_url = "http://www.vhannibal.net/"
		for match in matches:
			link, name, date = match
			name = name.strip()
			date = date.strip()
			if not link.startswith("http"):
				link = base_url + link.lstrip("/")
			list.append((date, name, link))
			logger.debug("Trovati %d setting nel server", len(list))

		return list

	except Exception as e:
		logger.error("Download fallito! Errore: %s", str(e))
		return []


def Load():
	logger.debug("Lettura file Date...")
	try:
		AutoTimer = '0'
		if PY3:
			NameSat = 'Hot Bird 13°E'
		else:
			NameSat = 'Hot Bird 13\xc2\xb0E'
		Data = '0'
		Type = '0'
		Personal = '0'
		DowDate = '0'
		if os.path.exists(DirFolder + '/NGsetting/Date'):
			xf = open(DirFolder + '/NGsetting/Date', "r")
			f = xf.readlines()
			xf.close()
			for line in f:
				try:
					LoadDate = line.strip()
					elements = LoadDate.split('=')
					if len(elements) == 2:
						key, value = elements
						value = value.strip()

						if 'AutoTimer' in key:
							AutoTimer = value
						elif 'NameSat' in key:
							NameSat = value
						elif 'Data' in key:
							Data = value
						elif 'Type' in key:
							Type = value
						elif 'Personal' in key:
							Personal = value
						elif 'DowDate' in key:
							DowDate = value
				except Exception as e:
					print("Errore durante il caricamento dei dati:", e)
		else:
			line = 'AutoTimer = 0\nNameSat = \nData = 0\nType = 0\nPersonal = 0\nDowDate = 0'
			with open(DirFolder + '/NGsetting/Date', 'w') as f:
				f.write(line)
		logger.info("Configurazione caricata: %s (Data: %s)", NameSat, Data)
		return (AutoTimer, NameSat, Data, Type, Personal, DowDate)
	except Exception as e:
		logger.error("Errore durante il caricamento della configurazione: %s", str(e))
		return ('0', 'Hot Bird 13°E', '0', '0', '0', '0')


def WriteSave(name, autotimer, Type, Data, Personal, DowDate):
	line = 'AutoTimer = {}\nNameSat = {}\nData = {}\nType = {}\nPersonal = {}\nDowDate = {}'.format(str(autotimer), str(name), str(Data), str(Type), str(Personal), str(DowDate))
	with open(DirFolder + '/NGsetting/Date', 'w') as f:
		f.write(line)
