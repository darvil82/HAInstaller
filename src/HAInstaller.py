from time import sleep
import winreg
import argparse
from os import path, listdir, system as runsys
from srctools import cmdseq, clean_line, Property
from tempfile import TemporaryFile
from urllib import request
from json import loads as jsonLoads
from zipfile import ZipFile
from textwrap import dedent
from sys import exit
from platform import architecture

from utils import getIndent, isProcess, Version
from pbar import PBar, VT100




POSTCOMPILER_ARGS = "--propcombine $path\$file"
VERSION = Version("1.7.3")
AVAILABLE_GAMES: dict[str, tuple[str, str]] = {
	# Game definitions. These specify the name of the main game folder, and for every game, the fgd, and the second game folder inside.
	# Game Folder: (folder2, fgdname)

	"Alien Swarm": ("asw", "swarm"),
	"Black Mesa": ("bms", "blackmesa"),
	"Counter-Strike Global Offensive": ("csgo", "csgo"),
	"GarrysMod": ("garrysmod", "gmod"),
	"Half-Life 2": ("hl2", "hl2"),
	"Infra": ("infra", "infra"),
	"Left 4 Dead": ("l4d", "l4d"),
	"Left 4 Dead 2": ("left4dead2", "left4dead2"),
	"Portal": ("portal", "portal"),
	"Portal 2": ("portal2", "portal2"),
	"Team Fortress 2": ("tf", "tf")
}








def vLog(message: str, end="\n", onlyAppend: bool = False):
	"""Prints a message if verbose is on"""

	if args.verbose:
		if not onlyAppend: print(message, end=end, flush=True)

		with open("HAInstaller.log", "a", errors="ignore") as f:
			f.write(message + end)






def msgLogger(*values: object, type: str = None, blink: bool = False, end: str = "\n"):
	"""
	Print a message out on the terminal.
	@type: Available types: `good, error, loading, warning`
	"""

	MSG_PREFIX = {
		"error":    f"{VT100.color((255, 87, 87))}[ E ]",
		"good":     f"{VT100.color((48, 240, 134))}[ √ ]{VT100.color((255, 255, 255))}",
		"loading":  f"{VT100.color((235, 175, 66))}[...]",
		"warning":  f"{VT100.color((92, 160, 2557))}[ ! ]"
	}

	strs = ' '.join(str(item) for item in values)
	msg = f"{VT100.moveHoriz(-9999)}{VT100.underline}{MSG_PREFIX.get(type, '[   ]')}{VT100.noUnderline} {strs}{VT100.reset}{VT100.clearRight}"

	if blink:
		print(f"{VT100.underline}{msg}{VT100.noUnderline}", end="", flush=True)
		sleep(0.25)

	sleep(0.15)

	# progresssbar
	if type == "error":
		pbColor = (255, 87, 87)
	elif type == "good":
		pbColor = (48, 240, 134)
	elif type == "loading":
		pbColor = (235, 175, 66)
	elif type == "warning":
		pbColor = (92, 160, 255)

	global progressBar
	progressBar.colorset = {
		"horiz":	pbColor,
		"vert":		pbColor,
		"corner":	pbColor,
		"text":		{"outside":	pbColor}
	}
	progressBar.draw()

	print(msg, end=end)
	vLog(f">>> ({type}): {strs}", onlyAppend=True)		# print also to file if verbose is on






def closeScript(errorlevel: int = 0):
	"""Closes the script with an errorlevel"""

	runsys("pause > nul")
	print(VT100.bufferOld, end="")
	vLog("Script terminated\n\n\n\n", onlyAppend=True)
	exit(errorlevel)








def checkUpdates():
	"""Check if the latest version is not equal to the one that we are using"""

	url = "https://api.github.com/repos/DarviL82/HAInstaller/releases/latest"
	msgLogger("Checking for new versions", type="loading")

	try:
		with request.urlopen(url) as data:
			release = jsonLoads(data.read())
			version = Version(release.get("tag_name"))
	except Exception:
		msgLogger("An error ocurred while checking for updates", type="error")
		closeScript(1)

	if version > VERSION:
		msgLogger(f"There is a new version available.\n\tUsing:\t{VERSION}\n\tLatest:\t{version}", type="warning")
	else:
		msgLogger("Using latest version", type="good")








