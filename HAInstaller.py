from os import path, listdir, system as runsys
import winreg
from srctools import cmdseq, clean_line
from tempfile import TemporaryFile
from urllib import request
from json import loads as jsonLoads
from zipfile import ZipFile




AVAILABLE_GAMES = {
	# Game Folder:		fgdname | (fgdname, folder2)
	"Portal 2": "portal2",
	"Alien Swarm": "asw",
	"Black Mesa": ("bms", "blackmesa"),
	"Counter-Strike Global Offensive": "csgo",
	"Half-Life 2": "hl2",
	"Garry's Mod": "gmod",
	"Infra": "infra",
	"Left 4 Dead": "l4d",
	"Left 4 Dead 2": "left4dead2",
	"Portal": "portal",
	"Team Fortress 2": "tf2"
}


GAMEINFO_ENTRY = "Game\tHammer"







def msglogger(string, type=None):
	"""
	Types: good, bad, loading
	"""
	if type == "bad":
		prefix = "\x1b[91m[ E ]"
	elif type == "good":
		prefix = "\x1b[92m[ √ ]"
	elif type == "loading":
		prefix = "\x1b[33m[...]"
	
	print(f"{prefix} {string}\x1b[0m")






def getSteamPath() -> str:
	"""
	Return a string with the path where Steam is located. First checks the registry key for SteamPath, and if it can't find it, the path will be prompted to the user.
	"""
	def checkPath(filename: str) -> bool:
		"""
		Check if the filepath supplied is valid and actually contains Steam.
		"""
		STEAM_CONTENTS = {
			'crashhandler.dll', 'crashhandler64.dll', 'CSERHelper.dll', 'd3dcompiler_46.dll', 'd3dcompiler_46_64.dll', 'GameOverlayRenderer.dll', 'GameOverlayRenderer64.dll',
			'GfnRuntimeSdk.dll', 'icui18n.dll', 'icuuc.dll', 'libavcodec-58.dll', 'libavformat-58.dll', 'libavresample-4.dll', 'libavutil-56.dll', 'libfreetype-6.dll',
			'libharfbuzz-0.dll', 'libswscale-5.dll', 'libx264-142.dll', 'openvr_api.dll', 'SDL2.dll', 'SDL2_ttf.dll', 'Steam.dll', 'Steam2.dll', 'steamclient.dll', 'steamclient64.dll',
			'SteamOverlayVulkanLayer.dll', 'SteamOverlayVulkanLayer64.dll', 'SteamUI.dll', 'steamwebrtc.dll', 'steamwebrtc64.dll', 'tier0_s.dll', 'tier0_s64.dll', 'v8.dll', 'video.dll',
			'VkLayer_steam_fossilize.dll', 'VkLayer_steam_fossilize64.dll', 'vstdlib_s.dll', 'vstdlib_s64.dll', 'zlib1.dll', 'GameOverlayUI.exe', 'steam.exe', 'steamerrorreporter.exe',
			'steamerrorreporter64.exe', 'streaming_client.exe', 'uninstall.exe', 'WriteMiniDump.exe'
		}

		if path.isdir(filename):
			for steamfile in STEAM_CONTENTS:
				if not path.exists(path.join(filename, steamfile)):
					print(f"The directory '{filename}' isn't a valid Steam directory.")
					break
				else:
					return True
		else:
			print(f"The directory '{filename}' does not exist.")


	try:
		hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\Valve\Steam")
		folder = winreg.QueryValueEx(hkey, "SteamPath")[0]
		winreg.CloseKey(hkey)
	except Exception:
		print("Couldn't find the Steam path, please specify a directory: ", end="")
		folder = input()

	while not checkPath(folder):
		print("Try again: ", end="")
		folder = input()

	msglogger(f"Got Steam path ('{folder}')", "good")
	return folder








def selectGame():
	"""
	Let the user select one of their games.
	"""
	usingGames = []
	for game in listdir(commonPath):
		if game in AVAILABLE_GAMES:
			usingGames.append(game)

	msglogger("Select a game to install HammerAddons:", "loading")
	lstCounter = 1
	for game in usingGames:
		print(f"\t{lstCounter}: {game}")
		lstCounter += 1
	
	while True:
		try:
			usrInput = int(input())
			if usrInput not in range(1, len(usingGames) + 1):
				raise ValueError
			print("\x1b[A\x1b[2K", end="")
			msglogger(f"Selected game '{usingGames[usrInput - 1]}'", "good")
			return usingGames[usrInput - 1]

		except (ValueError, IndexError):
			print("\x1b[A\x1b[2K", end="")
			pass

	






