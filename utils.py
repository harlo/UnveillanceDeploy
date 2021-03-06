import re, os
from json import dumps
from fabric.api import local, settings
from fabric.operations import prompt

def make_assets(mode, config, docker_vars):
	par_dir = os.path.abspath(os.path.join(__file__, os.pardir))
	this_dir = os.getcwd()

	if not os.path.exists(os.path.join(par_dir, config['docker']['SUPER_PACKAGE'])):
		print "You don't have package %s installed.\nAdd it by running git submodule add [URL]" % config['docker']['SUPER_PACKAGE']
		return False

	os.chdir(os.path.join(par_dir, mode))

	if not os.path.exists("lib"):
		with settings(warn_only=True):
			local("mkdir lib")
			local("mkdir lib/make")

	with open("lib/make/unveillance.secrets.%s.json" % mode, 'wb') as t:
		t.write(dumps(config['secrets']))

	c_map = {
		'a' : config['docker']['USER'],
		'p' : config['docker']['SUPER_PACKAGE'],
		'h' : os.path.join("home", config['docker']['USER']),
		'd' : ("unveillance/%s-%s" % (
			config['docker']['SUPER_PACKAGE'], config['docker']['USER'])).lower(),
		'f' : ("%s:%s" % (
			config['docker']['SUPER_PACKAGE'], config['docker']['USER'])).lower(),
		'r' : par_dir,
		'm' : mode
	}

	config['docker']['BUILT_PACKAGE'] = c_map['f']
	docker_vars.append(('BUILT_PACKAGE', c_map['f']))

	replacements = [
		("Dockerfile.init.example", docker_vars, 'docker'),
		("Dockerfile.commit.example", docker_vars, 'docker'),
		("install.sh.example", docker_vars, 'docker'),
		("run.sh.example", docker_vars, 'docker')
	]
	
	for f in replacements:
		with open(os.path.join("lib", f[0].replace(".example","")), 'wb') as t:
			t.write(''.join(build_config(f, config)))

	with settings(warn_only=True):
		docker_is = local("which docker", capture=True)
	
	if len(docker_is) == 0:
		print "Do you have docker installed?"
		docker_is = prompt("If so, what is its path?")

		if len(docker_is) == 0:
			print "No Docker to use!  Please install docker!"
			return False
	
	c_map['docker_is'] = "sudo %s" % docker_is

	cmds = [
		"cd %(r)s/%(m)s/lib" % (c_map),
		"mv %(r)s/%(p)s make" % (c_map),
		"mv Dockerfile.init Dockerfile",
		"%(docker_is)s build -t %(d)s ." % (c_map),
		"mv make/%(p)s %(r)s" % (c_map),
		"%(docker_is)s run --name unveillance_stub -it %(d)s" % (c_map),
		"mv Dockerfile.commit Dockerfile",
		"%(docker_is)s start unveillance_stub" % (c_map),
		"%(docker_is)s commit unveillance_stub %(f)s" % (c_map),
		"%(docker_is)s stop unveillance_stub" % (c_map),
		"%(docker_is)s build -t %(f)s ." % (c_map),
		"%(docker_is)s rm unveillance_stub" % (c_map),
		"%(docker_is)s rmi %(d)s" % (c_map),
		"cd %(r)s" %(c_map),
		"echo \"Finished building!  Now try:\"",
		"echo \"%(docker_is)s run -iPt %(f)s\"" % (c_map)
	]

	with open("lib/commit_image.txt", 'wb') as c:
		c.write("\n".join(cmds))

	with settings(warn_only=True):
		local("mv lib/install.sh lib/make")
		local("mv lib/run.sh lib/make")
		local("chmod +x lib/make/*.sh")

		if "EXTRA_DATA" in config['docker'].keys() and os.path.exists(config['docker']['EXTRA_DATA']):
			local("cp -R %s/* lib/make" % config['docker']['EXTRA_DATA'])

	os.chdir(this_dir)
	return True

def verify_config(config, vars):
	for d in vars:
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

	return config

def build_config(f, config):
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