def parseArgs():
	"""Parse the arguments passed to the script"""

	global args
	argparser = argparse.ArgumentParser(
		epilog=dedent(f"""\
			Using version {VERSION}

			Repositories:
				HAInstaller:    {VT100.underline}https://github.com/DarviL82/HAInstaller{VT100.noUnderline}
				HammerAddons:   {VT100.underline}https://github.com/TeamSpen210/HammerAddons{VT100.noUnderline}
			"""
		),
		formatter_class=argparse.RawTextHelpFormatter
	)
	argparser.add_argument("-a", "--args", help=f"Arguments for the PostCompiler executable. Default are '{POSTCOMPILER_ARGS}'.", default=POSTCOMPILER_ARGS)
	argparser.add_argument("-g", "--game", help="The name of the game folder in which the addons will be installed.")
	argparser.add_argument("-v", "--version", help="Select the version of HammerAddons to install. Please keep in mind that some versions\nmight not be compatible with all the games. Default value is 'latest'.", default="latest")
	argparser.add_argument("--skipCmdSeq", help="Do not modify the CmdSeq.wc file.", action="store_true")
	argparser.add_argument("--skipGameinfo", help="Do not modify the gameinfo.txt file.", action="store_true")
	argparser.add_argument("--skipDownload", help="Do not download any files.", action="store_true")
	argparser.add_argument("--verbose", help="Show more information of all the steps and create a log file", action="store_true")
	argparser.add_argument("--ignoreHammer", help="Do not check if Hammer is running.", action="store_true")
	argparser.add_argument("--chkup", help="Check for new versions of the installer.", action="store_true")
	argparser.add_argument("--noPbar", help="Disable the progress bar", action="store_true")
	args = argparser.parse_args()

	if args.chkup:
		checkUpdates()
		exit()








def getSteamPath() -> tuple[str]:
	"""
	Return a tuple with with all the steam libraries that it can find. The first library in the tuple will always be the main Steam directory.

	First checks the registry key for SteamPath, and if it can't find it, the path will be prompted to the user.
	"""

	def checkPath(foldername: str) -> bool:
		"""Check if the filepath supplied is valid and actually contains Steam."""

		# All the files that the main Steam path should contain
		STEAM_CONTENTS = {
			'crashhandler.dll', 'crashhandler64.dll', 'CSERHelper.dll', 'd3dcompiler_46.dll', 'd3dcompiler_46_64.dll', 'GameOverlayRenderer.dll', 'GameOverlayRenderer64.dll',
			'GfnRuntimeSdk.dll', 'icui18n.dll', 'icuuc.dll', 'openvr_api.dll', 'SDL2.dll', 'SDL2_ttf.dll', 'Steam.dll', 'Steam2.dll', 'steamclient.dll', 'steamclient64.dll',
			'SteamOverlayVulkanLayer.dll', 'SteamOverlayVulkanLayer64.dll', 'SteamUI.dll', 'steamwebrtc.dll', 'steamwebrtc64.dll', 'tier0_s.dll', 'tier0_s64.dll', 'v8.dll', 'video.dll',
			'VkLayer_steam_fossilize.dll', 'VkLayer_steam_fossilize64.dll', 'GameOverlayUI.exe', 'steam.exe', 'steamerrorreporter.exe', 'steamerrorreporter64.exe','streaming_client.exe',
			'uninstall.exe', 'WriteMiniDump.exe'
		}

		# Check if the path supplied is actually the true Steam path by checking if it contains every file in STEAM_CONTENTS
		if path.isdir(foldername):
			dirLS = listdir(foldername)
			missingFiles = []

			for file in STEAM_CONTENTS:
				if file not in dirLS:
					missingFiles.append(file)

			if len(missingFiles) >= 1:
				vLog(f"\tDirectory '{foldername}' is missing the next file/s: '" + "', '".join(missingFiles) + "'")
				msgLogger(f"The directory '{foldername}' isn't a valid Steam directory. (Missing {len(missingFiles)} file/s.)", type="error")
				return False
			else:
				return True
		else:
			msgLogger(f"The directory '{foldername}' does not exist.", type="error")


	msgLogger("Finding Steam", type="loading")

	try:
		# Read the SteamPath registry key
		hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\Valve\Steam")
		folder = winreg.QueryValueEx(hkey, "SteamPath")[0]
		winreg.CloseKey(hkey)
	except Exception:
		msgLogger("Couldn't find the Steam path, please specify a directory: ", type="loading", end="")
		folder = input()

	# Continue asking for path until it is valid
	while not checkPath(folder):
		msgLogger("Try again: ", type="loading", end="")
		folder = input()


	steamlibs: list[str] = [folder]

	# Find other steam libraries (thanks TeamSpen)
	try:
		with open(path.join(folder, "steamapps/libraryfolders.vdf")) as file:
			conf = Property.parse(file)
	except FileNotFoundError:
			pass
	else:
		for prop in conf.find_key("LibraryFolders"):
			if prop.name.isdigit():
				# Huh, seems like this file has a new structure, so we check if it contains kvs inside or not
				if prop.has_children():
					lib = prop.value[0].value
				else:
					lib = prop.value

				if path.isdir(path.join(lib, "steamapps/common")):
					steamlibs.append(lib)

	if len(steamlibs) > 1:
		msgLogger(f"Found Steam libraries:\n\t'" + "'\n\t'".join(steamlibs) + "'", type="good")
	else:
		msgLogger(f"Found Steam library '{folder}'", type="good")

	return tuple(steamlibs)








