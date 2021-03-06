# encoding: utf-8
__docformat__ = "restructuredtext en"
# Copyright (c) 2008-2014, IPython Development Team and Enthought, Inc.

import unittest
import numpy
from numpy.testing import assert_array_equal

import distarray.local.denselocalarray as dla
from distarray.error import InvalidCommSizeError, InvalidRankError
from distarray.mpiutils import MPI, create_comm_of_size, create_comm_with_list


class TestCreateCommAlternate(unittest.TestCase):
    """ Test alternate code paths for creating the MPI comm.

    In particular, test creating the comm from a list,
    and the failure modes for creating the comm.

    These code paths are not covered normally by MpiTestCase,
    so this test case does not derive from that usual base class.
    """

    def setUp(self):
        # Get the maximum number of nodes available.
        COMM_PRIVATE = MPI.COMM_WORLD.Clone()
        self.max_size = COMM_PRIVATE.Get_size()

    def test_create_comm_with_list(self):
        """ Test that create_comm_with_list() works correctly. """
        nodes = [0, 1, 2, 3]
        comm = create_comm_with_list(nodes)
        if comm == MPI.COMM_NULL:
            # Only proceed when not COMM_NULL.
            return
        # Run a simple test to confirm this comm works.
        size = len(nodes)
        nrows = size * 3
        a = dla.zeros((nrows, 20), comm=comm)
        expected = numpy.zeros((nrows // size, 20))
        assert_array_equal(a.local_array, expected)
        # Cleanup.
        comm.Free()

    def test_size_too_big(self):
        """ Test that a comm of size with too many nodes will fail. """
        too_many = 2 * self.max_size
        with self.assertRaises(InvalidCommSizeError):
            create_comm_of_size(too_many)

    def test_list_too_big(self):
        """ Test that a comm from list with too many nodes will fail. """
        too_many = 2 * self.max_size
        nodes = range(too_many)
        with self.assertRaises(InvalidCommSizeError):
            create_comm_with_list(nodes)

    def test_invalid_ranks(self):
        """ Test that a comm from list with invalid ranks will fail. """
        max_size = self.max_size
        # Nodes should be 0..max_size - 1, so create invalid values.
        nodes = range(10, max_size + 10)
        with self.assertRaises(InvalidRankError):
            create_comm_with_list(nodes)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
