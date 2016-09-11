import getopt
import sys
import string
import xlsxwriter
import pymysql.cursors
import requests

import regex as re

PYBICO_VERBOSE = False

def split_authors(res):
	authors = res.split(', ')
	new_authors = []
	for author in authors:
		new_authors.append(author.strip().replace(". ", "."))
	return new_authors

def isEnglish(s):
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True

def pybico_import_txt(filename):
	rn1 = r"(?P<authors>((\pL\. ?(\pL\. )?\pL+,? )|(\pL+ \pL\. ?(\pL\.)?,? )" #regular for authors
	rn2 = r"|(\p{Lu}\p{Ll}+ \p{Lu}\p{Ll}+,? )"
	rn3 = r")+)"
	ra_ru = r"(?P<article>\p{Lu}\p{Ll}+ \p{Ll}+.*?) *\/\/ *" #regular for article
	ra_eng = r"(?P<article>\p{Lu}.*?) *\/\/ *" #regular for article
	rj = r'(?P<source>[ \pL"“”]+)' #regular for source
	rm = r"(?P<misc>.+)" #regular for misc
	reg_ru = re.compile(rn1+rn2+rn3+ra_ru+rj+rm, re.UNICODE)
	reg_eng = re.compile(rn1+rn3+ra_eng+rj+rm, re.UNICODE)
	data = []
	f = open(filename, 'r')
	content = f.read()
	items = content.split('\n')
	for item in items:
		res = None
		if isEnglish(item[:15]):
			res = reg_eng.match(item.strip())
		else:
			res = reg_ru.match(item.strip())
		if res != None:
			authors = res.group("authors").split(', ')
			data.append({"authors": split_authors(res.group("authors")), "article": res.group("article"), "source": res.group("source"), "misc": res.group("misc")})
		else:
			print("Wrong line: " + item)	
	return data

def clean(string, p):
	result = p.sub('', string)
	return result

def get_result(found, factor):
	if found != "да":
		return 0
	if factor == '':
		return -1
	return factor

def pybico_import_id(filename):
	data = []
	f = open(filename, 'r')
	content = f.read()
	author_ids = content.split('\n')
	print(author_ids)
	article_reg_string = r'id="arw(?P<id>\d*).+?".*?a href=.*?<b>(?P<article>.*?)<\/b>.*?<i>(?P<authors>.*?)<\/i>.*?<font color=.+?>((.*?В сборнике: )?<a .+?>(?P<source>.+?)<\/a>)?(?P<misc>.+?)<\/td'
	article_reg = re.compile(article_reg_string, re.UNICODE)
	rsci_reg_string = r'Входит в РИНЦ.*?<font color=#00008f>(?P<rsci>.*?)<\/font>.*?(Импакт-фактор журнала в РИНЦ.*?<font color=#00008f>(?P<rsci_factor>\d+)<\/font>)?'
	scopus_reg_string = r'.*?Входит в Scopus.*?<font color=#00008f>(?P<scopus>.*?)<\/font>.*?(Импакт-фактор журнала в Scopus.*?<font color=#00008f>(?P<scopus_factor>\d+)<\/font>)?'
	wos_reg_string = r'.*?Входит в Web of Science.*?<font color=#00008f>(?P<wos>.*?)<\/font>.*?(Импакт-фактор журнала в Web of Science.*?<font color=#00008f>(?P<wos_factor>\d+)<\/font>)?'
	#hac_reg_string = r'(Входит в ВАК.*?<font color=#00008f>(?P<hac>(да)|(нет))</font>)?.*(Импакт-фактор журнала в ВАК.*?<font color=#00008f>(?P<hac_factor>\d+)</font>)?'
	status_reg_string = rsci_reg_string+scopus_reg_string+wos_reg_string
	status_reg = re.compile(status_reg_string, re.UNICODE)
	p = re.compile(r'(<.*?>)|(&nbsp;)|(^[., ])')
	for author_id in author_ids:
		request_status_code = 0
		while request_status_code != 200 :
			r = requests.get('http://elibrary.ru/author_items.asp?authorid='+author_id)
			request_status_code = r.status_code
		html = r.text
		number_of_pages = 1
		while 'javascript:goto_page('+str(number_of_pages)+')' in html:
			number_of_pages+=1
		if number_of_pages != 1:
			number_of_pages-=1
		for page_number in range(number_of_pages):
			request_status_code = 0
			while request_status_code != 200 :
				page_request = requests.post('http://elibrary.ru/author_items.asp', data = {'authorid': author_id, 'pagenum': ''+str(page_number+1)})
				request_status_code = page_request.status_code
			page = page_request.text.replace('\n', '').replace('\r', '')
			matches = article_reg.findall(page)
			for article_res in matches:
				request_status_code = 0
				while request_status_code != 200 :
					article_request = requests.get('http://elibrary.ru/item.asp?id='+article_res[0])
					request_status_code = article_request.status_code
				article_page = article_request.text.replace('\n', '').replace('\r', '')
				status_res = status_reg.findall(article_page)
				#status_res_hac = status_reg_hac.match(article_page)
				data.append(({"authors": split_authors(clean(article_res[2], p)), "article": clean(article_res[1], p),
					"source": clean(article_res[3], p), "misc": clean(article_res[6], p),
					"scopus": get_result(status_res[0][3], status_res[0][5]),
					"wos": get_result(status_res[0][6], status_res[0][8]), 
					#"hac": get_result(status_res_hac["hac"] if status_res_hac["hac"] else '', status_res_hac["hac_factor"] if status_res_hac["hac_factor"] else 0),
					"rsci": get_result(status_res[0][0], status_res[0][2])
					}))
	return data