def parseCmdSeq():
	"""
	Read the user's CmdSeq.wc file, and add the postcompiler commands to it. This will also check if there's already a postcompiler command being used.
	"""
	msglogger("Adding postcompiler compile commands", "loading")
	
	gameBin = path.join(commonPath, selectedGame, "bin\\")
	cmdSeqPath = path.join(gameBin, "CmdSeq.wc")
	cmdsAdded = 0

	postCompilerCmd = {
		"exe": path.join(gameBin, "postcompiler\\bin\postcompiler.exe"),
		"args": "--propcombine $path\$file"
	}

	if path.isfile(cmdSeqPath):
		with open(cmdSeqPath, "rb") as cmdfile:
			data = cmdseq.parse(cmdfile)

		for config in data:
			foundBsp = False
			commands = data.get(config)
			for cmd in commands:
				exeValue = getattr(cmd, "exe")
				if foundBsp:
					if "postcompiler" not in str(exeValue).lower():
						commands.insert(commands.index(cmd), cmdseq.Command(postCompilerCmd["exe"], postCompilerCmd["args"]))
						cmdsAdded += 1
					break
				if exeValue == "$bsp_exe":
					foundBsp = True
					continue

		with open(cmdSeqPath, "wb") as cmdfile:
			cmdseq.write(data, cmdfile)
		
		if cmdsAdded == 0:
			msglogger("No need to add more commands", "good")
		else: msglogger(f"Added {cmdsAdded} command/s successfully", "good")

	else:
		msglogger(f"Couldn't find the CmdSeq.wc file in the game '{selectedGame}'. Perhaps you forgot to launch Hammer for the first time?", "bad")
		quit()
	






def downloadAddons():
	"""
	Download and unzip all necessary files.
	"""
	
	gamePath = path.join(commonPath, selectedGame)
	url = "https://api.github.com/repos/TeamSpen210/HammerAddons/releases/latest"

	with request.urlopen(url) as data:
		release = jsonLoads(data.read())
		dwnUrl = release.get("assets")[0].get("browser_download_url")
		version = release.get("tag_name")

		msglogger(f"Downloading required files of latest version {version}", "loading")

		with request.urlopen(dwnUrl) as data, TemporaryFile() as tempfile:
			tempfile.write(data.read())
			with ZipFile(tempfile) as zipfile:
				for file in zipfile.namelist():
					if file.startswith("postcompiler/"):
						zipfile.extract(file, path.join(gamePath, "bin\\"))
					elif file.startswith("hammer/"):
						zipfile.extract(file, gamePath)
					elif file.startswith(f"instances/{inGameFolder}"):
						zipfile.extract(file, path.join(gamePath, "sdk_content\\maps\\"))
			
				zipfile.extract(f"{AVAILABLE_GAMES.get(selectedGame)}.fgd", path.join(gamePath, "bin\\"))

	msglogger("Downloaded all files!", "good")







def parseGameInfo():
	"""
	Add the 'Game	Hammer' entry into the Gameinfo file while keeping the old contents.
	"""
	msglogger("Modifying the GameInfo.txt file", "loading")
	gameInfoPath = path.join(commonPath, selectedGame, inGameFolder, "gameinfo.txt")

	def get_indent(string) -> str:
		indent = ""
		for x in string:
			if x in {" ", "\t"}:
				indent += x
			else:
				return indent

	with open(gameInfoPath, encoding="utf8") as file:
		data = list(file)
	for number, line in reversed(list(enumerate(data))):
		strip_line = clean_line(line)
		if strip_line == GAMEINFO_ENTRY:
			msglogger("Already modified!", "good")
			break
		elif "|gameinfo_path|" in strip_line:
			data.insert(number + 1, f"{get_indent(line)}{GAMEINFO_ENTRY}\n")
			with open(gameInfoPath, "w") as file:
				for line in data:
					file.write(line)
			msglogger("Done!", "good")
			break
		
	
	









	





def main():
	global inGameFolder, selectedGame, steamPath, commonPath

	steamPath = getSteamPath()
	

	commonPath = path.join(steamPath, "steamapps\common")
	runsys("")

	try:
		selectedGame = selectGame()
		
		if isinstance(AVAILABLE_GAMES.get(selectedGame), str):
			inGameFolder = AVAILABLE_GAMES.get(selectedGame)
		else:
			inGameFolder = AVAILABLE_GAMES.get(selectedGame)[0]

		parseCmdSeq()
		parseGameInfo()
		downloadAddons()
	except KeyboardInterrupt:
		msglogger("Installation Interrupted", "bad")
		quit()
	msglogger(f"Finished installing HammerAddons for {selectedGame}!", "good")

	
	






	


	
	

		





if __name__ == "__main__":
	main()