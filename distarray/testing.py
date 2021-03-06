import unittest
import importlib
import tempfile
import os
import types

from uuid import uuid4
from functools import wraps
from distarray.externals import six

from IPython.parallel import Client

from distarray.error import InvalidCommSizeError
from distarray.mpiutils import MPI, create_comm_of_size


def temp_filepath(extension=''):
    """Return a randomly generated filename.

    This filename is appended to the directory path returned by
    `tempfile.gettempdir()` and has `extension` appended to it.
    """
    tempdir = tempfile.gettempdir()
    filename = str(uuid4())[:8] + extension
    return os.path.join(tempdir, filename)


def import_or_skip(name):
    """Try importing `name`, raise SkipTest on failure.

    Parameters
    ----------
    name : str
        Module name to try to import.

    Returns
    -------
    module : module object
        Module object imported by importlib.

    Raises
    ------
    unittest.SkipTest
        If the attempted import raises an ImportError.

    Examples
    --------
    >>> h5py = import_or_skip('h5py')
    >>> h5py.get_config()
    <h5py.h5.H5PYConfig at 0x103dd5a78>

    """
    try:
        return importlib.import_module(name)
    except ImportError:
        errmsg = '%s not found... skipping.' % name
        raise unittest.SkipTest(errmsg)


def comm_null_passes(fn):
    """Decorator. If `self.comm` is COMM_NULL, pass.

    This allows our tests to pass on processes that have nothing to do.
    """

    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'comm') and (self.comm == MPI.COMM_NULL):
            pass
        else:
            return fn(self, *args, **kwargs)

    return wrapper


class CommNullPasser(type):

    """Metaclass.

    Applies the `comm_null_passes` decorator to every method on a generated
    class.
    """

    def __new__(cls, name, bases, attrs):

        for attr_name, attr_value in six.iteritems(attrs):
            if isinstance(attr_value, types.FunctionType):
                attrs[attr_name] = comm_null_passes(attr_value)

        return super(CommNullPasser, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(CommNullPasser)
class MpiTestCase(unittest.TestCase):

    """Base test class for MPI test cases.

    Overload `get_comm_size` to change the default comm size (default is 4).
    """

    @classmethod
    def get_comm_size(cls):
        return 4

    @classmethod
    def setUpClass(cls):
        try:
            cls.comm = create_comm_of_size(cls.get_comm_size())
        except InvalidCommSizeError:
            msg = "Must run with comm size >= {}."
            raise unittest.SkipTest(msg.format(cls.get_comm_size()))

    @classmethod
    def tearDownClass(cls):
        if cls.comm != MPI.COMM_NULL:
            cls.comm.Free()


class IpclusterTestCase(unittest.TestCase):

    """Base test class for test cases needing an ipcluster.

    Overload `get_ipcluster_size` to change the default (default is 4).
    """

    @classmethod
    def get_ipcluster_size(cls):
        return 4

    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        if len(cls.client) < cls.get_ipcluster_size():
            errmsg = 'Tests need an ipcluster with at least {} engines running.'
            raise unittest.SkipTest(errmsg.format(cls.get_ipcluster_size()))

    def tearDown(self):
        self.client.clear(block=True)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
