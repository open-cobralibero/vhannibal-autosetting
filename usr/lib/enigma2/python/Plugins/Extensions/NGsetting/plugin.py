#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Import standard library modules
import os
import socket
import sys
import time
import codecs

# Import third-party modules
from random import choice

# Import Enigma2 related modules
from enigma import (
	RT_HALIGN_LEFT,
	RT_VALIGN_CENTER,
	eListboxPythonMultiContent,
	eTimer,
	gFont,
	getDesktop,
)

# Import from Screens and Components (Enigma2 libraries)
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Import local modules (relative imports)
from . import logger
from .Moduli.Setting import StartProcess
from .Moduli.Config import ConverDate_noyear, WriteSave
from .Moduli.Config import Load, DownloadSetting
from .Moduli.Language import _
from .Moduli.Lcn import LCN
from .Moduli.Select import MenuSelect

# Import Plugin-related module
from Plugins.Plugin import PluginDescriptor


PY3 = sys.version_info[0] >= 3

Version = '2.9'
MinStart = int(choice(range(59)))
plugin_path = '/usr/lib/enigma2/python/Plugins/Extensions/NGsetting'
Ddate = plugin_path + '/Moduli/NGsetting/Date'
SSelect = plugin_path + '/Moduli/NGsetting/Select'
HD = getDesktop(0).size()


if HD.width() == 1920:
	skin_path = plugin_path + '/Skin/fhd/'
elif HD.width() == 2560:
	skin_path = plugin_path + '/Skin/uhd/'
else:
	skin_path = os.path.join(plugin_path, "Skin/hd/")


def ReloadBouquets():
	print('\n----Reloading bouquets----\n')
	try:
		from enigma import eDVBDB
	except ImportError:
		eDVBDB = None
	if eDVBDB:
		db = eDVBDB.getInstance()
		if db:
			db.reloadServicelist()
			db.reloadBouquets()
			print("eDVBDB: bouquets reloaded...")
	else:
		os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=2 > /dev/null 2>&1 &")
		os.system("wget -qO - http://127.0.0.1/web/servicelistreload?mode=4 > /dev/null 2>&1 &")
		print("wGET: bouquets reloaded...")


class MenuListiSettingE2(MenuList):

	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)
		if HD.width() == 2560:
			self.l.setFont(0, gFont('Regular', 48))
			self.l.setItemHeight(56)
		elif HD.width() == 1920:
			self.l.setFont(0, gFont('Regular', 34))
			self.l.setItemHeight(50)
		else:
			self.l.setFont(0, gFont('Regular', 25))
			self.l.setItemHeight(45)


class MenuListiSettingE2A(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, True, eListboxPythonMultiContent)
		if HD.width() == 2560:
			self.l.setFont(0, gFont('Regular', 48))
			self.l.setItemHeight(56)
		elif HD.width() == 1920:
			self.l.setFont(0, gFont('Regular', 34))
			self.l.setItemHeight(50)
		else:
			self.l.setFont(0, gFont('Regular', 25))
			self.l.setItemHeight(45)


