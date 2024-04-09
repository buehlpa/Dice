import argparse
import json
import sys

def load_config(filename):
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{filename}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in '{filename}': {e}")
        sys.exit(1)

def parse_args(config):
    parser = argparse.ArgumentParser()
    for key, value in config.items():
        parser.add_argument(f'--{key}', default=value, type=type(value))
    return parser.parse_args()


def load_and_parse_args(config_file="config.json"):
    config = load_config(config_file)
    args = parse_args(config)
    return args

if __name__ == "__main__":
    args = load_and_parse_args(config_file="config.json")
    print(args)