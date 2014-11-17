import os, re

from sys import argv, exit
from json import dumps, loads

from fabric.api import settings, local
from fabric.operations import prompt

from utils import build_config, verify_config

def build_image(config):
	whoami = local('whoami', capture=True)

	docker_vars = [
		('SUPER_PACKAGE', "CompassFrontend"),
		('USER', whoami),
		('USER_PWD', "unveillance"),
		('ssh_root', "/home/%s/.ssh" % whoami),
		('MAIN_PORT', 8888)
	]
	
	sec_vars = [
		('annex_local', "/home/%s/annex" % whoami),
		('gdrive_auth_no_ask', True)
	]

	if 'secrets' in config.keys() and 'secrets_file' in config['secrets'].keys():
		try:
			with open(config['secrets']['secrets_file'], 'rb') as C:
				annex_config = loads(C.read())
				config['secrets'].update(annex_config)

				del config['secrets']['secrets_file']
		except Exception as e:
			print "bad secrets file"
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