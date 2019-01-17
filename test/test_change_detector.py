import unittest
import sys
import re
from tempfile import TemporaryFile
from routechanges.change_detector import (get_rows,
                                          aggregate_routes)
from ipaddress import IPv4Network


class TestChangeDetector(unittest.TestCase):

    def setUp(self):
        self.file = open("test/aggregate_routes_test_file.txt")
        self.aux_file = sys.stdout
        sys.stdout = TemporaryFile(mode="w+t")

    def test_aggregate_routes(self):
        """Test if rechability is the same for the original BGP routes
        file and the output of aggregate_routes() when run over that
        file.
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

        line_count = 0
        for row in get_rows(file):
            line_count += 1
            row[net] = IPv4Network(row[net])

            # Suppose there is no covering prefix for this network and
            # path.
            found = False

            # Look for covering prefix.
            for output in self.aux_file:
                output = output[0:-1]  # Remove newline character
                # Get network and path
                o_row = re.findall("(.{19})(.+)", output)
                o_row = [x.strip() for x in o_row[0]]
                o_row[0] = IPv4Network(o_row[0])

                # If there is a covering prefix set found = True.
                if (o_row[0].compare_networks(row[net]) < 1 and
                    o_row[0].overlaps(row[net]) and
                        o_row[1] == row[path]):
                    found = True
                    break

            self.assertTrue(found, "No path and covering prefix for network "
                            "{0}:\n {1}".format(line_count, row[net]))
            self.aux_file.seek(0)  # Rewind file for next iteration

    def tearDown(self):
        self.file.close()
        self.aux_file.close()
