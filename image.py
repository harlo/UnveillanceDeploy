import os, re

from sys import argv, exit
from time import time
from json import dumps, loads

from fabric.api import settings, local
from fabric.operations import prompt

def clean_up():
	with settings(warn_only=True):
		local("rm -rf lib")
		
	return True

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
		('ssh_root', "/home/unveillance/.ssh")
	]
	
	sec_vars = [
		('annex_dir', "/home/unveillance/annex"),
		('uv_server_host', "localhost"),
		('uv_uuid', "unveillance_annex")
	]

	# 'proxy_set_header Cookie "$http_cookie;$uv_public";'
	nginx_vars = [
		('client_max_body_size', 20),
		('mode', 1),
		('proxy_extras', ""),
		('proxy_main_port', 8889)
	]

	for d in [('docker', docker_vars), ('secrets', sec_vars), ('nginx', nginx_vars)]:
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
		return not clean_up()

	replacements = [
		("Dockerfile.init.example", docker_vars, 'docker'),
		("install.sh.example", docker_vars, 'docker'),
		("run.sh.example", docker_vars, 'docker'),
		("nginx.conf.example", nginx_vars, 'nginx')
	]
	
	for f in replacements:
		with open(f[0].replace(".example","").replace(".init",""), 'wb') as t:
			t.write(''.join(builld_config(f, config)))

	config['secrets']['ssh_root'] = config['docker']['ssh_root']

	if not os.path.exists("lib"):
		with settings(warn_only=True):
			local("mkdir lib")

	with open("lib/unveillance.secrets.json", 'wb') as t:
		t.write(dumps(config['secrets']))

	with settings(warn_only=True):
		local("mv nginx.conf lib")
		local("mv install.sh lib")
		local("mv run.sh lib")
		local("chmod +x lib/*.sh")

	print "****************************** [ IMPORTANT!!!! ] ******************************"
	print "The next few commands require sudo."
	print "If you can do sudo without a password, press ENTER."
	print "Or else, type it in here"
	sudo_pwd = prompt("[DEFAULT None]: ")

	c_map = {
		'a' : config['docker']['ANNEX_USER'],
		'p' : config['docker']['SUPER_PACKAGE'],
		'h' : os.path.join("home", config['docker']['ANNEX_USER']),
		's' : "sudo" if len(sudo_pwd) == 0 else "echo \"%s\" | sudo -S" % sudo_pwd,
		'd' : ("unveillance/%s-%s" % (
			config['docker']['SUPER_PACKAGE'], config['docker']['ANNEX_USER'])).lower()
	}

	with settings(warn_only=True):
		image_id = None
		local("mv %(p)s lib" % (c_map))

		# BUILD CONTAINER
		build_cmd = "%(s)s docker build -t %(d)s ." % (c_map)

		for status in local(build_cmd, capture=True).splitlines():
			print "XX: %s" % status
			try:
				image_id = re.findall(r'Successfully built ([\w]{12})', status)[0]
				break
			except Exception as e:
				pass
		
		del c_map['s']
		local("mv lib/%(p)s ." % (c_map))

		if image_id is None:
			print "SORRY NO IMAGE"
			return not clean_up()
	
	# write commands to a file
	run_cmd = "sudo docker run --name unveillance_stub -i -t %(d)s" % (c_map)
	print run_cmd

	commit_as = ("%(p)s:%(a)s" % (c_map)).lower()		
	print commit_as

	with open("commit_image.txt", 'wb') as c:
		c.write("\n".join([run_cmd, commit_as]))

	config['docker']['BUILT_PACKAGE'] = commit_as
	docker_vars.append(('BUILT_PACKAGE', commit_as))

	with open("Dockerfile", 'wb') as c:
		c.write("".join(builld_config(("Dockerfile.commit.example", docker_vars, 'docker'), config)))

	return clean_up()

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