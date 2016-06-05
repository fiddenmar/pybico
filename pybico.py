import getopt
import sys
import re
from openpyxl import Workbook

PYBICO_VERBOSE = False

def pybico_import_txt(filename):
	rn = "(?P<names>((\w\. \w\. [\w]+,? )|([\w]+ \w\. \w\.,? ))+)" #regular for names
	ra = "(?P<article>[\w ]+)\/\/ " #regular for article
	rj = "(?P<journal>[\w ]+\.) - " #regular for journal
	rm = "(?P<misc>.+)" #regular for misc
	reg = re.compile(rn+ra+rj+rm)
	data = []
	f = open(filename, 'r')
	content = f.read()
	items = content.split('\n')
	for item in items:
		res = reg.match(item)
		if res != None:
			data.append((res.group("names").split(','), res.group("article"), res.group("journal"), res.group("misc")))
	return data

def pybico_import(mode, filename):
	data = []
	#test = ([name1, name2, ...], article_name, journal, misc)
	if mode == "txt":
		data = pybico_import_txt(filename)
	else:
		data = None
	return data

def pybico_export(mode, filename, data):
	if mode == "xlsx":
		pybico_export_xlsx(filename, data)
	else:
		return None
	
def usage():
	print("usage: pybico [options] input output")
	print("\toptions:")
	print("\t -h, --help\t print out help")
	print("\t -v\t verbose mode")
	print("\t -i\t input mode (txt)")
	print("\t -o\t output mode (xlsx)")

def main(argv):
	global PYBICO_VERBOSE

	try:
		opts, args = getopt.getopt(argv, "hx:v", ["help", "xlsx"])
	except getopt.GetoptError as err:
		print(str(err))
		usage()
		sys.exit(2)

	PYBICO_VERBOSE = False
	input_mode = "txt"
	output_mode = "xlsx"
	input_filename = args[0]
	output_filename = args[1]

	for o, a in opts:
		if o == "-v":
			PYBICO_VERBOSE = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o == "-i":
			input_mode = a
		elif o == "-o":
			output_mode = a
		else:
			assert False, "unhandled option"
	data = pybico_import(input_mode, input_filename)
	print(data)
	#pybico_export(output_mode, output_filename, res)

if __name__ == '__main__':
	main(sys.argv[1:])