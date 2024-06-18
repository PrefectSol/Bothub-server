import argparse
import os
import json
import subprocess


def stop(opt) -> int:
    try:        
        with open(opt.config, 'r') as file:
            config = json.load(file)
    except Exception as e:
        print(f'ERROR: configuration not found: {e}')
        return 1

    if not os.path.isfile(config['platform-file']):
        print('ERROR: The platform instance does not exist.')
        return 1

    with open(config['platform-file'], 'rb') as file:
        dpid = json.loads(file.read().decode(config['encoding-std']))['dpid']

    print(f'STOP: The platform has started to stop: wait {config["control"]["stop-timeout"]} seconds')

    subprocess.run(['docker', 'stop', '-t', str(config['control']['stop-timeout']), dpid])
    result = subprocess.run(['docker', 'logs', dpid], capture_output=True, text=True)
    
    print('\nDocker process stderr:')
    print(result.stderr)
    print('Docker process stdout:')
    print(result.stdout)
    
    if os.path.isfile(config['platform-file']):
        os.remove(config['platform-file'])
    
    return 0


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='platform/platform-config.json', help='path to platform-config.json')

    return parser.parse_args()


if __name__ == '__main__':
    opt = parse_opt()
    exit(stop(opt))
