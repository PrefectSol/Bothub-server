import argparse
import os
import json
import subprocess

def disable_net(opt) -> int:
    try:        
        with open(opt.config, 'r') as file:
            config = json.load(file)
    except Exception as e:
        print(f'ERROR: configuration not found: {e}')
        return 1

    if not os.path.isfile(config['platform-file']):
        print('The platform instance does not exist.')
        return 1

    with open(config['platform-file'], 'rb') as file:
        data = json.loads(file.read().decode(config['encoding-std']))

    if not data['NetModule']:
        print('The network module is already disabled.')
        return 1
    
    subprocess.run(['docker', 'kill', '-s', 'SIGUSR1', data['dpid']])
    
    data['NetModule'] = False
    with open(config['platform-file'], 'wb') as file:
        file.write(json.dumps(data).encode(config['encoding-std']))
        
    print('The network module has been disabled.')
    
    return 0


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='platform/platform-config.json', help='path to platform-config.json')

    return parser.parse_args()


if __name__ == '__main__':
    opt = parse_opt()
    exit(disable_net(opt))
