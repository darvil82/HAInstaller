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








class Version(str):
    """Simple object for managing versions a bit easier.
        >>> Version("1.4.5-2") < Version("1.5-6")
        >>> True
    """

    def __init__(self, version: str, sep: str = ".") -> None:
        """The string format should be something like `1.2.3` or `1.2.3-4`.
            * `sep` is the seperator of every version field. A dot is normally what is used."""

        self.version = version
        self._sep = sep
        self._maxLenght = 16
        self.stripped = self._stripVersion(self.version)
        self._float = self._toFloat(self.stripped)


    def _stripVersion(self, string: str) -> str:
        """Remove any character from string which isn't a number, dot, or -"""

        endStr = ""
        for char in string:
            if char.isdigit() or char in ".-":
                endStr += char
                continue
        return endStr


    def _toFloat(self, version: str) -> list:
        parts = version.split("-")

        if version:
            main = parts[0].split(self._sep)
            result = float("".join(main))
        else:
            result = 0


        if self._countChars(int(result)) < self._maxLenght:
            for x in range(0, self._maxLenght - self._countChars(int(result))):
                result *= 10
        else:
            raise Exception(f"Maximun Version lenght exceeded. ({self._maxLenght})")

        if len(parts) > 1:
            result += float(parts[1]) / 10
        return result


    def _countChars(self, object) -> int:
        cnt = 0
        for x in str(object):
            cnt += 1
        return cnt

    def __lt__(self, other) -> bool:
        return self._float < other._float

    def __gt__(self, other) -> bool:
        return self._float > other._float

    def __eq__(self, other) -> bool:
        return self._float == other._float

    def __repr__(self) -> str:
        return self.stripped

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        return self.stripped