#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# recoded @ lululla 20250507
from re import search, IGNORECASE
import glob
from shutil import copy, copy2, copyfile, copytree, rmtree, move
from os import listdir, makedirs, remove
from os.path import join, exists, isdir, dirname, basename
import sys
import time
import zipfile
from . import logger

PY3 = sys.version_info.major >= 3
if PY3:
	from urllib.request import urlopen, Request
else:
	from urllib2 import urlopen, Request


try:
	from requests import get
except ImportError:
	pass


DirFolder = dirname(sys.modules[__name__].__file__)


def TimerControl():
	now = time.localtime(time.time())
	Ora = str(now[3]).zfill(2) + ':' + str(now[4]).zfill(2) + ':' + str(now[5]).zfill(2)
	Date = str(now[2]).zfill(2) + '-' + str(now[1]).zfill(2) + '-' + str(now[0])
	return '%s ora: %s' % (Date, Ora)


def StartSavingTerrestrialChannels():

	def ForceSearchBouquetTerrestrial():
		try:
			# Loop through all .tv files in /etc/enigma2/
			for file in sorted(glob.glob("/etc/enigma2/*.tv")):
				with open(file, "r") as f:
					content = f.read().strip().lower()

				# Check for specific conditions in the file content
				if 'eeee0000' in content and '82000' not in content and 'c0000' not in content:
					return file
			return None
		except Exception as e:
			logger.exception("Error in ForceSearchBouquetTerrestrial: %s", e)
			return None

	def ResearchBouquetTerrestrial(search):
		try:
			# Loop through all .tv files in /etc/enigma2/
			for file in sorted(glob.glob("/etc/enigma2/*.tv")):
				with open(file, "r") as f:
					content = f.read().strip().lower()

				# Search for "#NAME" and the search term in the file
				if "#name" in content:
					if search.lower() in content:
						if 'eeee0000' in content:
							return file
			return None
		except Exception as e:
			logger.exception("Error in ResearchBouquetTerrestrial: %s", e)
			return None

	def SaveTrasponderService():
		Trasponder = False
		inTransponder = False
		inService = False

		try:
			# Open the files for writing using 'with' to ensure proper resource management
			with open(DirFolder + '/NGsetting/Temp/TrasponderListOldLamedb', 'w') as TrasponderListOldLamedb, \
				 open(DirFolder + '/NGsetting/Temp/ServiceListOldLamedb', 'w') as ServiceListOldLamedb, \
				 open('/etc/enigma2/lamedb', 'r') as LamedbFile:

				# Process the lamedb file
				while True:
					line = LamedbFile.readline()
					if not line:
						break

					# Handle transponder and service sections
					if not (inTransponder or inService):
						if line.startswith('transponders'):
							inTransponder = True
						if line.startswith('services'):
							inService = True

					if line.startswith('end'):
						inTransponder = False
						inService = False

					line = line.lower()  # Process the line in lowercase for easier matching

					# Check if line contains 'eeee0000'
					if 'eeee0000' in line:
						Trasponder = True

						# Write transponder lines if inside transponder section
						if inTransponder:
							TrasponderListOldLamedb.write(line)
							for _ in range(3):  # Write next 3 lines
								line = LamedbFile.readline()
								TrasponderListOldLamedb.write(line)

						# Write service lines if inside service section
						if inService:
							tmp = line.split(':')
							# Writing only the relevant parts of the service line
							ServiceListOldLamedb.write(f"{tmp[0]}:{tmp[1]}:{tmp[2]}:{tmp[3]}:{tmp[4]}:0\n")
							for _ in range(2):  # Write next 2 lines
								line = LamedbFile.readline()
								ServiceListOldLamedb.write(line)

			# If no transponder was found, copy the enigma2 settings
			if not Trasponder:
				dst = "/etc/enigma2"
				src = DirFolder + "/NGsetting/Temp/enigma2"
				if exists(dst):
					rmtree(dst)
				copytree(src, dst)

		except Exception as e:
			logger.exception("An error occurred in SaveTrasponderService: %s", e)
			return False

		return Trasponder

	def CreateBouquetForce():
		temp_bouquet_path = DirFolder + "/NGsetting/Temp/TerrestrialChannelListArchive"
		service_list_path = DirFolder + "/NGsetting/Temp/ServiceListOldLamedb"

		with open(temp_bouquet_path, "w") as bouquet_file:
			bouquet_file.write("#NAME terrestre\n")
			with open(service_list_path, "r") as service_file:
				for line in service_file:
					if "eeee" in line:
						parts = line.strip().split(":")
						try:
							service_type = hex(int(parts[4]))[2:]
							bouquet_file.write(
								"#SERVICE 1:0:%s:%s:%s:%s:%s:0:0:0:\n" % (
									service_type, parts[0], parts[2], parts[3], parts[1]
								)
							)
						except (IndexError, ValueError):
							pass  # skip malformed lines

	def SaveBouquetTerrestrial():
		NameDirectory = ResearchBouquetTerrestrial('terr')
		if not NameDirectory:
			NameDirectory = ForceSearchBouquetTerrestrial()
		try:
			copyfile(NameDirectory, DirFolder + '/NGsetting/Temp/TerrestrialChannelListArchive')
			return True
		except:
			pass
	Service = SaveTrasponderService()
	if Service:
		if not SaveBouquetTerrestrial():
			CreateBouquetForce()
		return True


