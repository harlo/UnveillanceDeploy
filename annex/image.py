from vars import docker_vars
from utils import make_assets

def build_image(config):
	config['secrets']['ssh_root'] = config['docker']['ssh_root']

	default_ports = " ".join([str(p) for p in [config['docker']['MAIN_PORT'], config['docker']['MAIN_PORT'] + 1]])
	config['docker']['EXTRA_PORTS'] = " ".join([default_ports, config['docker']['EXTRA_PORTS']])

	return make_assets("annex", config, docker_vars)