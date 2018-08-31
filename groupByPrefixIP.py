from os import listdir
from os.path import isfile, join
import csv
import json
import argparse


def groupByPrefixIP(prefix_number):
	root = "/home/alexandra/Desktop/Visualization/rutas_bgp/csv"
	ips = []
	for file in listdir(root):
		file_csv = "GroupByPrefix/Prefix_" + str(prefix_number) + "/" + file.split(".")[0] + ".csv"
		file_csv_open = open(join(root,file_csv),"w")
		if isfile(join(root,file)):
			file_open = open(join(root,file),"r+")
			reader = csv.reader(file_open, delimiter = ',')
			for row in reader:
				ip = row[0]
				prefixs = ip.split('.')
				prefix_ip = ''
				for i in range(0, (prefix_number/8)):
					prefix_ip = prefix_ip + prefixs[i] + '.'
				for i in range((prefix_number/8), 3):
					prefix_ip = prefix_ip + '0.'
				prefix_ip = prefix_ip + '0/' + str(prefix_number)
				if prefix_ip not in ips:
					ips.append(prefix_ip)
				route = [prefix_ip]
				for index in range(1,len(row)):
					route.append(row[index])
				writer = csv.writer(file_csv_open, delimiter = ',')
				writer.writerow(route)
			break
	print('finish group')

parser = argparse.ArgumentParser(description="Run script with the prefix number")
parser.add_argument('-n', '--prefixNumber', type=int, help='prefix number to group IPs (8, 16, 24)')

if __name__ == '__main__':
	args = parser.parse_args()
	prefix_number = args.prefixNumber

	if(prefix_number == 8 or prefix_number == 16 or prefix_number == 24):
		groupByPrefixIP(prefix_number)
	else:
		"Ingrese un numero valido (8, 16 o 24)"

