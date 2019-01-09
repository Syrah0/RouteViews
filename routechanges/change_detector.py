import re
from ipaddress import ip_network


def _calculate_regexp(header_line):
	"""Returns a regular expression	that helps to get each column in a
	row.
	"""
	header = header_line[0:-1]  # Remove newline character
	header = header.replace("Next Hop", "Next_Hop")
	header = re.split(r' [a-zA-Z]', header)
	# First column only loses one character unlike the others that lose
	# the first and last character.
	header[0] = header[0][0:-1]

	regex = []  # List of regexp for each column
	for column in header:
		# Last column is the path, so it has undefined length.
		if column == header[-1]:
			regex.append("(.+)")
			break
		# Create regexp for a column based on the number of
		# characters it has.
		regex.append("(.{%s})" %str(len(column)+2))

	return ''.join(regex)  # Return complete regexp


def _get_row_values(row, regex):
	""" Returns a list that contains each column in a row. """
	row = row[0:-1] # Remove newline character
	values = re.findall(regex, row)
	values = [x.strip() for x in values[0]]
	# Remove last node (i , e or ?) that doesn't count when
	# comparing paths.
	values[6]= values[6][0:-1]
	return values


def aggregate_routes(file):
	"""Aggregate BGP routes in file and print them to stdin."""
	# Skip first 5 lines
	for _ in range(5):
		file.readline()
	header = file.readline()

	# Regex to parse row columns.
	regex = _calculate_regexp(header)

	net = 1  # Network index in a row array
	path = 6  # Path index
	file.readline()  # Skip default route in first row
	second_row = file.readline()
	if second_row == "\n": return
	second_row =_get_row_values(second_row, regex)
	second_row[net] = ip_network(second_row[net])
	# Rows to be displayed
	row_list = [second_row]

	for line in file:
		if line=="\n": break
		row = _get_row_values(line, regex)
		row[net] = ip_network(row[net])
		for r in row_list:
			if r[net].overlaps(row[net]) and r[path] == row[path]:
				break
			elif r[path] == row[path]:
				supernet = r[net].supernet()
				if supernet.overlaps(row[net]):
					r[net] = supernet
					break
			elif r == row_list[-1]:
				row_list.append(row)

	# Show aggregated routes.
	for row in row_list:
		print("{0:18} {1}".format(str(row[net]), row[path]))
