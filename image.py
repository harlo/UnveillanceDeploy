import os, re

from sys import argv, exit
from time import time
from json import dumps, loads

from fabric.api import settings, local
from fabric.operations import prompt

def builld_config(f, config):
	file_ = []
	rx = re.compile("\$\{(%s)\}" % '|'.join([d[0] for d in f[1]]))

	with open(f[0], 'rb') as stub:
		for line in [line for line in stub.readlines()]:
			for e in re.findall(rx, line):
				try:
					line = line.replace("${%s}" % e, str(config[f[2]][e]))
				except Exception as ex:
					print e, ex, type(ex)
		
			file_.append(line)

	return file_

def build_image(config):
	docker_vars = [
		('SUPER_PACKAGE', "CompassAnnex"),
		('ANNEX_USER', "unveillance"),
		('ANNEX_USER_PWD', "unveillance"),
		('ssh_root', "/home/unveillance/.ssh"),
		('EXTRA_PORTS', ""),
		('MAIN_PORT', 8889)
	]
	
	sec_vars = [
		('annex_dir', "/home/unveillance/annex"),
		('uv_server_host', "localhost"),
		('uv_uuid', "unveillance_annex")
	]

	for d in [('docker', docker_vars), ('secrets', sec_vars)]:
		if d[0] not in config.keys():
			config[d[0]] = {}

		for e in d[1]:
			if e[0] not in config[d[0]].keys():
				hint = "" if type(e[1]) is not list else "(space-separated values) "

				directive = prompt("%s [DEFAULT %s%s]: " % (e[0], hint, e[1]))

				if len(directive) == 0:
					directive = e[1]

				if type(e[1]) is list:
					directive = directive.split(' ')

				config[d[0]][e[0]] = directive

	with open("last_config.json", 'wb') as c:
		c.write(dumps(config))

	# check to see if user has submodule first
	if not os.path.exists(config['docker']['SUPER_PACKAGE']):
		print "You don't have package %s installed.\nAdd it by running git submodule add [URL]"
		return False

	default_ports = " ".join([str(p) for p in [config['docker']['MAIN_PORT'], config['docker']['MAIN_PORT'] + 1]])
	config['docker']['EXTRA_PORTS'] = " ".join([default_ports, config['docker']['EXTRA_PORTS']])
	print config['docker']['EXTRA_PORTS']

	replacements = [
		("Dockerfile.init.example", docker_vars, 'docker'),
		("install.sh.example", docker_vars, 'docker'),
		("run.sh.example", docker_vars, 'docker')
	]

	if not os.path.exists("lib"):
		with settings(warn_only=True):
			local("mkdir lib")
			local("mkdir lib/make")
	
	for f in replacements:
		with open(os.path.join("lib", f[0].replace(".example","")), 'wb') as t:
			t.write(''.join(builld_config(f, config)))

	config['secrets']['ssh_root'] = config['docker']['ssh_root']

	with open("lib/make/unveillance.secrets.json", 'wb') as t:
		t.write(dumps(config['secrets']))

	with settings(warn_only=True):
		local("mv lib/install.sh lib/make")
		local("mv lib/run.sh lib/make")
		local("chmod +x lib/make/*.sh")

	c_map = {
		'a' : config['docker']['ANNEX_USER'],
		'p' : config['docker']['SUPER_PACKAGE'],
		'h' : os.path.join("home", config['docker']['ANNEX_USER']),
		'd' : ("unveillance/%s-%s" % (
			config['docker']['SUPER_PACKAGE'], config['docker']['ANNEX_USER'])).lower()
	}

	cmds = [
		"cd lib",
		"mv ../%(p)s make" % (c_map),
		"mv Dockerfile.init Dockerfile",
		"sudo docker build -t %(d)s ." % (c_map),
		"mv make/%(p)s ../" % (c_map),
		"sudo docker run --name unveillance_stub -it %(d)s" % (c_map),
		"mv Dockerfile.commit Dockerfile",
		"sudo docker start unveillance_stub",
		"sudo docker commit unveillance_stub %(p)s:%(a)s" % (c_map),
		"sudo docker build -t %(p)s:%(a)s ." % (c_map),
		"sudo docker rm unveillance_stub",
		"cd ../",
		"echo \"Finished building!  Now try:\"",
		"echo \"sudo docker run -iPt %(p)s:%(a)s\"" % (c_map)
	]

	with open("lib/commit_image.txt", 'wb') as c:
		c.write("\n".join(cmds))

	config['docker']['BUILT_PACKAGE'] = "%(p)s:%(a)s" % (c_map)
	docker_vars.append(('BUILT_PACKAGE', "%(p)s:%(a)s" % (c_map)))

	with open("lib/Dockerfile.commit", 'wb') as c:
		c.write("".join(builld_config(("Dockerfile.commit.example", docker_vars, 'docker'), config)))

	return True

if __name__ == "__main__":
	config = None

	if len(argv) == 2:
		config = argv[1]

	if config is None and os.path.exists("last_config.json"):
		use_last_config = prompt("Use last configuration (y or n)? [DEFAULT y]: ")
		if len(use_last_config) == 0 or use_last_config == "y":
			config = "last_config.json"

	if config is None:
		config = {}
	elif type(config) is str:
		try:
			with open(config, 'rb') as c:
				config = loads(c.read())
		except Exception as e:
			print e
			exit(-1)
	else:
		exit(-1)

	if build_image(config):
		exit(0)
	
	exit(-1)