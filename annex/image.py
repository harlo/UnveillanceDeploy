import os

from sys import argv, exit
from time import time
from json import dumps, loads

from fabric.operations import prompt

from utils import make_assets, verify_config

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

	config['secrets']['ssh_root'] = config['docker']['ssh_root']

	default_ports = " ".join([str(p) for p in [config['docker']['MAIN_PORT'], config['docker']['MAIN_PORT'] + 1]])
	config['docker']['EXTRA_PORTS'] = " ".join([default_ports, config['docker']['EXTRA_PORTS']])

	return make_assets("annex", config, docker_vars)