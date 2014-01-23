import os

# this function needs to be in a separate module because it is used in
# both parser.py and tasks.py
CONFIG_FILENAME = "workflow.yaml"

def find_config_path(config_filename=CONFIG_FILENAME):
    """Recursively decend into parent directories looking for the 
    """

    config_path = ''
    directory = os.getcwd()
    while directory:
        filename = os.path.join(directory, config_filename)
        if os.path.exists(filename):
            config_path = filename
            break
        directory = os.path.sep.join(directory.split(os.path.sep)[:-1])
    if not config_path:
        raise exceptions.ConfigurationNotFound(
            config_filename,
            os.getcwd()
        )
    return config_path

def get_root_directory(config_filename=CONFIG_FILENAME):
    return os.path.dirname(find_config_path(config_filename=config_filename))
