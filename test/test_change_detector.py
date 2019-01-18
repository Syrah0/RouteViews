import unittest
import sys
import re
from tempfile import TemporaryFile
from routechanges.change_detector import (get_rows,
                                          aggregate_routes)
from ipaddress import IPv4Network


class TestGetRows(unittest.TestCase):

    def setUp(self):
        self.file = open("test/get_rows_test_file.txt")
        self.spected_output = [
            ["0.0.0.0", "27486 3549"],
            ["1.4.128.0/24", "27486 12926 13335"],
            ["41.230.169.0/24", "27486 3547"],
            ["43.230.170.0/25", "27486 3543"],
            ["57.230.170.128/25", "27486 3641"],
            ["86.230.171.0/24", "27486 3949"],
            ["210.14.24.0", "27486 6862 7473 3758 55415"],
        ]

    def test_get_rows(self):
        """Test if every parsed row contains the correct information
        from the file.
        """
        for row, spected_row in zip(get_rows(self.file), self.spected_output):
            self.assertEqual(row, spected_row)

    def tearDown(self):
        self.file.close()


class TestAggregateRoutes(unittest.TestCase):

    def setUp(self):
        self.file = open("test/aggregate_routes_test_file.txt")
        # These two files will be later interchanged so aux_file
        # contains the output of aggregate_routes().
        self.aux_file = sys.stdout
        sys.stdout = TemporaryFile(mode="w+t")

    def test_aggregate_routes(self):
        """Test if there is a path and covering prefix for each of the
        rows of the original BGP routing table file in the output of
        aggregate_routes() when run over that file.
        """
        # Run function over file.
        file = self.file
        aggregate_routes(file)

        # Disconnect aux_file from stdout.
        sys.stdout, self.aux_file = self.aux_file, sys.stdout

        # Now the output of aggregate_routes() is in aux_file.
        self.aux_file.seek(0)
        file.seek(0)  # Rewind file
        net = 0  # Network index in a row array
        path = 1  # Path index

        # Extract rows from generated output.
        path_dict = {}
        # path_dict will be a dict with paths as keys and lists of networks
        # as values.
        for output in self.aux_file:
            output = output[0:-1]  # Remove newline character
            # Get network and path
            o_row = re.findall("(.{19})(.+)", output)
            o_row = [x.strip() for x in o_row[0]]
            current_net = IPv4Network(o_row[net])
            current_path = o_row[path]
            if current_path in path_dict:
                path_dict[current_path].append(current_net)
            else:
                path_dict[current_path] = [current_net]

        # Test if there is a path and covering prefix in the output for
        # each row in the original file
        row_count = 0
        for row in get_rows(file):
            row_count += 1
            row[net] = IPv4Network(row[net])

            # Suppose there is no covering prefix for this network and
            # path.
            found = False

            # Look for covering prefix.
            if row[path] in path_dict:
                for network in path_dict[row[path]]:
                    # If there is a covering prefix set found = True.
                    if (network.compare_networks(row[net]) < 1 and
                            network.overlaps(row[net])):
                        found = True
                        break
            self.assertTrue(found, "No path and covering prefix for network "
                            "in row {0}:\n {1}".format(row_count, row[net]))

    def tearDown(self):
        # Close BGP routes file and the output file.
        self.file.close()
        self.aux_file.close()
