from time import sleep
from os import system as runsys, environ
from sys import exit



__all__ = [
	"msgLogger",
	"closeScript",
	"getIndent",
	"isProcess",
	"Version"
]



def msgLogger(*values: object, type: str = None, blink: bool = False, end: str = "\n"):
	"""
	Print a message out on the terminal.
		- Types: `good, error, loading, warning`
	"""

	MSG_PREFIX = {
		"error":    "\x1b[91m[ E ]",
		"good":     "\x1b[92m[ √ ]\x1b[97m",
		"loading":  "\x1b[33m[...]",
		"warning":  "\x1b[96m[ ! ]"
	}

	msg = f"\x1b[9999D\x1b[4m{MSG_PREFIX.get(type, '[   ]')}\x1b[24m {' '.join(str(item) for item in values)}\x1b[0m\x1b[K"

	if blink:
		print(f"\x1b[7m{msg}\x1b[27m", end="", flush=True)
		sleep(0.25)

	print(msg, end=end)




def closeScript(errorlevel: int = 0):
	"""Closes the script with an errorlevel"""

	runsys("pause > nul")
	exit(errorlevel)




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

		self.version = version
		self._seps = seps
		self.stripped = self._strip(self.version)
		self._splitted = self._split(self.stripped)


	def _strip(self, string: str) -> str:
		"""Remove any character from string which isn't a number, or any of the separators"""

		endStr = ""
		for char in string:
			if char.isdigit() or char in ".-":
				endStr += char
				continue

		if endStr == "":
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

	def __lt__(self, other) -> bool:
		return self._compare(other, self)

	def __eq__(self, other) -> bool:
		return self._splitted == other._splitted

	def __repr__(self) -> str:
		return self.stripped

	def __hash__(self) -> int:
		return hash(str(self))

	def __str__(self) -> str:
		return self.stripped