class MenuiSettingE2(Screen, ConfigListScreen):
	def __init__(self, session):
		self.session = session
		skin = os.path.join(skin_path, 'Main.xml')
		with codecs.open(skin, "r", encoding="utf-8") as f:
			self.skin = f.read()

		Screen.__init__(self, session)
		self["actions"] = ActionMap(
			[
				"OkCancelActions",
				"ShortcutActions",
				"WizardActions",
				"ColorActions",
				"SetupActions",
				"NumberActions",
				"MenuActions",
				"HelpActions",
				"EPGSelectActions"
			],
			{
				"ok": self.keyOK,
				"up": self.keyUp,
				"down": self.keyDown,
				"blue": self.Auto,
				"green": self.Lcn,
				"yellow": self.Select,
				"cancel": self.exitplug,
				"left": self.keyRightLeft,
				"right": self.keyRightLeft,
				"red": self.exitplug
			},
			-1
		)
		self['autotimer'] = Label("")
		self['namesat'] = Label("")
		self['text'] = Label("")
		self['dataDow'] = Label("")
		self['Green'] = Pixmap()
		self['Blue'] = Pixmap()
		self['Yellow'] = Pixmap()
		self['Green'].hide()
		self['Yellow'].show()
		self['Blue'].show()
		self["Key_Lcn"] = Label('')
		self.LcnOn = False
		if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Date') and os.path.exists('/etc/enigma2/lcndb'):
			self['Key_Lcn'].setText(_("Lcn"))
			self.LcnOn = True
			self['Green'].show()
		self["Key_Red"] = Label(_("Exit"))
		self["Key_Green"] = Label(_("Setting Installed:"))
		self["Key_Personal"] = Label("")
		AutoTimer, NameSat, Data, Type, Personal, DowDate = Load()
		self['A'] = MenuListiSettingE2A([])
		self['B'] = MenuListiSettingE2([])
		self["B"].selectionEnabled(1)
		self["A"].selectionEnabled(1)
		self.currentlist = 'B'
		self.ServerOn = True
		self.DubleClick = True
		self.MenuA()
		self.List = DownloadSetting()
		self.MenuB()
		self.iTimer = eTimer()
		self.iTimer.callback.append(self.keyRightLeft)
		self.iTimer.start(1000, True)
		self.iTimer1 = eTimer()
		self.iTimer1.callback.append(self.StartSetting)
		self.OnWriteAuto = eTimer()
		self.OnWriteAuto.callback.append(self.WriteAuto)
		self.StopAutoWrite = False
		self.ExitPlugin = eTimer()
		self.ExitPlugin.callback.append(self.PluginClose)
		self.onShown.append(self.ReturnSelect)
		self.onShown.append(self.Info)

	def PluginClose(self):
		try:
			self.ExitPlugin.stop()
		except:
			pass
		self.close()

	def exitplug(self):
		if self.DubleClick:
			self.ExitPlugin.start(10000, True)
			self.DubleClick = False
			self.MenuB()
		else:
			self.PluginClose()

	def Select(self):
		AutoTimer, NameSat, Data, Type, Personal, DowDate = Load()
		if str(Personal).strip() == '0':
			self['Key_Personal'].setText(_("Favourites: Yes"))
			Personal = '1'
			self.session.open(MenuSelect)
		else:
			self['Key_Personal'].setText(_("Favourites: No"))
			Personal = '0'
		WriteSave(NameSat, AutoTimer, Type, Data, Personal, DowDate)

	def ReturnSelect(self):
		AutoTimer, NameSat, Data, Type, Personal, DowDate = Load()
		if not os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Select') or os.path.getsize('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Select') < 20:
			self['Key_Personal'].setText(_("Favourites: No"))
			WriteSave(NameSat, AutoTimer, Type, Data, '0', DowDate)

	def Lcn(self):
		if self.LcnOn:
			lcn = LCN()
			lcn.read()
			if len(lcn.lcnlist) > 0:
				lcn.writeBouquet()
				lcn.reloadBouquets()
				self.session.open(MessageBox, _("Sorting Lcn Completed"), MessageBox.TYPE_INFO, timeout=5)

	def Auto(self):
		if self.StopAutoWrite:
			return
		self.StopAutoWrite = True
		iTimerClass.StopTimer()
		AutoTimer, self.NameSat, self.Data, self.Type, self.Personal, self.DowDate = Load()
		if int(AutoTimer) == 0:
			self['autotimer'].setText(_("AutoUpdate: Yes"))
			self.jAutoTimer = 1
			iTimerClass.TimerSetting()
		else:
			self['autotimer'].setText(_("AutoUpdate: No"))
			self.jAutoTimer = 0
		self.OnWriteAuto.start(1000, True)

	def WriteAuto(self):
		self.StopAutoWrite = False
		WriteSave(self.NameSat, self.jAutoTimer, self.Type, self.Data, self.Personal, self.DowDate)

	def Info(self):
		AutoTimer, NameSat, Data, Type, Personal, DowDate = Load()
		if int(AutoTimer) == 0:
			TypeTimer = 'No'
		else:
			TypeTimer = 'Yes'
		if int(Personal) == 0:
			jPersonal = 'No'
		else:
			jPersonal = 'Yes'
		if str(DowDate) == '0':
			newDowDate = _('Last Update: Unregistered')
		else:
			newDowDate = _('Last Update: ') + DowDate
		self['Key_Personal'].setText(_("Favourites: ") + jPersonal)
		self['autotimer'].setText(_("AutoUpdate: ") + TypeTimer)
		self['namesat'].setText(NameSat)
		self['dataDow'].setText(newDowDate)

	def hauptListEntryMenuA(self, name, type):
		res = [(name, type)]
		if HD.width() == 2560:
			res.append(MultiContentEntryText(pos=(10, 0), size=(450, 56), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(4, 0), font=0, text=type, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		elif HD.width() == 1920:
			res.append(MultiContentEntryText(pos=(10, 0), size=(300, 40), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(4, 0), font=0, text=type, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		else:
			res.append(MultiContentEntryText(pos=(10, 0), size=(170, 40), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(4, 0), font=0, text=type, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		return res

	def hauptListEntryMenuB(self, name, date, link, name1, date1):
		res = [(name, date, link, name1, date1)]
		if HD.width() == 2560:
			res.append(MultiContentEntryText(pos=(30, 0), size=(850, 56), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(740, 0), size=(200, 40), font=0, text=date1, color=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=link, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))

		elif HD.width() == 1920:
			res.append(MultiContentEntryText(pos=(15, 0), size=(850, 40), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(680, 0), size=(200, 40), font=0, text=date1, color=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=link, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))

		else:
			res.append(MultiContentEntryText(pos=(10, 0), size=(400, 40), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(410, 0), size=(210, 40), font=0, text=date1, color=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
			res.append(MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=link, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		res.append(MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=name1, flags=RT_HALIGN_LEFT))
		res.append(MultiContentEntryText(pos=(0, 0), size=(0, 0), font=0, text=date, flags=RT_HALIGN_LEFT))
		return res

	def MenuA(self):
		self.jA = []
		self.jA.append(self.hauptListEntryMenuA('Mono', 'hot'))
		self.jA.append(self.hauptListEntryMenuA('Dual', 'dual'))
		self.jA.append(self.hauptListEntryMenuA('Trial', 'trial'))
		self.jA.append(self.hauptListEntryMenuA('Quadri', 'quadri'))
		self.jA.append(self.hauptListEntryMenuA('Motor', 'motor'))
		self.jA.append(self.hauptListEntryMenuA('Deutschland', 'deutschland'))
		self.jA.append(self.hauptListEntryMenuA('Polska', 'polska'))
		self["A"].setList(self.jA)

	def MenuB(self):
		self.jB = []
		if not self.DubleClick:
			self.ServerOn = False
			self.jB.append(self.hauptListEntryMenuB(_('NGsetting Version ') + Version, '', '', '', ''))
			self.jB.append(self.hauptListEntryMenuB(_('Coder: m43c0 & ftp21'), '', '', '', ''))
			self.jB.append(self.hauptListEntryMenuB(_('Edit by: @Lululla 20231201'), '', '', '', ''))
			self.jB.append(self.hauptListEntryMenuB(_('Skinner: mmark'), '', '', '', ''))
			self.jB.append(self.hauptListEntryMenuB(_('Vhannibal Official Plugin'), '', '', '', ''))
			self.jB.append(self.hauptListEntryMenuB(_('www.vhannibal.net'), '', '', '', ''))
			self["B"].setList(self.jB)
			return
		for date, name, link in self.List:
			if name.lower().find(self["A"].getCurrent()[0][1]) != -1:
				self.jB.append(self.hauptListEntryMenuB(str(name.title()), str(date), str(link), str(name), ConverDate_noyear(str(date))))

		if not self.jB:
			self.jB.append(self.hauptListEntryMenuB(_('Server down for maintenance'), '', '', '', ''))
			self["B"].setList(self.jB)
			self.ServerOn = False
			self.MenuA()
			return
		self["B"].setList(self.jB)

	def keyOK(self):
		logger.debug("Selezionato setting: %s", self["B"].getCurrent()[0][3])
		if not self.ServerOn:
			print('if not self.ServerOn')
			return
		if self.currentlist == 'A':
			self.currentlist = 'B'
			self["B"].selectionEnabled(1)
			self["A"].selectionEnabled(0)
			return
		self.name = self["B"].getCurrent()[0][3]
		self.jType = '1'
		if self.name.lower().find('dtt') != -1:
			self.jType = '0'
		self.AutoTimer, NameSat, self.Data, Type, self.Personal, self.DowDate = Load()
		try:
			nData = int(self.Data)
		except:
			nData = 0
		try:
			njData = int(self["B"].getCurrent()[0][1])
		except:
			njData = 999999
		if NameSat != self.name or Type != self.jType:
			self.session.openWithCallback(self.OnDownload, MessageBox, _('The new configurations are saved\nSetting: %s\nDate: %s\nThe choice is different from the previous\nDo you want to proceed with the manual upgrade?') % (self.name, self["B"].getCurrent()[0][4]), MessageBox.TYPE_YESNO, timeout=20)
		elif njData > nData:
			self.session.openWithCallback(self.OnDownload, MessageBox, _('The new configurations are saved\nSetting: %s\nDate: %s \n The new setting has a more recent date\nDo you want to proceed with the manual upgrade?') % (self.name, self["B"].getCurrent()[0][4]), MessageBox.TYPE_YESNO, timeout=20)
		else:
			self.session.openWithCallback(self.OnDownloadForce, MessageBox, _('Setting already updated, you want to upgrade anyway?'), MessageBox.TYPE_YESNO, timeout=20)

	def OnDownloadForce(self, conf):
		if conf:
			self.OnDownload(True, False)

	def StartSetting(self):
		iTimerClass.StopTimer()
		iTimerClass.startTimerSetting(True)

	def OnDownload(self, conf, noForce=True):
		if conf:
			if noForce:
				WriteSave(self.name, self.AutoTimer, self.jType, self.Data, self.Personal, self.DowDate)
			self.iTimer1.start(100, True)
		else:
			WriteSave(self.name, self.AutoTimer, self.jType, '0', self.Personal, self.DowDate)
		self.Info()

	def keyUp(self):
		self[self.currentlist].up()
		if self.currentlist == 'A':
			self.MenuB()

	def keyDown(self):
		self[self.currentlist].down()
		if self.currentlist == 'A':
			self.MenuB()

	def keyRightLeft(self):
		self["A"].selectionEnabled(0)
		self["B"].selectionEnabled(0)
		if self.currentlist == 'A':
			if not self.ServerOn:
				return
			self.currentlist = 'B'
			self["B"].selectionEnabled(1)
			self.MenuB()
		else:
			self.currentlist = 'A'
			self["A"].selectionEnabled(1)


class NgSetting():

	def __init__(self, session=None):
		self.session = session
		self.iTimer1 = eTimer()
		self.iTimer2 = eTimer()
		self.iTimer3 = eTimer()
		self.iTimer1.callback.append(self.startTimerSetting)
		self.iTimer2.callback.append(self.startTimerSetting)
		self.iTimer3.callback.append(self.startTimerSetting)

	def gotSession(self, session):
		self.session = session
		AutoTimer, NameSat, Data, Type, Personal, DowDate = Load()
		if int(AutoTimer) == 1:
			self.TimerSetting()

	def StopTimer(self):
		try:
			self.iTimer1.stop()
		except:
			pass
		try:
			self.iTimer2.stop()
		except:
			pass
		try:
			self.iTimer3.stop()
		except:
			pass

	def TimerSetting(self):
		try:
			self.StopTimer()
		except:
			pass
		now = time.time()
		ttime = time.localtime(now)
		start_time1 = time.mktime((ttime[0], ttime[1], ttime[2], 6, MinStart, 0, ttime[6], ttime[7], ttime[8]))
		start_time2 = time.mktime((ttime[0], ttime[1], ttime[2], 14, MinStart, 0, ttime[6], ttime[7], ttime[8]))
		start_time3 = time.mktime((ttime[0], ttime[1], ttime[2], 22, MinStart, 0, ttime[6], ttime[7], ttime[8]))
		logger.debug("Impostazione timer aggiornamenti: 6:%02d, 14:%02d, 22:%02d", MinStart, MinStart, MinStart)
		if start_time1 < (now + 60):
			start_time1 += 86400
		if start_time2 < (now + 60):
			start_time2 += 86400
		if start_time3 < (now + 60):
			start_time3 += 86400
		delta1 = int(start_time1 - now)
		delta2 = int(start_time2 - now)
		delta3 = int(start_time3 - now)
		self.iTimer1.start(1000 * delta1, True)
		self.iTimer2.start(1000 * delta2, True)
		self.iTimer3.start(1000 * delta3, True)

	def startTimerSetting(self, Auto=False):
		self.AutoTimer, NameSat, Data, self.Type, self.Personal, DowDate = Load()
		logger.info("Controllo aggiornamenti automatici...")
		try:
			def OnDsl():
				try:
					socket.setdefaulttimeout(0.5)
					socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
					return True
				except:
					return False
				return

			if OnDsl():
				for self.date, self.name, self.link in DownloadSetting():
					if self.name == NameSat:
						if self.date > Data or Auto:
							self.BackgroundAutoUpdate()
						break
			self.TimerSetting()
		except Exception as e:
			logger.error("Errore durante il controllo aggiornamenti: %s", str(e))

	def BackgroundAutoUpdate(self):
		logger.info("Download setting: %s (%s)", self.name, self.link)
		try:
			if StartProcess(self.link, self.Type, self.Personal):
				now = time.time()
				jt = time.localtime(now)
				year = str(jt[0])[2:]
				DowDate = str(jt[2]).zfill(2) + '/' + str(jt[1]).zfill(2) + '/' + year + ' @ ' + str(jt[3]).zfill(2) + ':' + str(jt[4]).zfill(2) + ':' + str(jt[5]).zfill(2)
				WriteSave(self.name, self.AutoTimer, self.Type, self.date, self.Personal, DowDate)
				ReloadBouquets()
				if self.session:
					self.session.open(
						MessageBox,
						_("New Setting Vhannibal ") + str(self.name) + _(" of ") + ConverDate_noyear(str(self.date)) + _(" updated"),
						MessageBox.TYPE_INFO,
						timeout=5
					)
				else:
					logger.error("Session is not available! Cannot show success MessageBox.")
				os.system('rm -rf /usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Temp/*')
			else:
				if self.session:
					self.session.open(
						MessageBox,
						_("Sorry!\nError Download Setting"),
						MessageBox.TYPE_ERROR,
						timeout=5
					)
				else:
					logger.error("Session is not available! Cannot show error MessageBox.")
		except Exception as e:
			logger.exception("Aggiornamento fallito! %s" % e)


global jsession
jsession = None
iTimerClass = NgSetting(jsession)


def SessionStart(reason, **kwargs):
	global jsession
	if reason == 0:
		jsession = kwargs["session"]
		iTimerClass.gotSession(jsession)


iTimerClass = NgSetting(jsession)


def AutoStart(reason, **kwargs):
	if reason == 1:
		iTimerClass.StopTimer()


def Main(session, **kwargs):
	session.open(MenuiSettingE2)


def Plugins(**kwargs):
	logger.info("Registrazione plugin Vhannibal AutoSetting versione %s", Version)
	return [
		PluginDescriptor(name="Vhannibal AutoSetting " + Version,
						 description="Vhannibal Official Plugin by NGSetting",
						 icon="Vhannibal.png",
						 where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU],
						 fnc=Main),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=SessionStart),
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=AutoStart)
	]