def TransferBouquetTerrestrialFinal():

	def RestoreTerrestrial():
		for file in listdir("/etc/enigma2/"):
			if search(r'^userbouquet.*\.tv$', file):
				try:
					with open("/etc/enigma2/" + file, "r") as f:
						content = f.read()
					if search("#NAME Digitale Terrestre", content, flags=IGNORECASE):
						return "/etc/enigma2/" + file
				except:
					pass

	try:
		with open(DirFolder + "/NGsetting/Temp/TerrestrialChannelListArchive", "r") as f:
			TerrestrialChannelListArchive = f.readlines()

		DirectoryUserBouquetTerrestrial = RestoreTerrestrial()
		if DirectoryUserBouquetTerrestrial:
			with open(DirectoryUserBouquetTerrestrial, "w") as f:
				for Line in TerrestrialChannelListArchive:
					if Line.lower().find("#name") != -1:
						f.write("#NAME Digitale Terrestre\n")
					else:
						f.write(Line)
			return True
	except:
		return False


def SearchIPTV():
	iptv_list = []
	for iptv_file in sorted(glob.glob("/etc/enigma2/userbouquet.*.tv")):
		try:
			with open(iptv_file, "r") as f:
				content = f.read().strip().lower()
			if "http" in content:
				iptv_list.append(basename(iptv_file))
		except:
			pass

	if not iptv_list:
		return False
	return iptv_list