def selectGame(steamlibs: tuple) -> tuple[str, str]:
	"""
	Let the user select one of their games.

	Returns a tuple containing the name of the game, and the location of the library that it belongs to.
	"""

	# Populate usingGames with the games that the user has installed and are supported by HammerAddons
	usingGames: list[tuple[str, str]] = []

	for lib in steamlibs:
		common = path.join(lib, "steamapps/common")
		for game in listdir(common):
			if game in AVAILABLE_GAMES:
				if path.exists(path.join(common, game, AVAILABLE_GAMES.get(game)[0], "gameinfo.txt")):
					usingGames.append((game, lib))

	if len(usingGames) == 0:
		# No supported games found, quitting
		msgLogger("Couldn't find any game supported by HammerAddons", type="error")
		closeScript(1)

	if args.game:
		# Check the string passed from the game argument
		if args.game in AVAILABLE_GAMES:
			for game, lib in usingGames:
				if args.game == game:
					msgLogger(f"Selected game '{args.game}'", type="good")
					return tuple((game, lib))

			msgLogger(f"The game '{args.game}' is not installed", type="error")
		else:
			msgLogger(f"The game '{args.game}' is not supported", type="error")


	# Print a simple select menu with all the available choices
	msgLogger("Select a game to install HammerAddons", type="loading")
	for number, game in enumerate(usingGames):
		if args.verbose:
			print(f"\t{number + 1}: {game[0]} ('{path.join(game[1], 'steamapps/common/', game[0])}')")
		else:
			print(f"\t{number + 1}: {game[0]}")
	print("")

	while True:
		try:
			usrInput = int(input(f"[1-{len(usingGames)}]: "))
			if usrInput not in range(1, len(usingGames) + 1):
				raise ValueError

			# The value is correct, so we move the cursor up the same number of lines taken by the menu to drawn, so then we can override it
			print(VT100.moveVert(-len(usingGames) - 2) + VT100.clearDown, end="")
			msgLogger(f"Selected game '{usingGames[usrInput - 1][0]}'", type="good")
			return tuple(usingGames[usrInput - 1])
		except (ValueError, IndexError):
			# If the value isn't valid, we move the terminal cursor up and then clear the line. This is done to not cause ugly spam when typing values
			print(VT100.moveVert(-1) + VT100.clearLine, end="")








