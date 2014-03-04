import os

from .base import BaseElement

class FileSystem(BaseElement):
    """Evaluate the state of elements on the file system.
    """

    def get_state(self):
        state = None

        # for filesystem protocols, dereference any soft links that
        # the element may point to and calculate the state from
        element_path = os.path.realpath(
            os.path.join(self.root_directory, self.name)
        )
        if os.path.exists(element_path):
            if os.path.isfile(element_path):
                with open(element_path) as stream:
                    state = self._get_stream_state(stream)
            elif os.path.isdir(element_path):
                state_hash = hashlib.sha1()
                for root, directories, filenames in os.walk(element_path):
                    for filename in filenames:
                        with open(os.path.join(root, filename)) as stream:
                            state_hash.update(self._get_stream_state(stream))
                state = state_hash.hexdigest()
            else:
                raise NotImplementedError((
                    "file a feature request to support this type of "
                    "element "
                    "https://github.com/deanmalmgren/data-workflow/issues"
                ))
        return state
