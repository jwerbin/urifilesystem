"""
URIFilesystem is unified interface to access data stored at any location that has a supported fsspec style implementation.
It abstracts away the specifics of how to access data through different protocols.
A single URIFilesystem object will be able to interact with mutliple system through the same method calls. e.g.

```
files = ['~./readme.txt', 's3://my_bucket/readme.txt', 'sftp://my_server.com/readme.txt', 'file://home/me/readme.txt']
fs = URIFilesystem()
for f in files:
    with fs.open(f, mode='r') as fid:
        print(f'File {f}:')
        print(fid.read(), '\n\n')
```

"""
from functools import partial
from typing import Dict, Optional
from urllib.parse import urlparse
from fsspec.spec import AbstractFileSystem


class URIFilesystem(AbstractFileSystem):
    """
    URIFilesystem is unified interface to access data stored at any location that has a supported fsspec style implementation.

    This class is reponsible for owning the FileSystem dictionary object.
    Presenting a uniform system interface and ensure the the returned values are uniform and meet the following criteria.
    1. If a path is returned the paths are full formed (can be passed back to a URIFilesystem objects)
       e.g. some of the filesystems will return the paths without the scheme or locations.
    
    Note: inherit from AbstractFilesystem for documentation purposes
    """
    _methods_to_expose = ['mkdir', 'mkdirs', 'rmdir', 'ls', 'walk', 'find', 'du', 'glob', 'exists', 'info', 'checksum', 'size', 
                          'sizes', 'isdir', 'isfile', 'pipe_file', 'pipe', 'cat', 'head', 'tail', 'copy', 'rm', 'open', 'touch']

    def __init__(self, credentials: Optional[Dict[str, Dict]] = None) -> None:
        """
        Creates a URIFilesystem object.

        inputs:

            credentials,    A dict containing credentials for specific systems (if needed). If no creditials are provided 
                            accesss will be atempted without credentials. The keys to this dict should be of the form.
                            f'{scheme}://{netloc}' where netloc can be '' if there are generic parameters for a particular scheme.
                            When a Uri is used  they system will always try to use the more specific parameters if they have been 
                            provided.
        """
        # Don't actually initialize the base class. It is used purely for documentation.
        self._filesystems = FileSystemContainer(credentials=credentials)
        self._setup_interface()

    def _setup_interface(self):
        for method_name in self._methods_to_expose:
            setattr(self, method_name, partial(self._method_call, method_name))
            # Get the doc string from the AbstractFileSystem
            getattr(self, method_name).__doc__ = getattr(super(), method_name).__doc__

    def _method_call(self, method: str, path: str, *args, **kwargs):
        return getattr(self._filesystems.get(path), method)(*args, **kwargs)