def parseCmdSeq():
	"""Read the user's CmdSeq.wc file, and add the postcompiler commands to it. This will also check if there's already a postcompiler command being used."""

	msgLogger("Adding postcompiler compile commands", type="loading")

	gameBin = path.join(commonPath, selectedGame.lower(), "bin/")
	cmdSeqPath = path.join(gameBin, "CmdSeq.wc")
	cmdSeqDefaultPath = path.join(gameBin, "CmdSeqDefault.wc")

	if Version(args.version) >= Version("2.4.0") or args.version == "latest":
		if isSysX64:
			compFolder = "postcompiler_win64"
		else:
			compFolder = "postcompiler_win32"
	else:
		compFolder = "postcompiler"


	# Postcompiler command definition
	POSTCOMPILER_CMD: dict[str, str] = {
		"exe": path.join(gameBin, f"{compFolder}/postcompiler.exe"),
		"args": args.args.lower()
	}

	# If the CmdSeq.wc file does not exist, we then check for the file CmdSeqDefault.wc, which has the default commands. Copy it as CmdSeq.wc
	if not path.isfile(cmdSeqPath):
		if path.isfile(cmdSeqDefaultPath):
			with open(cmdSeqDefaultPath, "rb") as defCmdFile, open(cmdSeqPath, "wb") as CmdFile:
				CmdFile.write(defCmdFile.read())
		else:
			msgLogger(f"Couldn't find the 'CmdSeqDefault.wc' file in the game directory '{gameBin}'.", type="error")
			closeScript(1)



	with open(cmdSeqPath, "rb") as cmdfile:
		data = cmdseq.parse(cmdfile)

	# We check for the existence of the bsp command. If found, we append the postcompiler command right after it
	cmdsAdded = 0	# times we appended a postcompiler command
	cmdsFound = 0	# times we found VBSP
	for config in data:
		foundBsp = False
		commands = data.get(config)

		vLog(f"\n\tConfig: '{config}'")

		for index, cmd in enumerate(commands):
			exeValue = str(cmd.exe).lower()
			argValue = str(cmd.args).lower()

			vLog(f"\t\tL Command:\n\t\t\tExe:      '{exeValue}'\n\t\t\tArgument: '{argValue}'")

			if foundBsp:
				if POSTCOMPILER_CMD["exe"] != exeValue:
					commands.insert(index, cmdseq.Command(POSTCOMPILER_CMD["exe"], POSTCOMPILER_CMD["args"]))
					vLog("\t--- Found VBSP, appended command ---")
					cmdsAdded += 1
				else:
					if POSTCOMPILER_CMD["args"] != argValue:
						commands.pop(index)
						commands.insert(index, cmdseq.Command(POSTCOMPILER_CMD["exe"], POSTCOMPILER_CMD["args"]))
						vLog("\t--- Found postcompiler, re-appended command with new args ---")
						cmdsAdded += 1
				break
			if exeValue == "$bsp_exe":
				foundBsp = True
				cmdsFound += 1
				continue

	if cmdsFound < 1:
		msgLogger("Couldn't find any configuration with commands", type="error")
	elif cmdsAdded == 0:
		# No commands were added, no need to modify
		msgLogger("Found already existing commands", type="warning")
	else:
		with open(cmdSeqPath, "wb") as cmdfile:
			cmdseq.write(data, cmdfile)
		msgLogger(f"Added {cmdsAdded} command/s successfully", type="good")








