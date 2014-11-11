import os, re

from sys import argv, exit
from time import time
from json import dumps, loads
from fabric.api import settings, local
from fabric.operations import prompt

def clean_up():
	with settings(warn_only=True):
		local("rm Dockerfile")
		local("rm unveillance.secrets.json")
		local("rm nginx.conf")

	return True

def build_image(config):
	docker_vars = [
		('SUPER_PACKAGE', "UnveillanceAnnex"),
		('ANNEX_USER', "unveillance"),
		('ANNEX_USER_PWD', "unveillance")
	]
	
	sec_vars = [
		('ssh_root', "/home/unveillance/.ssh"),
		('annex_dir', "/home/unveillance/unveillance_remote"),
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
			if e not in config[d[0]].keys():
				directive = prompt("%s [DEFAULT %s]: " % (e[0], e[1]))

				if len(directive) == 0:
					directive = e[1]

				config[d[0]][e[0]] = directive

	dockerfile = []
	doc_rx = re.compile("\$\{(%s)\}" % '|'.join([d[0] for d in docker_vars]))
	with open("Dockerfile.example", 'rb') as dockerstub:
		for line in [line.strip() for line in dockerstub.readlines()]:
			for e in re.findall(doc_rx, line):
				line = line.replace("${%s}" % e, config['docker'][e])
			
			dockerfile.append(line)

	# first, do we have a stock build for the annex user?
	with open("Dockerfile", 'wb') as t:
		t.write('\n'.join(dockerfile))

	nginxfile = []
	ngx_rx = re.compile("\${(%s)\}" % '|'.join([n[0] for n in nginx_vars]))
	with open("nginx.conf.example", 'rb') as nginxstub:
		for line in nginxstub.readlines():
			for e in re.findall(ngx_rx, line):
				line = line.replace("${%s}" % e, config['nginx'][e])

		nginxfile.append(line)

	with open("nginx.conf", 'wb') as t:
		t.write(''.join(nginxfile))
	
	with open("unveillance.secrets.json", 'wb') as t:
		t.write(dumps(config['secrets']))

	c_map = {
		'a' : config['docker']['ANNEX_USER'],
		'p' : config['docker']['SUPER_PACKAGE'],
		'h' : os.path.join(config['docker']['ANNEX_USER'], config['docker']['SUPER_PACKAGE'])
	}

	with settings(warn_only=True):
		image_id = None

		# BUILD CONTAINER
		build_cmd = "sudo docker build -t unveillance/%(p)s-%(a)s ." % (c_map)

		for status in local(build_cmd, capture=True).splitlines():
			print "XX: %s" % status
			try:
				image_id = re.findall(r'Successfully built ([\w]{12})', status)[0]
				break
			except Exception as e:
				pass
		
		if image_id is None:
			print "SORRY NO IMAGE"
			return not clean_up()

		container_id = None

		# RUN SETUP ON IN IT AND CLOSE
		run_cmd = "sudo docker run -i -t unveillance/%(p)s-%(a)s /bin/bash cd %(h)s && ./setup.sh %(h)s/unveillance.secrets.json && ./shutdown.sh" % (c_map)

		for status in local(run_cmd, capture=True).splitlines():
			print "XX: %s" % status
			try:
				container_id = re.findall(r'Successfully built ([\w]{12})', status)[0]
				break
			except Exception as e:
				pass

		if container_id is None:
			print "COULD NOT BUILD CONTAINER"
			return not clean_up()

		c_map['c'] = container_id

		# COMMIT CONTAINER FOR DEPLOYMENT
		commit_cmd = "sudo docker commit %(c)s unveillance/%(p)s:%(a)s" % (c_map)
		for status in local(commit_cmd, capture=True).splitlines():
			print "XX: %s" % status

	return clean_up()

if __name__ == "__main__":
	config = {}

	if len(argv) == 2:
		try:
			with open(argv[1], 'rb') as c:
				config = loads(c.read())
		except Exception as e:
			print e

	if build_image(config):
		exit(0)

	exit(-1)