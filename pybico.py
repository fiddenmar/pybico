import getopt
import sys
import string

from loader import Loader
from saver import Saver
from dbwrapper import DBWrapper as DB

PYBICO_VERBOSE = False

def usage():
	print("usage: pybico [options]")
	print("\toptions:")
	print("\t -h, --help\t print out help")
	print("\t -v\t verbose mode")
	print("\t -l\t import file path to load")
	print("\t -s\t export file path to save")
	print("\t -i\t import format (txt, id)")
	print("\t -e\t export format (xlsx)")
	print("\t -u\t database user")
	print("\t -p\t path to database password")

def main(argv):
	global PYBICO_VERBOSE

	try:
		opts, args = getopt.getopt(argv, "hvl:s:i:e:u:p:", ["help"])
	except getopt.GetoptError as err:
		print(str(err))
		usage()
		sys.exit(2)

	PYBICO_VERBOSE = False
	import_format = "txt"
	export_format = "xlsx"
	import_filename = ""
	export_filename = ""
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
		elif o == "-l":
			import_filename = a
		elif o == "-s":
			export_filename = a
		elif o == "-i":
			import_format = a
		elif o == "-e":
			export_format = a
		else:
			assert False, "unhandled option"

	# f = open(password_path, 'r')
	# password = f.read()

	password = "12345"
	db = DB(user, password)
	if import_filename != "":
		l = Loader(import_format, import_filename)
		data = l.load()
		db.add(data)
	if export_filename != "":
		data = db.get()
		s = Saver(data, export_format, export_filename)
		s.save()

if __name__ == '__main__':
	main(sys.argv[1:])