def pybico_import(format, filename, usr, pswd):
	data = []
	#test = ([author1, author2, ...], article, source, misc)
	if format == "txt":
		data = pybico_import_txt(filename)
	elif format == "id":
		data = pybico_import_id(filename)
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
						get_relation_sql = "SELECT * FROM `relation` WHERE `publication_id`=%s AND `author_id`=%s"
						cursor.execute(get_relation_sql, (str(publication_id), str(author)))
						result = cursor.fetchone()
						if not result:
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
				get_authors_sql = "SELECT `author_id` FROM `relation` WHERE `publication_id`=%s"
				cursor.execute(get_authors_sql, (str(target_id)))
				res = cursor.fetchall()
				for a in res:
					get_name_sql = "SELECT `name`, `position`, `miet` FROM `author` WHERE `id`=%s"
					cursor.execute(get_name_sql, (str(a["author_id"])))
					author = cursor.fetchone()
					authors.append({"name": author["name"], "position": author["position"], "miet": author["miet"]})
				get_source_sql = "SELECT `name`, `type`, `scopus`, `wos`, `hac`, `rsci` FROM `source` WHERE `id`=%s"
				cursor.execute(get_source_sql, (str(pub["source_id"])))
				src_res = cursor.fetchone()
				source = {"name": src_res["name"], "type": src_res["type"], "scopus": src_res["scopus"], "wos": src_res["wos"], "hac": src_res["hac"], "rsci": src_res["rsci"]}
				data.append({"authors": authors, "article": pub["title"], "source": source, "misc": pub["misc"]})
	finally:
		connection.close()
	return data

def get_author_names(authors, styles, cell_format):
	names = []
	for i, author in enumerate(authors):
		if (not not author["miet"]):
			if (author["position"] == "аспирант"):
				names.append(styles["aspir"])
			elif (author["position"] == "студент"):
				names.append(styles["student"])
			else:
				names.append(styles["miet"])
		if i == len(authors)-1:
			names.append(author["name"])
		else:
			names.append(author["name"]+"\n")
	names.append(cell_format)
	return tuple(names)

def get_author_miet(authors):
	miet = 0
	for author in authors:
		miet += not not author["miet"]
	return miet

def get_impact_factor(source):
	impact_list = [source["scopus"], source["wos"], source["hac"], source["rsci"]]
	impact = max(impact_list)
	if impact == 0:
		impact = -1
	if impact == -1:
		return ""
	return impact

