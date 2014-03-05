import os
import hashlib

from .base import BaseResource

class FileSystem(BaseResource):
    """Evaluate the state of resources on the file system.
    """

    @property
    def current_state(self):
        state = None

        # for filesystem protocols, dereference any soft links that
        # the resource may point to and calculate the state from
        resource_path = os.path.realpath(
            os.path.join(self.root_directory, self.name)
        )
        if os.path.exists(resource_path):
            if os.path.isfile(resource_path):
                with open(resource_path) as stream:
                    state = self._get_stream_state(stream)
            elif os.path.isdir(resource_path):
                state_hash = hashlib.sha1()
                for root, directories, filenames in os.walk(resource_path):
                    for filename in filenames:
                        with open(os.path.join(root, filename)) as stream:
                            state_hash.update(self._get_stream_state(stream))
                state = state_hash.hexdigest()
            else:
                raise NotImplementedError((
                    "file a feature request to support this type of "
                    "resource "
                    "https://github.com/deanmalmgren/data-workflow/issues"
                ))
        return state
