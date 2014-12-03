import os
from json import loads, dumps
from sys import argv, exit

if __name__ == "__main__":	
	if len(argv) < 2:
		exit(-1)

	if argv[1] == "frontend":
		from frontend.vars import docker_vars, sec_vars
		from frontend.image import build_image
	elif argv[1] == "annex":
		from annex.vars import docker_vars, sec_vars
		from annex.image import build_image
	else:
		exit(-1)

	config = None

	if len(argv) == 3:
		config = argv[2]

	if config is None and os.path.exists(os.path.join(argv[1], "last_config.json")):
		from fabric.operations import prompt

		use_last_config = prompt("Use last configuration (y or n)? [DEFAULT y]: ")
		if len(use_last_config) == 0 or use_last_config == "y":
			config = os.path.join(argv[1], "last_config.json")

	if config is None:
		config = {}
	elif type(config) is str:
		try:
			with open(config, 'rb') as c:
				config = loads(c.read())
		except Exception as e:
			print e
			exit(-1)

	return_dir = os.getcwd()
	os.chdir(argv[1])		

	from utils import verify_config
	config = verify_config(config, [('docker', docker_vars), ('secrets', sec_vars)])

	with open("last_config.json", 'wb+') as c:
		c.write(dumps(config))

	res = build_image(config)
	os.chdir(return_dir)
	exit(0 if res else -1)