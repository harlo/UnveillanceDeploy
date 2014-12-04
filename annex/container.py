import json, sys, os, re
from fabric.api import local, settings
from fabric.context_managers import hide

def get_config(package_name, as_local=True):
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
		package_config = {'secrets' : json.loads(package_config), 'docker' : {}}

	s = package_config['secrets']['server_port']
	m = package_config['secrets']['server_message_port']
	package_config['secrets']['server_user'] = c_map['u']

	annex_ports = []
	as_local = bool(as_local)

	if as_local:
		package_config['secrets'].update({
			'annex_remote_port' : c_map['p'],
			'server_port' : int(config['HostConfig']['PortBindings']['%d/tcp' % s][0]['HostPort']),
			'server_message_port' : int(config['HostConfig']['PortBindings']['%d/tcp' % m][0]['HostPort']),
			'server_force_ssh' : True
		})

	else:
		package_config['secrets'].update({
			'annex_local' : os.path.join(c_map['h'], "annex_local"),
			'ssh_root' : os.path.join(c_map['h'], ".ssh")
		})

		package_config['docker'].update({
			'MAIN_PORT' : 8888,
			'ssh_root' : package_config['secrets']['ssh_root']
		})

	for p in config['HostConfig']['PortBindings'].keys():
		annex_ports.append(str(p.replace("/tcp", "")))

	package_config['docker'].update({
		'USER' : package_config['secrets']['server_user'],
		'ANNEX_PACKAGE' : package_name,
		'ANNEX_PORTS' : " ".join(annex_ports)
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