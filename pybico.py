import getopt
import sys
import string
import importlib.util

from dbwrapper import DBWrapper as DB

PYBICO_VERBOSE = False

def usage():
	print("usage: pybico [options]")
	print("\toptions:")
	print("\t -h, --help\t print out help")
	print("\t -v\t verbose mode")
	print("\t -i\t input file path")
	print("\t -o\t output file path")
	print("\t -l\t loader module file path")
	print("\t -r\t loader custom regex file path")
	print("\t -s\t saver module file path")
	print("\t -u\t database user")
	print("\t -p\t path to database password")

def main(argv):
	global PYBICO_VERBOSE

	try:
		opts, args = getopt.getopt(argv, "hvl:s:i:o:u:p:r:", ["help"])
	except getopt.GetoptError as err:
		print(str(err))
		usage()
		sys.exit(2)

	PYBICO_VERBOSE = False
	loader_module_filepath = "./loaders/loader_gost_txt.py"
	loader_custom_regex_file = ""
	saver_module_filepath = "./savers/saver_xlsx.py"
	input_filepath = ""
	output_filepath = ""
	password_path = ""
	user = ""

	for o, a in opts:
		if o == "-v":
			PYBICO_VERBOSE = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o == "-u":
			user = a
		elif o == "-p":
			password_path = a
		elif o == "-i":
			input_filepath = a
		elif o == "-o":
			output_filepath = a
		elif o == "-l":
			load_format = a
		elif o == "-s":
			save_format = a
		else:
			assert False, "unhandled option"

	f = open(password_path, 'r')
	password = f.read().strip('\n')

	db = DB(user, password)

	if input_filepath != "":
		loader_spec = importlib.util.spec_from_file_location("loader", loader_module_filepath)
		loader = importlib.util.module_from_spec(loader_spec)
		loader_spec.loader.exec_module(loader)
		l = loader.Loader()
		data = []
		if loader_custom_regex_file == "":
			data = l.load(input_filepath)
		else:
			data = l.load(input_filepath, loader_custom_regex_file)
		db.add(data)
	if output_filepath != "":
		data = db.get()
		saver_spec = importlib.util.spec_from_file_location("saver", saver_module_filepath)
		saver = importlib.util.module_from_spec(saver_spec)
		saver_spec.loader.exec_module(saver)
		s = saver.Saver()
		s.save(data, output_filepath)

if __name__ == '__main__':
	main(sys.argv[1:])