def get_status(source):
	status = []
	impact_list = [source["scopus"], source["wos"], source["hac"], source["rsci"]]
	status_list = ["Scopus", "Web of Science", "ВАК", "РИНЦ"]
	for i, impact in enumerate(impact_list):
		if impact != 0:
			output = status_list[i]
			if impact != -1:
				output = output+"="+impact
			status.append(output)
	return status

def pybico_export_xlsx(filename, data):
	offset = 3
	wb = xlsxwriter.Workbook(filename)
	ws = wb.add_worksheet()
	center = wb.add_format()
	center.set_text_wrap()
	center.set_align("center")
	center.set_align("vcenter")
	left = wb.add_format()
	left.set_text_wrap()
	left.set_align("left")
	left.set_align("top")

	miet = wb.add_format()
	miet.set_underline()
	aspir = wb.add_format()
	aspir.set_underline()
	aspir.set_bold()
	student = wb.add_format()
	student.set_underline()
	student.set_italic()
	styles = {"miet": miet, "aspir": aspir, "student": student}
	
	ws.write(0, 0, "№ раздела", center)
	ws.write(0, 1, "Автор (ФИО сотрудника МИЭТ, студента, аспиранта, center)", center)
	ws.write(0, 2, "Название статьи, книги, монографии, уч. пособия и др.", center)
	ws.write(0, 3, "Наименование журнала или конференции", center)
	ws.write(0, 4, "Город, издательство, год, номер, том, страницы", center)
	ws.write(0, 5, "Статус\nWeb of Science\nScopus\nРИНЦ\nВАК", center)
	ws.write(0, 6, "Импакт-фактор", center)
	ws.merge_range('H1:I1', "Количество авторов", center)
	ws.write(1, 7, "Всего", center)
	ws.write(1, 8, "В т.ч. сотрудников МИЭТ", center)

	ws.set_row(0, 80)
	ws.set_row(1, 40)
	ws.set_column(0, 0, 10)
	ws.set_column(1, 1, 20)
	ws.set_column(2, 2, 40)
	ws.set_column(3, 3, 25)
	ws.set_column(4, 4, 25)
	ws.set_column(5, 5, 10)
	ws.set_column(6, 6, 10)
	ws.set_column(7, 7, 10)
	ws.set_column(8, 8, 15)

	for i in range(1, 10):
		ws.write(2, i-1, str(i), center)

	for i, item in enumerate(data):
		pos = i+offset
		ws.write(pos, 0, str(item["source"]["type"]), center)
		ws.write_rich_string(pos, 1, *get_author_names(item["authors"], styles, left))
		ws.write(pos, 2, item["article"], left)
		ws.write(pos, 3, item["source"]["name"], left)
		ws.write(pos, 4, item["misc"], left)
		ws.write(pos, 5, str("\n".join(get_status(item["source"]))), center)
		ws.write(pos, 6, str(get_impact_factor(item["source"])), center)
		ws.write(pos, 7, str(len(item["authors"])), center)
		ws.write(pos, 8, str(get_author_miet(item["authors"])), center)
		height = 4
		if len(item["authors"]) > height:
			height = len(item["authors"])
		ws.set_row(pos, 20*height)

	wb.close()

def pybico_export(format, filename, data):
	if format == "xlsx":
		pybico_export_xlsx(filename, data)
	else:
		return None
	
def usage():
	print("usage: pybico [options]")
	print("\toptions:")
	print("\t -h, --help\t print out help")
	print("\t -v\t verbose mode")
	print("\t -o\t import file path to open")
	print("\t -s\t export file path to save")
	print("\t -i\t import format (txt, id)")
	print("\t -e\t export format (xlsx)")
	print("\t -u\t database user")
	print("\t -p\t path to database password")

def main(argv):
	global PYBICO_VERBOSE

	try:
		opts, args = getopt.getopt(argv, "hvo:s:i:e:u:p:", ["help"])
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
		elif o == "-o":
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
	if import_filename != "":
		pybico_import(import_format, import_filename, user, password)
	if export_filename != "":
		data = pybico_extract(user, password)
		pybico_export(export_format, export_filename, data)

if __name__ == '__main__':
	main(sys.argv[1:])