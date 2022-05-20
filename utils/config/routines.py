import configparser

def new_instance(section=None):
    config_info = configparser.ConfigParser()
    if section is not None:
        config_info.add_section(section)

    return config_info


def read_config(config_file_path):
    config_info = configparser.ConfigParser()
    config_info.read(config_file_path)
    return config_info


def write_config(config_info, config_file_path):
    with open(config_file_path, 'w') as config_file:
        config_info.write(config_file)
