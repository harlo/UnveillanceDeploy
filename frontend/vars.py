from fabric.api import local
whoami = local('whoami', capture=True)

docker_vars = [
	('SUPER_PACKAGE', "CompassFrontend"),
	('USER', whoami),
	('USER_PWD', "unveillance"),
	('ssh_root', "/home/%s/.ssh" % whoami),
	('MAIN_PORT', 8888)
]

sec_vars = [
	('annex_local', "/home/%s/annex" % whoami),
	('gdrive_auth_no_ask', True)
]