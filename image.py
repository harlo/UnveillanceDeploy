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

	return False

def build_image(config):
	docker_vars = ['SUPER_PACKAGE', 'ANNEX_USER']
	sec_vars = ['']

	for e in docker_vars + sec_vars:
		if e not in config.keys():
			config[e] = prompt("%s: " % e)

	dockerfile = []
	doc_rx = re.compile("\$\{(%s)\}" % '|'.join(docker_vars))
	with open("Dockerfile.example", 'rb') as dockerstub:
		for line in [line.strip() for line in dockerstub.readlines()]:
			for e in re.findall(doc_rx, line):
				line = line.replace("${%s}" % e, config[e])
			
			dockerfile.append(line)

	# first, do we have a stock build for the annex user?
	with open("Dockerfile", 'wb') as t:
		t.write('\n'.join(dockerfile))

	unveillance_secrets = {}
	for s in sec_vars:
		unveillance_secrets[s] = config[s]

	with open("unveillance.secrets.json", 'wb') as t:
		t.write(dumps(unveillance_secrets))

	with settings(warn_only=True):
		image_id = None
		build_cmd = "sudo docker build -t unveillance/stock:%s ." % config['ANNEX_USER']

		for status in local(build_cmd, capture=True).splitlines():
			print "XX: %s" % status
			try:
				image_id = re.findall(r'Successfully built ([\w]{12})', status)[0]
				break
			except Exception as e:
				pass
		
		if image_id is None:
			print "SORRY NO IMAGE"
			return clean_up()

		container_id = None
		run_cmd = "sudo docker run -d -t && cd %(h)s && ./setup.sh %(h)s/unveillance.secrets.json" % (
			{'h' : os.path.join(config['ANNEX_USER'], config['SUPER_PACKAGE'])})

		for status in local(run_cmd, capture=True).splitlines():
			print "XX: %s" % status

		#for status in local("sudo docker commit %s unveillance/annex:blank" % image_id, capture=True).splitlines():
			#print "XX: %s" % status

	return not clean_up()

if __name__ == "__main__":
	if len(argv) == 2:
		config = argv[1]
	else:
		config = {}

	if build_image(config):
		exit(0)

	exit(-1)

	#! /bin/bash
	# SUPER_PACKAGE: the superclass'ed version of Unveillance you created (i.e. InformaAnnex, CompassAnnex)
	#SUPER_PACKAGE=$1

	#cat Dockerfile | envsubst | sudo docker build -t unveillance/stock -

	# Run & Commit the stub image
	#sudo docker commit -m