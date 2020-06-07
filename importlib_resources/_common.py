from __future__ import absolute_import

import os
import tempfile
import contextlib
import types
import importlib

from ._compat import (
    Path, FileNotFoundError,
    singledispatch, package_spec,
    )


def resolve(cand):
    return (
        cand if isinstance(cand, types.ModuleType)
        else importlib.import_module(cand)
        )


def get_package(package):
    """Take a package name or module object and return the module.

    Raise an exception if the resolved module is not a package.
    """
    resolved = resolve(package)
    if package_spec(resolved).submodule_search_locations is None:
        raise TypeError('{!r} is not a package'.format(package))
    return resolved


def from_package(package):
    """
    Return a Traversable object for the given package.

    """
    spec = package_spec(package)
    reader = spec.loader.get_resource_reader(spec.name)
    return reader.files()


@contextlib.contextmanager
def _tempfile(reader, suffix=''):
    # Not using tempfile.NamedTemporaryFile as it leads to deeper 'try'
    # blocks due to the need to close the temporary file to work on Windows
    # properly.
    fd, raw_path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, reader())
        os.close(fd)
        yield Path(raw_path)
    finally:
        try:
            os.remove(raw_path)
        except FileNotFoundError:
            pass


@singledispatch
@contextlib.contextmanager
def as_file(path):
    """
    Given a Traversable object, return that object as a
    path on the local file system in a context manager.
    """
    with _tempfile(path.read_bytes, suffix=path.name) as local:
        yield local


@as_file.register(Path)
@contextlib.contextmanager
def _(path):
    """
    Degenerate behavior for pathlib.Path objects.
    """
    yield path