def StartProcess(link, type, Personal):
	logger.info("Avvio processo per: %s", link)

	def LamedbRestore():
		try:
			with open(DirFolder + "/NGsetting/Temp/TrasponderListNewLamedb", "w") as f_trans:
				with open(DirFolder + "/NGsetting/Temp/ServiceListNewLamedb", "w") as f_serv:
					inTransponder = False
					inService = False
					with open("/etc/enigma2/lamedb", "r") as infile:
						for line in infile:
							if not (inTransponder or inService):
								if line.startswith("transponders"):
									inTransponder = True
								if line.startswith("services"):
									inService = True
							if line.startswith("end"):
								inTransponder = False
								inService = False
							if inTransponder:
								f_trans.write(line)
							if inService:
								f_serv.write(line)

			with open("/etc/enigma2/lamedb", "w") as out_lamedb:
				out_lamedb.write("eDVB services /4/\n")

				try:
					with open(DirFolder + "/NGsetting/Temp/TrasponderListNewLamedb", "r") as f:
						out_lamedb.writelines(f.readlines())
					with open(DirFolder + "/NGsetting/Temp/TrasponderListOldLamedb", "r") as f:
						out_lamedb.writelines(f.readlines())
				except:
					pass
				out_lamedb.write("end\n")

				try:
					with open(DirFolder + "/NGsetting/Temp/ServiceListNewLamedb", "r") as f:
						out_lamedb.writelines(f.readlines())
					with open(DirFolder + "/NGsetting/Temp/ServiceListOldLamedb", "r") as f:
						out_lamedb.writelines(f.readlines())
				except:
					pass
				out_lamedb.write("end\n")

			logger.info("Setting applicati correttamente!")
			return True

		except Exception as e:
			logger.exception("Errore critico durante l'installazione! %s" % e)
			return False

	def DownloadSettingAgg(link):
		foldsettmp = DirFolder + '/NGsetting/Temp/listaE2.zip'
		tmpe2 = DirFolder + '/NGsetting/Temp/enigma2'
		tmpextr = DirFolder + '/NGsetting/Temp/setting'

		# Creazione delle directory necessarie, se non esistono
		makedirs(tmpe2, exist_ok=True)
		makedirs(tmpextr, exist_ok=True)

		try:
			# Scarica il file ZIP
			logger.info(f"Downloading settings from: {link}")
			if PY3:
				link_zip = get(link)
				with open(foldsettmp, 'wb') as f:
					f.write(link_zip.content)
				logger.info("Download completed successfully.")
			else:
				req = Request(link)
				req.add_header('User-Agent', "VAS14")
				response = urlopen(req)
				link_data = response.read()
				response.close()
				with open(foldsettmp, 'wb') as f:
					f.write(link_data)
				logger.info("Download completed successfully.")

			# Verifica se il file ZIP esiste e tenta di estrarlo
			if exists(foldsettmp):
				try:
					logger.info("Extracting the ZIP file...")
					with zipfile.ZipFile(foldsettmp, 'r') as image_zip:
						image_zip.extractall(tmpextr)

					dir_setting = listdir(tmpextr)
					if dir_setting:
						name_setting = dir_setting[0]
						dir_name = tmpextr + '/' + name_setting
						logger.info(f"Directory name: {dir_name}")
						for filename in glob.glob(join(dir_name, '*')):
							copy(filename, tmpe2)
						logger.info("Files copied to the enigma2 directory.")
					else:
						logger.warning("No setting directory found in the ZIP file.")
				except zipfile.BadZipFile:
					logger.error("Failed to extract the ZIP file. It may be corrupted.")
				except Exception as e:
					logger.error(f"Error during extraction: {e}")

			if exists(DirFolder + "/NGsetting/Temp/enigma2/lamedb"):
				logger.info("Settings downloaded and extracted successfully.")
				return True

		except Exception as e:
			logger.error(f"Error in downloading or extracting settings: {e}")
			return False

	def SaveList(list):
		# Open the file with 'with' to ensure it is properly closed
		with open('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/SelectBack', 'w') as jw:
			for dir, name in list:
				jw.write(f"{dir}---{name}\n")

	def SavePersonalSetting():
		try:
			# Ensure the directory exists
			makedirs(DirFolder + '/NGsetting/SelectFolder', exist_ok=True)

			# Open and read the file with 'with' for better resource management
			with open('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Select', 'r') as jw:
				jjw = jw.readlines()

			count = 1
			list = []

			# Process each line in the file
			for x in jjw:
				try:
					jx = x.split('---')
					newfile = f'userbouquet.NgSetting{count}.tv'
					src = f'/etc/enigma2/{jx[0]}'
					dst = f'/{DirFolder}/NGsetting/SelectFolder/{newfile}'

					# Copy the file using shutil.copyfile
					copyfile(src, dst)

					list.append((newfile, jx[1]))
					count += 1
				except Exception as e:
					# Log any errors that occur while processing each line
					logger.exception(f"Error copying file: {src} to {dst} - {e}")
					pass

			# Save the list of files after processing
			SaveList(list)
		except Exception as e:
			logger.exception("Error in SavePersonalSetting: %s", e)
			return False

		return True

	def TransferPersonalSetting():
		try:
			# Open the SelectBack file with 'with' to ensure it's properly closed
			with open('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/SelectBack', 'r') as jw:
				jjw = jw.readlines()

			# Iterate over the list and copy files
			for x in jjw:
				try:
					jx = x.split('---')
					src = DirFolder + '/NGsetting/SelectFolder/' + jx[0]
					dst = '/etc/enigma2/'

					# Use shutil.copy instead of os.system
					if exists(src):
						copy(src, dst)
				except Exception as e:
					# Log the error if something goes wrong with file copying
					logger.exception(f"Error transferring personal setting: {e}")
					pass
		except Exception as e:
			# Log the error if the SelectBack file can't be read
			logger.exception(f"Error reading SelectBack file: {e}")
			pass
		return True

	def CreateUserbouquetPersonalSetting():
		try:
			# Open the SelectBack file with 'with' to ensure it's properly closed
			with open('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/SelectBack', 'r') as jw:
				jjw = jw.readlines()
		except Exception as e:
			logger.exception(f"Error reading SelectBack file: {e}")
			jjw = []

		try:
			# Open the bouquets.tv file and read lines
			with open("/etc/enigma2/bouquets.tv", 'r') as jRewriteBouquet:
				RewriteBouquet = jRewriteBouquet.readlines()

			with open("/etc/enigma2/bouquets.tv", "w") as WriteBouquet:
				Counter = 0
				for xx in RewriteBouquet:
					if Counter == 1:
						for x in jjw:
							if x[0].strip() != '':
								try:
									jx = x.split('---')
									WriteBouquet.write(f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "{jx[0].strip()}" ORDER BY bouquet\n')
								except Exception as e:
									logger.exception(f"Error writing service line: {e}")
									pass
						WriteBouquet.write(xx)
					else:
						WriteBouquet.write(xx)
					Counter += 1
		except Exception as e:
			logger.exception(f"Error processing bouquets.tv: {e}")
			pass

	# added for IPTV
	def KeepIPTV():
		iptv_to_save = SearchIPTV()
		if iptv_to_save:
			for iptv in iptv_to_save:
				try:
					# Copia il file IPTV nella cartella temporanea
					src = "/etc/enigma2/" + iptv
					dst = DirFolder + "/NGsetting/Temp/enigma2/" + iptv
					logger.info("Copying IPTV file: %s to %s", src, dst)

					# Utilizzo di shutil per copiare i file
					copy(src, dst)
					logger.info("IPTV file %s copied successfully.", iptv)
				except Exception as e:
					logger.error("Error copying IPTV file %s: %s", iptv, str(e))

	def TransferNewSetting():
		try:

			def copytree_compat(src, dst):
				if not exists(dst):
					makedirs(dst)
				for item in listdir(src):
					s = join(src, item)
					d = join(dst, item)
					if isdir(s):
						copytree_compat(s, d)
					else:
						copy2(s, d)

			copytree_compat(DirFolder + "/NGsetting/Temp/enigma2", "/etc/enigma2")
		except Exception as e:
			logger.error(f"Copy failed: {e}")
			return False
		return True

	Status = True
	if int(type) == 1:
		SavingProcessTerrestrialChannels = StartSavingTerrestrialChannels()
		try:
			if exists(DirFolder + '/NGsetting/enigma2'):
				rmtree(DirFolder + '/NGsetting/enigma2')
			copytree('/etc/enigma2/', DirFolder + '/NGsetting/enigma2')
		except Exception as e:
			logger.exception(f"Error copying Enigma2 directory: {e}")
			Status = False

	if not DownloadSettingAgg(link):
		try:
			copytree(DirFolder + '/NGsetting/enigma2', '/etc/enigma2', dirs_exist_ok=True)
			rmtree(DirFolder + '/NGsetting/enigma2')
		except Exception as e:
			logger.exception(f"Error copying settings: {e}")
			Status = False
	else:
		personalsetting = False
		if int(Personal) == 1:
			personalsetting = SavePersonalSetting()
		if TransferNewSetting():
			if personalsetting:
				if TransferPersonalSetting():
					CreateUserbouquetPersonalSetting()
					try:
						rmtree(DirFolder + '/NGsetting/SelectFolder')
						move('/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/SelectBack',
							 '/usr/lib/enigma2/python/Plugins/Extensions/NGsetting/Moduli/NGsetting/Select')
					except Exception as e:
						logger.exception(f"Error with personal setting transfer: {e}")
						Status = False
			try:
				rmtree(DirFolder + '/NGsetting/enigma2')
			except Exception as e:
				logger.exception(f"Error removing NGsetting/enigma2: {e}")
				Status = False
		else:
			try:
				copytree(DirFolder + "/NGsetting/enigma2", "/etc/enigma2", dirs_exist_ok=True)
				temp_folder = DirFolder + "/NGsetting/Temp"
				if exists(temp_folder):
					for item in listdir(temp_folder):
						item_path = join(temp_folder, item)
						try:
							if isdir(item_path):
								rmtree(item_path)
							else:
								remove(item_path)
						except Exception as e:
							logger.error("Failed to delete %s: %s", item_path, str(e))
				else:
					logger.warning("Temp folder does not exist: %s", temp_folder)
			except Exception as e:
				logger.exception("Error restoring Enigma2 settings: %s", str(e))
				Status = False

			Status = False

		if int(type) == 1 and Status:
			if SavingProcessTerrestrialChannels:
				if LamedbRestore():
					TransferBouquetTerrestrialFinal()

	# Optionally remove temporary files, but ensure it is commented or checked before actual deletion
	# try:
	#     shutil.rmtree(DirFolder + '/NGsetting/Temp/*')
	# except Exception as e:
	#     logger.exception(f"Error removing temporary files: {e}")
	return Status
