import yaml


class CommandLineException(Exception):
    """convenience exception to make it easy to not print traceback when
    run from the command line
    """
    pass


class ConfigurationNotFound(CommandLineException):
    def __init__(self, config_filename, cwd):
        self.config_filename = config_filename
        self.cwd = cwd

    def __str__(self):
        return "No configuration file called '%s' found in directory\n'%s'" % (
            self.config_filename,
            self.cwd,
        )


class InvalidTaskDefinition(CommandLineException):
    def __init__(self, message, yaml_dict):
        self.message = message
        self.yaml_dict = yaml_dict

    def __str__(self):
        msg = self.message + "; offending task:"
        return "%s\n\n%s" % (msg, yaml.dump(self.yaml_dict))


class ResourceNotFound(CommandLineException):
    def __init__(self, resource):
        self.resource = resource

    def __str__(self):
        return "\nResource '%s' not found" % self.resource


class NonUniqueTask(CommandLineException):
    pass


class ShellError(CommandLineException):
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def __str__(self):
        return "Command failed with exit code %s" % self.exit_code
