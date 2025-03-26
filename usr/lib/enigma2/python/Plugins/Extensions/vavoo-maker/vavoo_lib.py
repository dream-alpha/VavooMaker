#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from os import path as os_path, popen, remove as os_remove
from random import choice
from re import split, sub
from sys import version_info
from time import time
from unicodedata import normalize

import json
import requests

PY3 = False
PY3 = version_info[0] == 3

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('vavoo-maker'))


def decodeHtml(text):
	if PY3:
		import html
		text = html.unescape(text)
	else:
		from six.moves import html_parser
		h = html_parser.HTMLParser()
		text = h.unescape(text.decode('utf8')).encode('utf8')

	html_replacements = {
		'&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>', '&ndash;': '-',
		'&quot;': '"', '&ntilde;': '~', '&rsquo;': "'", '&nbsp;': ' ',
		'&equals;': '=', '&quest;': '?', '&comma;': ',', '&period;': '.',
		'&colon;': ':', '&lpar;': '(', '&rpar;': ')', '&excl;': '!',
		'&dollar;': '$', '&num;': '#', '&ast;': '*', '&lowbar;': '_',
		'&lsqb;': '[', '&rsqb;': ']', '&half;': '1/2', '&DiacriticalTilde;': '~',
		'&OpenCurlyDoubleQuote;': '"', '&CloseCurlyDoubleQuote;': '"'
	}

	for key, val in html_replacements.items():
		text = text.replace(key, val)
	return text.strip()


def rimuovi_parentesi(testo):
	return sub(r'\s*\([^)]*\)\s*', ' ', testo).strip()


def sanitizeFilename(filename):
	"""Return a fairly safe version of the filename.

	We don't limit ourselves to ascii, because we want to keep municipality
	names, etc, but we do want to get rid of anything potentially harmful,
	and make sure we do not exceed Windows filename length limits.
	Hence a less safe blacklist, rather than a whitelist.
	"""
	blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0", "(", ")", " "]
	reserved = [
		"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
		"COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
		"LPT6", "LPT7", "LPT8", "LPT9",
	]  # Reserved words on Windows
	filename = "".join(c for c in filename if c not in blacklist)
	# Remove all charcters below code point 32
	filename = "".join(c for c in filename if 31 < ord(c))
	filename = normalize("NFKD", filename)
	filename = filename.rstrip(". ")  # Windows does not allow these at end
	filename = filename.strip()
	if all([x == "." for x in filename]):
		filename = "__" + filename
	if filename in reserved:
		filename = "__" + filename
	if len(filename) == 0:
		filename = "__"
	if len(filename) > 255:
		parts = split(r"/|\\", filename)[-1].split(".")
		if len(parts) > 1:
			ext = "." + parts.pop()
			filename = filename[:-len(ext)]
		else:
			ext = ""
		if filename == "":
			filename = "__"
		if len(ext) > 254:
			ext = ext[254:]
		maxl = 255 - len(ext)
		filename = filename[:maxl]
		filename = filename + ext
		filename = filename.rstrip(". ")
		if len(filename) == 0:
			filename = "__"
	return filename


def get_external_ip():
	try:
		return popen('curl -s ifconfig.me').readline().strip()
	except:
		pass
	try:
		return requests.get('https://v4.ident.me').text.strip()
	except:
		pass
	try:
		return requests.get('https://api.ipify.org').text.strip()
	except:
		pass
	try:
		return requests.get('https://api.myip.com/').json().get("ip", "")
	except:
		pass
	try:
		return requests.get('https://checkip.amazonaws.com').text.strip()
	except:
		pass
	return None


def convert_to_unicode(data):
	"""
	In Python 3 le stringhe sono già Unicode, quindi:
	- Se data è bytes, decodificalo.
	- Se è str, restituiscilo così com'è.
	"""
	if isinstance(data, bytes):
		return data.decode('utf-8')
	elif isinstance(data, str):
		return data
	elif isinstance(data, dict):
		return {convert_to_unicode(k): convert_to_unicode(v) for k, v in data.items()}
	elif isinstance(data, list):
		return [convert_to_unicode(item) for item in data]
	return data


def set_cache(key, data, timeout):
	"""Salva i dati nella cache."""
	file_path = os_path.join(PLUGIN_PATH, key + '.json')
	try:
		if version_info[0] < 3:
			import io
			with io.open(file_path, 'w', encoding='utf-8') as cache_file:
				json.dump(convert_to_unicode(data), cache_file, indent=4, ensure_ascii=False)
		else:
			with open(file_path, 'w', encoding='utf-8') as cache_file:
				json.dump(convert_to_unicode(data), cache_file, indent=4, ensure_ascii=False)
	except Exception as e:
		print("Error saving cache:", e)


def get_cache(key):
	file_path = os_path.join(PLUGIN_PATH, key + '.json')
	if os_path.exists(file_path) and os_path.getsize(file_path) > 0:
		try:
			if version_info[0] < 3:
				import io
				with io.open(file_path, 'r', encoding='utf-8') as cache_file:
					data = json.load(cache_file)
			else:
				with open(file_path, 'r', encoding='utf-8') as cache_file:
					data = json.load(cache_file)

			if isinstance(data, dict):
				if data.get('sigValidUntil', 0) > int(time.time()):
					if data.get('ip', "") == get_external_ip():
						return data.get('value')
			else:
				print("Unexpected data format in {}: Expected a dict, got {}".format(file_path, type(data)))
		except ValueError as e:
			print("Error decoding JSON from", file_path, ":", e)
		except Exception as e:
			print("Unexpected error reading cache file {}:".format(file_path), e)
		os_remove(file_path)
	return None


def getAuthSignature():
	signfile = get_cache('signfile')
	if signfile:
		return signfile

	veclist = get_cache("veclist")
	if not veclist:
		veclist = requests.get("https://raw.githubusercontent.com/Belfagor2005/vavoo/refs/heads/main/data.json").json()
		set_cache("veclist", veclist, timeout=3600)

	sig = None
	i = 0
	while not sig and i < 50:
		i += 1
		vec = {"vec": choice(veclist)}
		req = requests.post('https://www.vavoo.tv/api/box/ping2', data=vec).json()
		sig = req.get('signed') or req.get('data', {}).get('signed') or req.get('response', {}).get('signed')

	if sig:
		set_cache('signfile', convert_to_unicode(sig), timeout=3600)
	return sig
