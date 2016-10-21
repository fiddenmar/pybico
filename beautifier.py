import regex as re
from author import Author
from source import Source
from publication import Publication

class Beautifier:

	def __init__(self):
		pass

	def beautify(data):
		beautified_data = []
		for publication in data:
			beautified_publication = Publication()
			beautified_publication.title = beautify_title(publication.title)
			beautified_publication.source = beautify_source(publication.source)
			beautified_publication.misc = beautify_misc(publication.misc)
			beautified_publication.author = beautify_author(publication.author)
			beautified_data.append(beautified_publication)
		return beautified_data

	def beautify_title(title):
		beautified_title = ""
		return beautified_title

	def beautify_source(source):
		beautified_source = ""
		return beautified_source

	def beautify_misc(misc):
		beautified_misc = ""
		return beautified_misc

	def beautify_author(author):
		beautified_author = ""
		return beautified_author