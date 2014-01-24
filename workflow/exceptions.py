class ConfigurationNotFound(Exception):
    def __init__(self, config_filename, cwd):
        self.config_filename = config_filename
        self.cwd = cwd

    def __str__(self):
        return "\nNo configuration file called '%s' found in directory\n'%s'"%(
            self.config_filename, 
            self.cwd,
        )

class InvalidTaskDefinition(Exception):
    pass

class ElementNotFound(Exception):
    def __init__(self, element):
        self.element = element

    def __str__(self):
        return "\nElement '%s' not found" % self.element

class NonUniqueTask(Exception):
    pass
