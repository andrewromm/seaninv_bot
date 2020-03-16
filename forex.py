import csv

instruments = []

with open('instruments.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=';')
	for row in reader:
		instruments.append(', '.join(row))


if __name__ == '__main__':
	print(instruments)