def parseGameInfo():
	"""Add the 'Game	Hammer' entry into the Gameinfo file while keeping the old contents."""

	msgLogger("Checking GameInfo.txt", type="loading")
	gameInfoPath = path.join(commonPath, selectedGame, inGameFolder, "gameinfo.txt")

	if not path.exists(gameInfoPath):
		msgLogger(f"Couldn't find the '{gameInfoPath}' file", type="error")
		closeScript(1)

	with open(gameInfoPath, encoding="utf8") as file:
		data = list(file)

	for number, line in reversed(list(enumerate(data))):
		strip_line = clean_line(line).lower()

		vLog(f"\t{number}: {line}", end="")

		if all(item in strip_line for item in {"game", "hammer"}):
			# Hammer is already in there, skip
			vLog("\t^ Found 'Game  Hammer'. Skipping.")
			msgLogger("No need to modify", type="warning")
			break

		elif "|gameinfo_path|" in strip_line:
			# Append Game Hammer right after the |gameinfo_path| entry
			data.insert(number + 1, f"{getIndent(line)}Game\tHammer\n")
			with open(gameInfoPath, "w") as file:
				for line in data:
					file.write(line)

			vLog("\t^ Found '|gameinfo_path|'. Added 'Game  Hammer' entry.")
			msgLogger("Added a new entry", type="good")
			break








def downloadAddons():
	"""Download and unzip all necessary files."""

	gamePath = path.join(commonPath, selectedGame)
	releasesUrl = "https://api.github.com/repos/TeamSpen210/HammerAddons/releases"
	vdfUrl = "https://raw.githubusercontent.com/DarviL82/HAInstaller/main/resources/srctools.vdf"


	def getZipUrl(ver: str) -> tuple[str, str]:
		"""
		Return a tuple with the version tag, and the url of the zip download page from the version specified. (`(verTag, zipUrl)`)

		- `ver` is a string containing a version value, or `latest`.
		"""

		verS = Version(ver)

		with request.urlopen(releasesUrl) as data:
			data = jsonLoads(data.read())

		# Create a dict with all the versionTags: zipUrls
		# We iterate through every release getting the only values that we need, the "tag_name", and the "browser_download_url"
		versions: dict[str, str] = {}

		for release in data:
			tag = Version(release.get("tag_name"))
			url = release.get("assets")[0].get("browser_download_url")
			versions[tag] = url
			vLog(f"\tFound version {tag}\t('{url}')")


		if ver.lower() == "latest":
			# If ver arg is "latest" we get the first key and value from the versions dict
			return (tuple(versions.keys())[0], tuple(versions.values())[0])
		elif verS in versions.keys():
			# If the stripped ver is a key inside versions, return itself and it's value in the dict
			return (verS, versions[verS])
		else:
			# We didn't succeed, generate an error message and exit
			msgLogger(f"Version '{ver}' does not exist, available versions: '" + "', '".join(map(str, versions.keys())) + "'", type="error")
			closeScript(1)



	try:
		msgLogger(f"Looking up for {args.version} version", type="loading")

		version, zipUrl = getZipUrl(args.version)

		msgLogger(f"Downloading required files of version {version}", type="loading")

		# Download all required files for HammerAddons
		with request.urlopen(zipUrl) as data, TemporaryFile() as tempfile:
			vLog(f"\tDownloading '{zipUrl}'... ", end="")

			tempfile.write(data.read())

			vLog(f"Done")
			msgLogger(f"Unzipping files", type="loading")

			with ZipFile(tempfile) as zipfile:
				for file in zipfile.namelist():
					# Extract the files found to the locations that we want
					if file.startswith("postcompiler"):
						if isSysX64 and file.startswith("postcompiler_win64/"):
							zipfile.extract(file, path.join(gamePath, "bin/"))
							vLog(f"\tExtracted file '{selectedGame}/bin/{file}'")

						elif not isSysX64 and file.startswith("postcompiler_win32/"):
							zipfile.extract(file, path.join(gamePath, "bin/"))
							vLog(f"\tExtracted file '{selectedGame}/bin/{file}'")

						elif file.startswith("postcompiler/"):
							zipfile.extract(file, path.join(gamePath, "bin/"))
							vLog(f"\tExtracted file '{selectedGame}/bin/{file}'")



					if file.startswith("hammer/"):
						zipfile.extract(file, gamePath)
						vLog(f"\tExtracted file '{selectedGame}/{file}'")
					elif file.startswith(f"instances/{inGameFolder}/"):
						zipfile.extract(file, path.join(gamePath, "sdk_content/maps/"))
						vLog(f"\tExtracted file '{selectedGame}/sdk_content/maps/{file}'")

				# Extract the FGD file to the bin folder
				zipfile.extract(f"{AVAILABLE_GAMES.get(selectedGame)[1]}.fgd", path.join(gamePath, "bin/"))
				vLog(f"\tExtracted file '{selectedGame}/bin/{AVAILABLE_GAMES.get(selectedGame)[1]}.fgd'\n\n")


		# Download srctools.vdf, so we can modify it to have the correct game folder inside.
		vdfPath = path.join(gamePath, "srctools.vdf")
		if not path.exists(vdfPath):
			with request.urlopen(vdfUrl) as data:
				with open(vdfPath, "wb") as file:
					vLog(f"\tDownloading '{vdfUrl}'... ", end="")

					file.write(data.read())

					vLog(f"Done")
		else:
			vLog("\tFound 'srctools.vdf'. Skipping.")

		with open(vdfPath) as file:
			data = list(file)

		# Replace the gameinfo entry to match the game that we are installing
		for number, line in list(enumerate(data)):
			strip_line = clean_line(line).lower()

			vLog(f"\t{number}: {line}", end="")

			if "\"gameinfo\"" in strip_line:
				if f"\"{inGameFolder}/\"" in strip_line:
					# We found it already in there, skip
					vLog(f"\t^ Found \"'gameinfo' '{inGameFolder}/'\". Skipping.")
					break

				else:
					# It isn't there, remove it and add a new one to match the game
					data.pop(number)
					data.insert(number, f"{getIndent(line)}\"gameinfo\" \"{inGameFolder}/\"\n")
					vLog(f"\t^ Changed line to \"'gameinfo' '{inGameFolder}/'\".")

					with open(vdfPath, "w") as file:
						for line in data:
							file.write(line)
					break

	except Exception as error:
		if args.verbose: raise
		msgLogger(f"An error ocurred while downloading the files ({error})", type="error")
		closeScript(1)

	msgLogger("Downloaded all files", type="good")
















