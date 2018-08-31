# nodes -> Hacer diccionario de todos los AS disponibles y los IP.
# ver todos los links! (source - target)

# Leer todos los archivos y crear dos diccionarios

from os import listdir
from os.path import isfile, join
import csv
import json

root = "/home/alexandra/Desktop/Visualization/rutas_bgp/csv/"
ases = []

for file in listdir(root):
	if isfile(join(root,file)):
		print(file)
		file_open = open(join(root,file),"r+")
		reader = csv.reader(file_open, delimiter = ',')
		for row in reader:
			for index in range(1,len(row)):
				try:
					new_as_row = row[index].split('{')[1].split('}')[0].split(',')[0]
				except:
					new_as_row = row[index]
				if new_as_row not in ases:
					ases.append(new_as_row)

file_as = root + "/ASes"
file_open_as = open(join(file_as, "ASes.txt"), "w")
for nAS in ases:
	file_open_as.write('AS')
	file_open_as.write(nAS)
	file_open_as.write('\n')
file_open_as.close()

print("finish")