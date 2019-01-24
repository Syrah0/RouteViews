import sys
import re
from ipaddress import IPv4Network


def _calculate_regexp(header_line):
    """Returns a regular expression and a list of integers. The regular
    expression will help to parse the columns for each row of the table,
    and the list will contain the widths of the columns except for the
    last one which is the path column that has undefined length.
    """
    header = header_line[0:-1]  # Remove newline character
    header = header.replace("Next Hop", "Next_Hop")
    header = re.split(r' [a-zA-Z]', header)
    # First column only loses one character unlike the others that lose
    # the first and last character.
    header[0] = header[0][0:-1]
    column_lengths = []
    regex = []  # List of regexp for each column
    for column in header:
        # Last column is the path, so it has undefined length.
        if column == header[-1]:
            regex.append("(.+)")
            break
        # Create regexp for a column based on the number of
        # characters it has.
        c_lenght = len(column)+2
        column_lengths.append(c_lenght)
        regex.append("(.{%s})" % str(c_lenght))

    # Return complete regexp and list of widths
    return ''.join(regex), column_lengths


def get_rows(file):
    """ Returns an iterator over the rows of the file containing only
    the information about network and path. The element returned for
    each itaration is a list with the first element as the string for
    the network and the second element the path of AS's.
    """
    # Skip first 5 lines of the file header.
    for _ in range(5):
        file.readline()

    # Calculate regex to parse rows.
    header = file.readline()
    regex, column_lengths = _calculate_regexp(header)
    first_three = sum(column_lengths[0:3])
    all_col = sum(column_lengths)  # Row length till path column

    for line in file:
        if line == "\n":
            break  # There are no more rows
        line = line[0:-1]  # Remove newline character
        if len(line) < first_three:  # The line is not complete
            # Remove first column and newline character to only get
            # the network.
            net = line[column_lengths[0]:len(line)]
            next_line = file.readline()
            # Remove every row before the path and remove newline
            # character.
            path = next_line[all_col:-1]
            row = [net, path]
        else:
            row = re.findall(regex, line)
            row = row[0]
            row = [row[1].strip(), row[6]]

        if row[1][-1] == "?" or row[1][-1] == "i":
            # Remove last node that does not help when comparing paths.
            row[1] = row[1][0:-1]
        row[1] = row[1].strip()  # Remove aditional spaces
        yield row


def aggregate_routes(file, return_list=False, output_file=None):
    """Aggregate BGP routes in file.
    The output of the function is ordered by network from lowest to
    highest ip and mask.
    If return_list is set to True the function will return a list of
    2-tuples where for each tuple the first element will be an
    IPv4Network object and the second element will be the string of the
    path for that network.
    If return_list is False the output will be printed to output_file
    where each row of the output is formatted with the first column
    having a width of 18 characters and containing the network left
    aligned, then comes a space and the second column that contains the
    path for that network. The second column has variable width
    depending on the path and ends with a newline character. If
    output_file is None sys.stdout will be used.
    This function does not modify the given file. 
    """
    if output_file == None:
        output_file = sys.stdout

    net = 0  # Network index in a row array
    path = 1  # Path index
    row_list = {}  # Rows to be displayed

    row_iterator = get_rows(file)
    default_present = False
    first_row = next(row_iterator)
    if first_row[net] == "0.0.0.0":
        # Skip default route in first row.
        # Add mask to be coherent with ipaddress library.
        first_row[net] = "0.0.0.0/32"
        default_present = True
        second_row = next(row_iterator)
        second_row[net] = IPv4Network(second_row[net], False)
        row_list[second_row[path]] = {second_row[net]}
    else:
        row_list[first_row[path]] = {IPv4Network(first_row[net], False)}

    # For each row of the table find if it can be aggregated and
    # aggregate it, otherwise add the network to the corresponding
    # set for its path in row_list.
    for row in row_iterator:
        row[net] = IPv4Network(row[net], False)
        current_path = row[path]
        current_net = row[net]
        if current_path in row_list:
            while True:
                supernet = current_net.supernet()
                if supernet != current_net:
                    if supernet in row_list[current_path]:
                        # There is no need to add this net.
                        break

                    # Get sibling net.
                    n1, n2 = supernet.subnets()
                    if n1 == current_net:
                        sibling_net = n2
                    else:
                        sibling_net = n1

                    if sibling_net in row_list[current_path]:
                        row_list[current_path].discard(sibling_net)
                        # Continue trying to aggregate the supernet.
                        current_net = supernet
                        continue

                # The net couldn't be aggregated.
                row_list[current_path].add(current_net)
                break
        else:
            row_list[current_path] = {current_net}

    final_list = []

    if default_present:
        if return_list:
            final_list = [(IPv4Network(first_row[net]), first_row[path])]
        else:
            # Print default route.
            print("{0:18} {1}".format(first_row[net], first_row[path]),
                  file=output_file)

    # Prepare to output rows ordered by network.
    for path, net_set in row_list.items():
        for network in net_set:
            final_list.append((network, path))

    final_list.sort(key=lambda pair: pair[0])

    if return_list:
        return final_list

    # Show aggregated routes.
    for network, path in final_list:
        print("{0:18} {1}".format(str(network), path), file=output_file)


def detect_changes(file_t1, file_t2, output_file=None):
    """Find changes in routes of file_t2 repect to file_t1 and print
    them to output_file, if output_file is None then sys.stdout will
    be used.
    """
    if output_file is None:
        output_file = sys.stdout

    routes_t1 = aggregate_routes(file_t1, return_list=True)
    routes_t2 = aggregate_routes(file_t2, return_list=True)

    covered_t1 = [False for route in routes_t1]

    # Net and path index for a tuple.
    net = 0
    path = 1

    for i, row_t2 in enumerate(routes_t2):
        # Find the more specific prefix in routes_t1 that contains
        # row_t2[net].
        specific_t1 = None
        specific_index = None
        for j, row_t1 in enumerate(routes_t1):
            if (row_t1[net].overlaps(row_t2[net]) and
                    row_t1[net].prefixlen <= row_t2[net].prefixlen):
                if (specific_t1 == None or
                        row_t1[net].prefixlen > specific_t1[net])
                    specific_t1 = row_t1
                    specific_index = j
                    continue

        if specific_t1 == None:
            # row_t2[net] is new.
            print(str(row_t2[net]), file=output_file)
            print("DEF", file=output_file)
            print(row_t2[path], file=output_file)
            continue

        if (specific_t1[net] == row_t2[net] and
                specific_t1[path] != row_t2[path]):
            # The net changed its path
            covered_t1[specific_index] = True
            print(str(row_t2[net]), file=output_file)
            print(specific_t1[path], file=output_file)
            print(row_t2[path], file=output_file)
            continue