def main():
	global inGameFolder, selectedGame, commonPath, progressBar, isSysX64

	runsys("")  # This is required to be able to display VT100 sequences on Windows 10
	parseArgs()
	isSysX64 = "64" in architecture()[0]

	progressBar = PBar(range=(0, 6), position=(23, 4), text="Preparing...")
	progressBar.enabled = not args.noPbar and not args.verbose

	print(f"{VT100.bufferNew}\n{VT100.color((0, 255, 255))}{VT100.underline}TeamSpen's Hammer Addons Installer - v{VERSION}{VT100.reset}\n")
	if progressBar.enabled: print("\n\n\n")

	progressBar.draw()

	try:
		steamlibs = getSteamPath()

		progressBar.step()

		selectedGame, steamPath = selectGame(steamlibs)
		commonPath = path.join(steamPath, "steamapps/common")
		inGameFolder = AVAILABLE_GAMES.get(selectedGame)[0]

		progressBar.step()

		if not args.ignoreHammer:
			# We check continuosly if Hammer is open. Once it is closed, we continue.
			while isProcess("hammer.exe"):
				msgLogger("Hammer is running, please close it before continuing. Press any key to retry.", type="error", blink=True)
				runsys("pause > nul")
				print(VT100.moveVert(-1), end="")

		progressBar.text = "Processing CmdSeq"
		progressBar.step()
		if not args.skipCmdSeq: parseCmdSeq()
		progressBar.text = "Processing Gameinfo"
		progressBar.step()
		if not args.skipGameinfo: parseGameInfo()
		progressBar.text = "Downloading files"
		progressBar.step()
		if not args.skipDownload: downloadAddons()

	except KeyboardInterrupt:
		msgLogger("Installation interrupted", type="error")
		closeScript(1)

	progressBar.text = "Done!"
	progressBar.step()
	msgLogger(f"Finished installing HammerAddons for {selectedGame}!", type="good", blink=True)
	closeScript()



if __name__ == "__main__":
	main()
