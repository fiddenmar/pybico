import getopt
import sys
import re
import string
from openpyxl import Workbook
from openpyxl.styles import Alignment
import pymysql.cursors

PYBICO_VERBOSE = False

def pybico_import_txt(filename):
	rn = "(?P<authors>((\w\. ?(\w\. )?[\w]+,? )|([\w]+ [\w]\. ?([\w]\.)?,? ))+)" #regular for authors
	ra = "(?P<article>.+?) *\/\/ *" #regular for article
	rj = '(?P<source>[ \w"“”]+)' #regular for source
	rm = "(?P<misc>.+)" #regular for misc
	reg = re.compile(rn+ra+rj+rm)
	data = []
	f = open(filename, 'r')
	content = f.read()
	items = content.split('\n')
	for item in items:
		res = reg.match(item.strip())
		if res != None:
			data.append({"authors": res.group("authors").split(', '), "article": res.group("article"), "source": res.group("source"), "misc": res.group("misc")})
		else:
			print("Wrong line: " + item)
	return data

def pybico_import(mode, filename, usr, pswd):
	data = []
	#test = ([author1, author2, ...], article, source, misc)
	if mode == "txt":
		data = pybico_import_txt(filename)
	else:
		data = None

	connection = pymysql.connect(host="127.0.0.1",
								user=usr,
								password=pswd,
								db='pybico',
								charset='utf8',
								cursorclass=pymysql.cursors.DictCursor)
	try:
		for item in data:
			author_id = []
			source_id = 0
			publication_id = 0
			with connection.cursor() as cursor:
				cursor.execute('SET NAMES utf8;')
				cursor.execute('SET CHARACTER SET utf8;')
				cursor.execute('SET character_set_connection=utf8;')
				get_source_sql = "SELECT `id` FROM `source` WHERE `name`=%s"
				cursor.execute(get_source_sql, (item["source"]))
				result = cursor.fetchone()
				if result:
					source_id = result["id"]
				else:
					insert_source_sql = "INSERT INTO `source` (`name`) VALUES (%s)"
					cursor.execute(insert_source_sql, (item["source"]))
					connection.commit()
					cursor.execute(get_source_sql, (item["source"]))
					res = cursor.fetchone()
					source_id = res["id"]
			for a in item["authors"]:
				author = a.strip()
				if author != "":
					with connection.cursor() as cursor:
						get_author_sql = "SELECT `id` FROM `author` WHERE `name`=%s"
						cursor.execute(get_author_sql, (author))
						result = cursor.fetchone()
						if result:
							author_id.append(result["id"])
						else:
							insert_author_sql = "INSERT INTO `author` (`name`) VALUES (%s)"
							cursor.execute(insert_author_sql, (author))
							connection.commit()
							cursor.execute(get_author_sql, (author))
							res = cursor.fetchone()
							author_id.append(res["id"])
			with connection.cursor() as cursor:
				get_publication_sql = "SELECT `id` FROM `publication` WHERE `title`=%s"
				cursor.execute(get_publication_sql, (item["article"]))
				result = cursor.fetchone()
				if result:
					publication_id = result["id"]
				else:
					insert_publication_sql = "INSERT INTO `publication` (`title`, `source_id`, `misc`) VALUES (%s, %s, %s)"
					cursor.execute(insert_publication_sql, (item["article"], str(source_id), item["misc"]))
					connection.commit()
					cursor.execute(get_publication_sql, (item["article"]))
					res = cursor.fetchone()
					publication_id = res["id"]
					for author in author_id:
						insert_relation_sql = "INSERT INTO `relation` (`publication_id`, `author_id`) VALUES (%s, %s)"
						cursor.execute(insert_relation_sql, (str(publication_id), str(author)))
					connection.commit()
	finally:
		connection.close()
	# return data

def pos_to_char(i):
	return string.ascii_uppercase[i] 

