import json
def read_config():
    # Read the configuration file
    config = json.load(open("config_web.json"))
    return config

def save_config(config):
    # Save the configuration file
    with open("config_web.json", "w") as f:
        json.dump(config, f, indent=4)
