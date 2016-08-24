import yaml
import jinja2
import six


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


class JinjaTemplateError(CommandLineException):
    source_message_prefix = "Original template source"
    error_message_prefix = "Error loading Jinja template"
    tab = "    "

    def __init__(self, template_string, error):
        self.template_string = template_string
        self.error = error

    def indent(self, s):
        return self.tab + s.replace('\n', '\n%s' % self.tab)

    def source_message(self):
        source = self.indent(self.template_string)
        return "%s:\n\n%s" % (self.source_message_prefix, source)

    def error_message(self):
        return "%s: %s\n\n" % (self.error_message_prefix, self.error.message)

    def __str__(self):
        return self.error_message() + self.source_message()


class JinjaRenderError(JinjaTemplateError):
    error_message_prefix = "Jinja template variable is not in context"

    def __init__(self, template_string, error, **context_dict):
        super(JinjaRenderError, self).__init__(template_string, error)
        self.context_dict = context_dict

    def __str__(self):
        context_str = "{\n"
        for k, v in six.iteritems(self.context_dict):
            context_str += "%s%s: %s,\n" % (self.tab, k, v)
        context_str += "}"
        msg = "\n\nContext:\n\n%s" % self.indent(context_str)
        return self.error_message() + self.source_message() + msg


class ShellError(CommandLineException):
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def __str__(self):
        return "Command failed with exit code %s" % self.exit_code


class YamlError(CommandLineException):
    def __init__(self, config_filename, yaml_error):
        self.config_filename = config_filename
        self.yaml_error = yaml_error

    def __str__(self):
        msg = "There was an error loading your YAML configuration file "
        msg += "located at\n%s:\n\n" % self.config_filename
        msg += str(self.yaml_error)

        # provide useful hints here for common problems
        if "{{" in str(self.yaml_error):
            msg += "\n\n"
            msg += "Try quoting your jinja templates if they start with '{{'\n"
            msg += "because YAML interprets an unquoted '{' as the start of\n"
            msg += "a new YAML object."
        return msg
