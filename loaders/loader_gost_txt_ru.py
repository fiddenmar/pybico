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
		items = content.split('\n')
		rn = r"(?P<authors>((\pL\. ?(\pL\. )?\pL+,? )|(\pL+ \pL\. ?(\pL\.)?,? )|(\p{Lu}\p{Ll}+ \p{Lu}\p{Ll}+,? ))+)" #regular for authors
		ra = r"(?P<article>\p{Lu}\p{Ll}+ \p{Ll}+.*?) *\/\/ *" #regular for article
		rj = r'(?P<source>[ \pL"“”]+)' #regular for source
		rm = r"(?P<misc>.+)" #regular for misc
		reg_ru = re.compile(rn+ra+rj+rm, re.UNICODE)
		for item in items:
			res = None
			res = reg_ru.match(item.strip())
			if res != None:
				publication = Publication()
				publication.authors = Author.parseAuthors(res.group("authors"))
				data.append({"authors": split_authors(res.group("authors")), "article": res.group("article"), "source": res.group("source"), "misc": res.group("misc")})
			else:
				print("Wrong line: " + item)
		return data

def split_authors(res):
	authors = res.split(', ')
	new_authors = []
	for author in authors:
		new_authors.append(author.strip().replace(". ", "."))
	return new_authors

def clean(string, p):
	result = p.sub('', string)
	return result

def get_result(found, factor):
	if found != "да":
		return 0
	if factor == '':
		return -1
	return factor