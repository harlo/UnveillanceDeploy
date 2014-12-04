from vars import docker_vars
from utils import make_assets

def build_image(config):
	config['secrets'].update({
		'ssh_root': config['docker']['ssh_root'],
		'api.port' : config['docker']['MAIN_PORT']
	})

	config['docker']['ANNEX_LOCAL'] = config['secrets']['annex_local']

	c_map = {
		'a' : ("%s:%s" % (
			config['docker']['ANNEX_PACKAGE'], config['docker']['USER'])).lower()
	}

	config['docker']['ANNEX_BUILD'] = c_map['a']
	docker_vars.append(('ANNEX_BUILD', c_map['a']))
	
	return make_assets("frontend", config, docker_vars)