def pybico_extract(usr, pswd):
	data = []
	connection = pymysql.connect(host="127.0.0.1",
								user=usr,
								password=pswd,
								db='pybico',
								charset='utf8',
								cursorclass=pymysql.cursors.DictCursor)
	try:
		with connection.cursor() as cursor:
			get_publication_sql = "SELECT * FROM `publication` WHERE `registered`=%s"
			cursor.execute(get_publication_sql, (str(0)))
			result = cursor.fetchall()
			for pub in result:
				target_id = pub["id"]
				authors = []
				source = ""
				get_author_sql = "SELECT `author_id` FROM `relation` WHERE `publication_id`=%s"
				cursor.execute(get_author_sql, (str(target_id)))
				res = cursor.fetchall()
				for a in res:
					get_name_sql = "SELECT `name` FROM `author` WHERE `id`=%s"
					cursor.execute(get_name_sql, (str(a["author_id"])))
					name = cursor.fetchone()
					authors.append(name["name"])
				get_source_sql = "SELECT `name` FROM `source` WHERE `id`=%s"
				cursor.execute(get_source_sql, (str(pub["source_id"])))
				src_res = cursor.fetchone()
				source = src_res["name"]
				data.append({"authors": authors, "article": pub["title"], "source": source, "misc": pub["misc"]})
	finally:
		connection.close()
	return data

def pybico_export_xlsx(filename, data):
	offset = 3
	wb = Workbook()
	ws = wb.active
	wstyle1 = Alignment(horizontal='left', vertical='top', text_rotation=0, wrap_text=True, shrink_to_fit=False, indent=0)
	wstyle2 = Alignment(horizontal='center', vertical='center', text_rotation=0, wrap_text=True, shrink_to_fit=False, indent=0)
	for r in range(0, offset+len(data)+1):
		ws.row_dimensions[r+1].height = 100
	ws.row_dimensions[3].height = 15
	for c in range(1,9):
		ch = pos_to_char(c-1)
		ws.column_dimensions[ch].width = 20
	for r in range(1,offset+1):
		for c in range(1,9):
			ws.cell(row = r, column = c).alignment = wstyle2
	for r in range(offset+1, offset+len(data)+1):
		for c in (2,3,4,6):
			ws.cell(row = r, column = c).alignment = wstyle1
		for c in (1,5,7,8):
			ws.cell(row = r, column = c).alignment = wstyle2
	ws.merge_cells('G1:H1')
	ws['A1'] = "№ раздела"
	ws['B1'] = "Автор (ФИО сотрудника МИЭТ, студента, аспиранта)"
	ws['C1'] = "Название статьи, книги, монографии, уч. пособия и др."
	ws['D1'] = "Наименование журнала или конференции"
	ws['E1'] = "Статус\nWeb of Science\nScopus\nРИНЦ\nВАК"
	ws['F1'] = "Город, издательство, год, номер, том, страницы"
	ws['G1'] = "Количество авторов"
	ws['G2'] = "Всего"
	ws['H2'] = "В т.ч. сотрудников МИЭТ"
	for c in range(1,9):
		ws.cell(row = 3, column = c).value = c
	for i, item in enumerate(data):
		pos = str(i+1+offset)
		ws['A'+pos] = "todo"
		ws['B'+pos] = "\n".join(item["authors"])
		ws['C'+pos] = item["article"]
		ws['D'+pos] = item["source"]
		ws['E'+pos] = "todo"
		ws['F'+pos] = item["misc"]
		ws['G'+pos] = str(len(item["authors"]))
		ws['H'+pos] = "todo"

	wb.save(filename) 

def pybico_export(mode, filename, data):
	if mode == "xlsx":
		pybico_export_xlsx(filename, data)
	else:
		return None
	
def usage():
	print("usage: pybico [options] input output user password_path")
	print("\toptions:")
	print("\t -h, --help\t print out help")
	print("\t -v\t verbose mode")
	print("\t -i\t input mode (txt)")
	print("\t -o\t output mode (xlsx)")

def main(argv):
	global PYBICO_VERBOSE

	try:
		opts, args = getopt.getopt(argv, "hx:vu:p:", ["help", "xlsx"])
	except getopt.GetoptError as err:
		print(str(err))
		usage()
		sys.exit(2)

	PYBICO_VERBOSE = False
	input_mode = "txt"
	output_mode = "xlsx"
	input_filename = args[0]
	output_filename = args[1]
	password_path = args[3]
	f = open(password_path, 'r')
	password = f.read()
	user = args[2]

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
		elif o == "-c":
			password_path = a
		elif o == "-u":
			user = a
		else:
			assert False, "unhandled option"
	pybico_import(input_mode, input_filename, user, password)
	data = pybico_extract(user, password)
	pybico_export(output_mode, output_filename, data)

if __name__ == '__main__':
	main(sys.argv[1:])