import json, sys, os, re
from fabric.api import local, settings
from fabric.context_managers import hide

def get_config(package_name, save_as=None):
	try:
		config = json.loads(sys.stdin.read())[0]
	except Exception as e:
		print e
		return

	c_map = {
		'p' : int(config['HostConfig']['PortBindings']['22/tcp'][0]['HostPort']),
		'o' : "PubkeyAuthentication=no",
		'u' : config['Config']['User'],
		'h' : str(config['Config']['WorkingDir']),
		'a' : package_name
	}

	package_config = None

	cmd = "ssh -f -o %(o)s -p %(p)d %(u)s@localhost 'source ~/.bash_profile && cd %(h)s/%(a)s/lib/Annex && python unveillance_annex.py -config'" % (c_map)
	
	with settings(hide('everything'), warn_only=True):	
		sentinel_found = False
		for line in local(cmd, capture=True).splitlines():
			if re.match(r'THE FOLLOWING LINES MAKE FOR YOUR FRONTEND CONFIG', line):
				sentinel_found = True
				continue

			if not sentinel_found:
				continue

			try:
				if line[0] == '{' and line[-1] == '}':
					package_config = line
					break
			except Exception as e:
				continue

	if package_config is not None:
		package_config = json.loads(package_config)

	s = package_config['server_port']
	m = package_config['server_message_port']

	package_config.update({
		'annex_remote_port' : c_map['p'],
		'server_port' : int(config['HostConfig']['PortBindings']['%d/tcp' % s][0]['HostPort']),
		'server_message_port' : int(config['HostConfig']['PortBindings']['%d/tcp' % m][0]['HostPort']),
		'server_force_ssh' : True,
		'server_user' : c_map['u']
	})

	i = "%s.%s" % (config['Config']['Image'].replace(":", "-"), config['Config']['Hostname'])

	if not os.path.exists("configs"):
		with settings(hide('everything'), warn_only=True):
			local("mkdir configs")

	with open("configs/%s.json" % i, 'wb+') as C:
		C.write(json.dumps(package_config))

	print i

def import_user(package_name, key_file):
	try:
		config = json.loads(sys.stdin.read())[0]
	except Exception as e:
		return

	c_map = {
		'p' : int(config['HostConfig']['PortBindings']['22/tcp'][0]['HostPort']),
		'o' : "PubkeyAuthentication=no",
		'u' : config['Config']['User'],
		'h' : str(config['Config']['WorkingDir']),
		'a' : package_name,
		'n' : os.path.basename(key_file),
		'k' : key_file
	}

	cmds = [
		"scp -o %(o)s -P %(p)d %(k)s %(u)s@localhost:%(h)s/.ssh" % (c_map),
		"ssh -f -o %(o)s -p %(p)d %(u)s@localhost 'source ~/.bash_profile && cd %(h)s/%(a)s/lib/Annex && python import_key.py %(h)s/.ssh/%(n)s'" % (c_map)
	]

	print " && ".join(cmds)