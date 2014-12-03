import os, re

from sys import argv, exit
from json import dumps, loads

from fabric.api import settings, local
from fabric.operations import prompt

from utils import build_config, verify_config

def build_image(config):
	from vars import sec_vars, docker_vars

	if 'secrets_file' in config.keys():
		try:
			with open(config['secrets_file'], 'rb') as C:
				annex_config = loads(C.read())
				config.update(annex_config)

				del config['secrets_file']
		except Exception as e:
			print "bad secrets file: %s" % e
			return False

	config = verify_config(config, [('docker', docker_vars), ('secrets', sec_vars)])

	with open("last_config.json", 'wb+') as c:
		c.write(dumps(config))

	config['secrets'].update({
		'ssh_root': config['docker']['ssh_root'],
		'api.port' : config['docker']['MAIN_PORT']
	})

	config['docker']['ANNEX_LOCAL'] = config['secrets']['annex_local']
	
	return make_assets("frontend", config, docker_vars)