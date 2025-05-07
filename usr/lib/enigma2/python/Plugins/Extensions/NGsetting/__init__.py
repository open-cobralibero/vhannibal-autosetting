# recoded @ lululla 20250507

import logging
from logging.handlers import RotatingFileHandler

from os import makedirs
from os.path import join, exists

log_dir = '/tmp/NGsetting'
log_file = join(log_dir, 'ngsetting.log')

# Create the directory if it doesn't exist
if not exists(log_dir):
	makedirs(log_dir)

logger = logging.getLogger('NGSetting')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler(
	log_file, maxBytes=1 * 1024 * 1024, backupCount=3, encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info('*************** NGSetting Initialized ***************')
