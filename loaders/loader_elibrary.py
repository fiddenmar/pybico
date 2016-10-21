import requests
import regex as re
from author import Author
from source import Source
from publication import Publication

class Loader:

	def __init__(self):
		pass

	def load(self, filename = None):
		self.filename = filename if filename else "data."+self.load_format
		data = []
		data = self.load_data()
		return data

	def load_data(self):
		data = []
		f = open(self.filename, 'r')
		content = f.read()
		author_ids = content.split('\n')
		print(author_ids)
		article_reg_string = r'id="arw(?P<id>\d*).+?".*?a href=.*?<b>(?P<article>.*?)<\/b>.*?<i>(?P<authors>.*?)<\/i>.*?<font color=.+?>((.*?В сборнике: )?<a .+?>(?P<source>.+?)<\/a>)?(?P<misc>.+?)<\/td'
		article_reg = re.compile(article_reg_string, re.UNICODE)
		rsci_reg_string = r'Входит в РИНЦ.*?<font color=#00008f>(?P<rsci>.*?)<\/font>.*?(Импакт-фактор журнала в РИНЦ.*?<font color=#00008f>(?P<rsci_factor>\d+)<\/font>)?'
		scopus_reg_string = r'.*?Входит в Scopus.*?<font color=#00008f>(?P<scopus>.*?)<\/font>.*?(Импакт-фактор журнала в Scopus.*?<font color=#00008f>(?P<scopus_factor>\d+)<\/font>)?'
		wos_reg_string = r'.*?Входит в Web of Science.*?<font color=#00008f>(?P<wos>.*?)<\/font>.*?(Импакт-фактор журнала в Web of Science.*?<font color=#00008f>(?P<wos_factor>\d+)<\/font>)?'
		hac_reg_string = r'(Входит в ВАК.*?<font color=#00008f>(?P<hac>(да)|(нет))</font>)?.*(Импакт-фактор журнала в ВАК.*?<font color=#00008f>(?P<hac_factor>\d+)</font>)?'
		status_reg_string = rsci_reg_string+scopus_reg_string+wos_reg_string+hac_reg_string
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
					data.append(({"authors": split_authors(clean(article_res[2], p)), "article": clean(article_res[1], p),
						"source": clean(article_res[3], p), "misc": clean(article_res[6], p),
						"scopus": get_result(status_res[0][3], status_res[0][5]),
						"wos": get_result(status_res[0][6], status_res[0][8]),
						"hac": get_result(status_res[0][9], status_res[0][11]),
						"rsci": get_result(status_res[0][0], status_res[0][2])
						}))
		return data

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

def clean(string, p):
	result = p.sub('', string)
	return result

def get_result(found, factor):
	if found != "да":
		return 0
	if factor == '':
		return -1
	return factor