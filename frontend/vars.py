docker_vars = [
	('SUPER_PACKAGE', "CompassFrontend"),
	('USER', "unveillance"),
	('ssh_root', "/home/unveillance/.ssh"),
	('MAIN_PORT', 8888),
	('ANNEX_PACKAGE', "CompassAnnex"),
	('ANNEX_PORTS', "8889 8890 22 9200")
]

sec_vars = [
	('annex_local', "/home/unveillance/annex_local"),
	('gdrive_auth_no_ask', True)
]