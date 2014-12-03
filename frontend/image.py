from vars import docker_vars

def build_image(config):
	config['secrets'].update({
		'ssh_root': config['docker']['ssh_root'],
		'api.port' : config['docker']['MAIN_PORT']
	})

	config['docker']['ANNEX_LOCAL'] = config['secrets']['annex_local']
	
	return make_assets("frontend", config, docker_vars)