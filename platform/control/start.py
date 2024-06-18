import argparse
import os
import json
import subprocess


def start(opt) -> int:
    try:        
        with open(opt.config, 'r') as file:
            config = json.load(file)
    except Exception as e:
        print(f'ERROR: configuration not found: {e}')
        return 1

    if os.path.isfile(config['platform-file']):
        print('ERROR: An instance of the platform already exists. The existence of more than one platform is not allowed.')
        return 1

    dpid = subprocess.check_output(['docker', 'run', '-v',
                                    f'{os.path.join(os.getcwd(), config["database"])}:/bothub-platform/database',
                                    '-d', 'bothub-platform'])

    data = {
        'dpid': dpid.decode(config['encoding-std']).strip(),
        'NetModule': False
    }

    with open(config['platform-file'], 'wb') as file:
        file.write(json.dumps(data).encode(config['encoding-std']))
    
    print('START: An instance of the platform has been started and written to a file:', config['platform-file'])
    
    return 0


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='platform/platform-config.json', help='path to platform-config.json')

    return parser.parse_args()


if __name__ == '__main__':
    opt = parse_opt()
    exit(start(opt))
