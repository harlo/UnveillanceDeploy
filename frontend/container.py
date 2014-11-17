import json, sys, os, re
from fabric.api import local, settings
from fabric.context_managers import hide

def get_ssh_key():
	try:
		config = json.loads(sys.stdin.read())[0]
	except Exception as e:
		return

	for e in [e.split("=") for e in config['Config']['Env']]:
		if e[0] == "PACKAGE_NAME":
			package_name = e[1]
			break

	c_map = {
		'p' : int(config['HostConfig']['PortBindings']['22/tcp'][0]['HostPort']),
		'o' : "PubkeyAuthentication=no",
		'u' : config['Config']['User'],
		'h' : str(config['Config']['WorkingDir']),
		'a' : package_name
	}

def push_to_annex(asset):
	try:
		config = json.loads(sys.stdin.read())[0]
	except Exception as e:
		return

	if not os.path.exists(asset):
		return

	assets = []
	if os.path.isdir(asset):
		for _, _, files in os.walk(asset):
			assets += files
	else:
		assets = [asset]

	if len(assets) == 0:
		return

	for e in [e.split("=") for e in config['Config']['Env']]:
		if e[0] == "PACKAGE_NAME":
			package_name = e[1]
		elif e[0] == "ANNEX_LOCAL":
			annex_local = e[1]

	c_map = {
		'p' : int(config['HostConfig']['PortBindings']['22/tcp'][0]['HostPort']),
		'o' : "PubkeyAuthentication=no",
		'u' : config['Config']['User'],
		'a' : package_name,
		'f' : " ".join(assets),
		'x' : annex_local
	}

	cmd = "scp -o %(o)s -P %(p)d %(f)s %(u)s@localhost:%(x)s" % (c_map)

	with settings(hide('everything'), warn_only=True):
		print local(cmd, capture=True)