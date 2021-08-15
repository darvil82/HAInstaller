from time import sleep
from os import system as runsys, environ
from sys import exit



__all__ = [
	"getIndent",
	"isProcess",
	"Version"
]





def getIndent(string: str) -> str:
	"""Return indentation from supplied string"""

	indent = ""
	for x in string:
		if x in " \t":
			indent += x
		else:
			return indent




def isProcess(process: str) -> bool:
	"""Checks if the process name given is running. String must contain the name of the program to find, including extension."""

	tempFile = f"{environ['TEMP']}\\ha"

	runsys(f"tasklist /FI \"IMAGENAME eq {process}\" > {tempFile}")
	with open(tempFile) as f:
		return process in f.read()








class Version():
	"""Simple object for managing versions a bit easier.
		>>> Version("1.4.5-2") < Version("1.5-6")
		>>> True
	"""

	def __init__(self, version: str, seps: list = [".", "-"]) -> None:
		"""
		The string format should be something like `1.2.3` or `1.2.3-4`.

		- `sep` is the seperator of every version field. A dot and a '-' is normally what is used.

		The values separated by dots are considered as the 'main' values of the version, and the number
		after the '-' is considered as a subversion value, which is less important.
		"""

		self._seps = seps
		self._stripped = self._strip(version)
		self._splitted = self._split(self._stripped)


	def _strip(self, string: str) -> str:
		"""Remove any character from string which isn't a number, or any of the separators"""

		endStr = ""
		for char in string:
			if char.isdigit() or char in ".-":
				endStr += char
				continue

		if endStr == "" or ".." in endStr:
			return "0"
		else:
			return endStr


	def _split(self, ver: str) -> list:
		split = ver.split(self._seps[1])
		main = [int(hoho) for hoho in split[0].split(self._seps[0])]

		# Remove all the trailing 0's of version, since those have no value.
		for number, item in reversed(list(enumerate(main))):
			if item == 0:
				main.pop(number)
			else:
				break

		# Ignore empty fields
		if len(split) > 1 and split[1] != "":
			sub = int(split[1])
		else:
			sub = 0

		return [main, sub]


	def _compare(self, first: object, second: object):
		ver1 = first._splitted
		ver2 = second._splitted

		if not ver1[0] == ver2[0]:
			# Checking main
			ver2Main = ver2[0]
			for number, item in enumerate(ver1[0]):
				if len(ver2Main) == number:
					return True
				elif item > ver2Main[number]:
					return True
				elif item < ver2Main[number]:
					return False
				elif item == ver2Main[number]:
					continue
			return False
		else:
			# Checking the second value
			return ver1[1] > ver2[1]


	def __gt__(self, other) -> bool:
		return self._compare(self, other)

	def __ge__(self, other) -> bool:
		return self.__gt__(other) or self.__eq__(other)

	def __lt__(self, other) -> bool:
		return self._compare(other, self)

	def __le__(self, other) -> bool:
		return self.__lt__(other) or self.__eq__(other)

	def __eq__(self, other) -> bool:
		return self._splitted == other._splitted

	def __repr__(self) -> str:
		return self._stripped

	def __hash__(self) -> int:
		return hash(str(self))

	def __str__(self) -> str:
		return self._stripped