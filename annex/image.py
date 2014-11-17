import os

from sys import argv, exit
from time import time
from json import dumps, loads

from fabric.operations import prompt

from utils import make_assets, verify_config

def build_image(config):
	docker_vars = [
		('SUPER_PACKAGE', "CompassAnnex"),
		('USER', "unveillance"),
		('USER_PWD', "unveillance"),
		('ssh_root', "/home/unveillance/.ssh"),
		('EXTRA_PORTS', ""),
		('MAIN_PORT', 8889)
	]
	
	sec_vars = [
		('annex_dir', "/home/unveillance/annex"),
		('uv_server_host', "localhost"),
		('uv_uuid', "unveillance_annex")
	]

	config = verify_config(config, [('docker', docker_vars), ('secrets', sec_vars)])

	with open("last_config.json", 'wb+') as c:
		c.write(dumps(config))

	config['secrets']['ssh_root'] = config['docker']['ssh_root']

	default_ports = " ".join([str(p) for p in [config['docker']['MAIN_PORT'], config['docker']['MAIN_PORT'] + 1]])
	config['docker']['EXTRA_PORTS'] = " ".join([default_ports, config['docker']['EXTRA_PORTS']])

	return make_assets("annex", config, docker_vars)