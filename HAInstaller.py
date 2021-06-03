from os import path, listdir, system as runsys
import winreg
import json
from srctools import cmdseq




def getSteamPath() -> str:
	"""
	Return a string with the path where Steam is located. First checks the registry key for SteamPath, and if it can't find it, the path will be prompted to the user.
	"""
	def checkPath(filename: str) -> bool:
		"""
		Check if the filepath supplied is valid and actually contains Steam.
		"""
		STEAM_CONTENTS = (
			'crashhandler.dll', 'crashhandler64.dll', 'CSERHelper.dll', 'd3dcompiler_46.dll', 'd3dcompiler_46_64.dll', 'GameOverlayRenderer.dll', 'GameOverlayRenderer64.dll',
			'GfnRuntimeSdk.dll', 'icui18n.dll', 'icuuc.dll', 'libavcodec-58.dll', 'libavformat-58.dll', 'libavresample-4.dll', 'libavutil-56.dll', 'libfreetype-6.dll',
			'libharfbuzz-0.dll', 'libswscale-5.dll', 'libx264-142.dll', 'openvr_api.dll', 'SDL2.dll', 'SDL2_ttf.dll', 'Steam.dll', 'Steam2.dll', 'steamclient.dll', 'steamclient64.dll',
			'SteamOverlayVulkanLayer.dll', 'SteamOverlayVulkanLayer64.dll', 'SteamUI.dll', 'steamwebrtc.dll', 'steamwebrtc64.dll', 'tier0_s.dll', 'tier0_s64.dll', 'v8.dll', 'video.dll',
			'VkLayer_steam_fossilize.dll', 'VkLayer_steam_fossilize64.dll', 'vstdlib_s.dll', 'vstdlib_s64.dll', 'zlib1.dll', 'GameOverlayUI.exe', 'steam.exe', 'steamerrorreporter.exe',
			'steamerrorreporter64.exe', 'streaming_client.exe', 'uninstall.exe', 'WriteMiniDump.exe'
		)

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

	return folder








def selectGame():
	AVAILABLE_GAMES = (
		"Portal 2",
		"Alien Swarm",
		"Black Mesa",
		"Counter-Strike Global Offensive",
		"Half-Life 2",
		"Garry's Mod",
		"Infra",
		"Left 4 Dead",
		"Left 4 Dead 2",
		"Portal",
		"Team Fortress 2"
	)

	commonFolder = path.join(steamPath, "steamapps\common")
	usingGames = []
	for game in listdir(commonFolder):
		if game in AVAILABLE_GAMES:
			usingGames.append(game)

	print("Select a game to install HammerAddons:")
	lstCounter = 1
	for game in usingGames:
		print(f"\t{lstCounter}: {game}")
		lstCounter += 1
	
	while True:
		try:
			usrInput = int(input())
			if usrInput not in range(1, len(usingGames)):
				print("\x1b[A\x1b[2K", end="")
				continue
			return usingGames[usrInput - 1]

		except (ValueError, IndexError):
			print("\x1b[A\x1b[2K", end="")
			pass

	
	





		


	


steamPath = getSteamPath()
runsys("")

def main():
	selectGame()
	






	


	
	

		





if __name__ == "__main__":
	main()