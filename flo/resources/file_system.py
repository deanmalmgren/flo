import os
import hashlib

from .base import BaseResource


class FileSystem(BaseResource):
    """Evaluate the state of resources on the file system.
    """

    def __init__(self, *args, **kwargs):
        super(FileSystem, self).__init__(*args, **kwargs)
        self.resource_path = os.path.realpath(
            os.path.join(self.root_directory, self.name)
        )

    def file_state(self, resource_path=None):
        with open(resource_path or self.resource_path) as stream:
            state = self.get_stream_state(stream)
        return state

    def directory_state(self):
        state_hash = hashlib.sha1()
        for root, directories, filenames in os.walk(self.resource_path):
            for filename in filenames:
                abs_filename = os.path.join(root, filename)
                state_hash.update(self.file_state(abs_filename))
        return state_hash.hexdigest()

    def get_current_state(self):
        if not os.path.exists(self.resource_path):
            return None
        elif os.path.isfile(self.resource_path):
            return self.file_state()
        elif os.path.isdir(self.resource_path):
            return self.directory_state()
        else:
            raise NotImplementedError((
                "file a feature request to support this type of "
                "resource "
                "https://github.com/deanmalmgren/flo/issues"
            ))

    def get_filename(self):
        return self.name
