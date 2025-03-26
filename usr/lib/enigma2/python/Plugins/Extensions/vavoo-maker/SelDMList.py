from Components.MenuList import MenuList
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT

# Definizione di default per la posizione e dimensione dei componenti
SELECTION_LIST_DESC = (50, 3, 650, 50)  # (dx, dy, dw, dh)
SELECTION_LIST_LOCK = (0, 2, 35, 35)  # (ix, iy, iw, ih)


def SelectionEntryComponent(description, value, index, selected):
	""" Crea una voce della lista con icona di selezione """
	dx, dy, dw, dh = SELECTION_LIST_DESC
	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT, description)
	]

	# Seleziona l'icona giusta in base allo stato
	if selected:
		selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "icons/lock_on.png"))
	else:
		selectionpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "icons/lock_off.png"))

	ix, iy, iw, ih = SELECTION_LIST_LOCK
	res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, selectionpng))

	return res


class SelectionList(MenuList):
	""" Lista personalizzata compatibile con Dreambox OE2.5 """

	def __init__(self, list=None, enableWrapAround=False):
		MenuList.__init__(self, list or [], enableWrapAround, content=eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 32))  # Imposta il font di default
		self.l.setItemHeight(50)  # Altezza dell'elemento della lista

	def addSelection(self, description, value, index, selected=True):
		""" Aggiunge un elemento alla lista """
		self.list.append(SelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		""" Inverte lo stato dell'elemento selezionato """
		if len(self.list):
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = SelectionEntryComponent(item[0], item[1], item[2], not item[3])
			self.setList(self.list)

	def getSelectionsList(self):
		""" Restituisce la lista degli elementi selezionati """
		return [(item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3]]

	def toggleAllSelection(self):
		""" Inverte lo stato di tutti gli elementi della lista """
		for idx, item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = SelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def removeSelection(self, item):
		""" Rimuove un elemento dalla lista """
		for it in self.list:
			if it[0][0:3] == item[0:3]:
				self.list.pop(self.list.index(it))
				self.setList(self.list)
				return

	def toggleItemSelection(self, item):
		""" Inverte la selezione di un elemento specifico """
		for idx, i in enumerate(self.list):
			if i[0][0:3] == item[0:3]:
				item = self.list[idx][0]
				self.list[idx] = SelectionEntryComponent(item[0], item[1], item[2], not item[3])
				self.setList(self.list)
				return

	def sort(self, sortType=False, flag=False):
		""" Ordina la lista """
		# sorting by sortType:
		# 0 - description
		# 1 - value
		# 2 - index
		# 3 - selected
		self.list.sort(key=lambda x: x[0][sortType], reverse=flag)
		self.setList(self.list)
