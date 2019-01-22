import unittest
import sys
import re
from tempfile import TemporaryFile
from routechanges.change_detector import (get_rows,
                                          aggregate_routes)
from ipaddress import IPv4Network


def compare_files(file1, file2, test_case):
    """Compares the lines of two files for a test_case object."""
    line_count = 0
    for line1, line2 in zip(file1, file2):
        line_count += 1
        test_case.assertEqual(
            line1, line2, "Line number {0} is not "
            "equal".format(line_count))


class TestGetRows(unittest.TestCase):

    def setUp(self):
        self.file = open("test/get_rows_test_file.txt")
        self.expected_output = [
            ["0.0.0.0", "27486 3549"],
            ["1.4.128.0/24", "27486 12926 13335"],
            ["41.230.169.0/24", ""],
            ["43.230.170.0/25", "27486 3543"],
            ["57.230.170.128/25", "27486 3641"],
            ["86.230.171.0/24", "27486 3949"],
            ["210.14.24.0", "27486 6862 7473 3758 55415"],
        ]

    def test_get_rows(self):
        """Test if every parsed row contains the correct information
        from the file.
        """
        for row, spected_row in zip(get_rows(self.file), self.expected_output):
            self.assertEqual(row, spected_row)

    def tearDown(self):
        self.file.close()


class TestAggregateRoutes(unittest.TestCase):

    def setUp(self):
        self.file = open("test/aggregate_routes_test_file.txt")
        # Will contain the output of aggregate_routes().
        self.output_file = TemporaryFile(mode="w+t")
        # Used only in test_aggregate_routes_output().
        self.expected_output_file = open(
            "test/aggregate_routes_expected_output.txt")

    def _execute_function(self):
        """Runs function aggregate_routes()."""
        # Run function over file.
        aggregate_routes(self.file, self.output_file)

        # Now the output of aggregate_routes() is in output_file.
        self.output_file.seek(0)

    def test_aggregate_routes_coverage(self):
        """Test if there is a path and covering prefix for each of the
        rows of the original BGP routing table file in the output of
        aggregate_routes() when run over that file.
        """
        self._execute_function()
        self.file.seek(0)  # Rewind file
        net = 0  # Network index in a row array
        path = 1  # Path index

        # Extract rows from generated output.
        path_dict = {}
        # path_dict will be a dict with paths as keys and lists of networks
        # as values.
        for output in self.output_file:
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
        for row in get_rows(self.file):
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

    def test_aggregate_routes_output(self):
        """Tests whether the output is equal to the contents of
        aggregate_routes_expected_output.txt.
        """
        self._execute_function()
        compare_files(self.output_file, self.expected_output_file, self)

    def tearDown(self):
        # Close BGP routes file, auxiliary and expected output file.
        self.file.close()
        self.output_file.close()
        self.expected_output_file.close()


class TestChangeDetection(unittest.TestCase):

    def setUp(self):
        self.file1 = open("test/change_detection_test_file_1.txt")
        self.file2 = open("test/change_detection_test_file_2.txt")
        self.output_file = TemporaryFile("w+t")
        self.expected_output = open(
            "test/change_detection_expected_output.txt")

    def test_change_detection(self):
        # TODO: Make detect_changes() function.
        detect_changes(file1, file2, output_file)
        output_file.seek(0)
        compare_files(self.output_file, self.expected_output_file, self)

    def tearDown(self):
        self.file1.close()
        self.file2.close()
        self.output_file.close()
        self.expected_output.close()
