import argparse
import os
import json


def status(opt) -> int:
    try:        
        with open(opt.config, 'r') as file:
            config = json.load(file)
    except Exception as e:
        print(f'ERROR: configuration not found: {e}')
        return 1

    if not os.path.isfile(config['platform-file']):
        print('STATUS: The platform instance does not exist.')
        return 1

    with open(config['platform-file'], 'rb') as file:
        data = json.loads(file.read().decode(config['encoding-std']))

    print('STATUS: The platform instance is exists.')
    print(json.dumps(data, indent=4))
    
    return 0


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='platform/platform-config.json', help='path to platform-config.json')

    return parser.parse_args()


if __name__ == '__main__':
    opt = parse_opt()
    exit(status(opt))
