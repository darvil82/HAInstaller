import winreg
from os import path, listdir, system as runsys
from srctools import cmdseq, clean_line, Property
from tempfile import TemporaryFile
from urllib import request
from json import loads as jsonLoads
from zipfile import ZipFile
from sys import exit
import argparse
from textwrap import dedent




POSTCOMPILER_ARGS = "--propcombine $path\$file"
VERSION = "1.4"
AVAILABLE_GAMES = {
    # Game definitions. These specify the name of the main game folder, and for every game, the fgd, and the second game folder inside.
    # Game Folder: (fgdname, folder2)
    
    "Alien Swarm": ("asw", "swarm"),
    "Black Mesa": ("bms", "blackmesa"),
    "Counter-Strike Global Offensive": ("csgo", "csgo"),
    "GarrysMod": ("gmod", "garrysmod"),
    "Half-Life 2": ("hl2", "hl2"),
    "Infra": ("infra", "infra"),
    "Left 4 Dead": ("l4d", "l4d"),
    "Left 4 Dead 2": ("left4dead2", "left4dead2"),
    "Portal": ("portal", "portal"),
    "Portal 2": ("portal2", "portal2"),
    "Team Fortress 2": ("tf2", "tf")
}








def msglogger(string, type=None, end="\n"):
    """
    Print a message out on the terminal.
    - Types: `good, error, loading, warning`
    """

    if type == "error":
        prefix = "\x1b[91m[ E ]"
    elif type == "good":
        prefix = "\x1b[92m[ √ ]\x1b[0m"
    elif type == "loading":
        prefix = "\x1b[33m[...]"
    elif type == "warning":
        prefix = "\x1b[96m[ ! ]"
    else:
        prefix = "[   ]"
    
    print(f"\x1b[4m\x1b[9999D{prefix}\x1b[24m {string}\x1b[0m\x1b[K", end=end)




def checkUpdates():
    """Check if the latest version is not equal to the one that we are using"""
    
    url = "https://api.github.com/repos/DarviL82/HAInstaller/releases/latest"
    msglogger("Checking for new versions", "loading")

    try:
        with request.urlopen(url) as data:
            release = jsonLoads(data.read())
            version = stripVersion(release.get("tag_name"))
    except Exception:
        msglogger("An error ocurred while checking for updates", "error")
        closeScript()
    
    if version != VERSION:
        msglogger(f"There is a new version available.\n\tUsing: {VERSION}\n\tLatest: {version}", "warning")
    else:
        msglogger("Using latest version", "good")




def closeScript():
    runsys("pause > nul")
    exit()




def get_indent(string) -> str:
    """Return indentation from supplied string"""

    indent = ""
    for x in string:
        if x in {" ", "\t"}:
            indent += x
        else:
            return indent



def stripVersion(string: str) -> str:
        """Remove any character from string which isn't a number or dot"""

        ver = ""
        for char in string:
            if char.isdigit() or char == ".":
                ver += char
        return ver







def parseArgs():
    """Parse the arguments passed to the script"""
    
    global args
    argparser = argparse.ArgumentParser(
        epilog=dedent(f"""\
            Using version {VERSION}

            Repositories:
                HAInstaller:    \x1b[4mhttps://github.com/L89David/HAInstaller\x1b[24m
                HammerAddons:   \x1b[4mhttps://github.com/TeamSpen210/HammerAddons\x1b[24m
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )
    argparser.add_argument("-a", "--args", help=f"Arguments for a hammer compile step. Default are '{POSTCOMPILER_ARGS}'", default=POSTCOMPILER_ARGS)
    argparser.add_argument("-g", "--game", help="The name of the game folder in which the addons will be installed.")
    argparser.add_argument("-v", "--version", help="Select the version of HammerAddons to install. Please keep in mind that all versions might not be compatible\nwith all the games. Default value is 'latest'.", default="latest")
    argparser.add_argument("--skipCmdSeq", help="Do not modify the CmdSeq.wc file.", action="store_false")
    argparser.add_argument("--skipGameinfo", help="Do not modify the gameinfo.txt file.", action="store_false")
    argparser.add_argument("--skipDownload", help="Do not download any files.", action="store_false")
    argparser.add_argument("--chkup", help="Check for new versions of the installer.", action="store_true")
    args = argparser.parse_args()

    if args.chkup:
        checkUpdates()
        exit()














def getSteamPath() -> tuple:
    """
    Return a tuple with with all the steam libraries that it can find. The first library in the tuple will always be the main Steam directory.

    First checks the registry key for SteamPath, and if it can't find it, the path will be prompted to the user.
    """

    def checkPath(filename: str) -> bool:
        """Check if the filepath supplied is valid and actually contains Steam."""

        # All the files that the main Steam path should contain
        STEAM_CONTENTS = {
            'crashhandler.dll', 'crashhandler64.dll', 'CSERHelper.dll', 'd3dcompiler_46.dll', 'd3dcompiler_46_64.dll', 'GameOverlayRenderer.dll', 'GameOverlayRenderer64.dll',
            'GfnRuntimeSdk.dll', 'icui18n.dll', 'icuuc.dll', 'libavcodec-58.dll', 'libavformat-58.dll', 'libavresample-4.dll', 'libavutil-56.dll', 'libfreetype-6.dll',
            'libharfbuzz-0.dll', 'libswscale-5.dll', 'libx264-142.dll', 'openvr_api.dll', 'SDL2.dll', 'SDL2_ttf.dll', 'Steam.dll', 'Steam2.dll', 'steamclient.dll', 'steamclient64.dll',
            'SteamOverlayVulkanLayer.dll', 'SteamOverlayVulkanLayer64.dll', 'SteamUI.dll', 'steamwebrtc.dll', 'steamwebrtc64.dll', 'tier0_s.dll', 'tier0_s64.dll', 'v8.dll', 'video.dll',
            'VkLayer_steam_fossilize.dll', 'VkLayer_steam_fossilize64.dll', 'vstdlib_s.dll', 'vstdlib_s64.dll', 'zlib1.dll', 'GameOverlayUI.exe', 'steam.exe', 'steamerrorreporter.exe',
            'steamerrorreporter64.exe', 'streaming_client.exe', 'uninstall.exe', 'WriteMiniDump.exe'
        }

        # Check if the path supplied is actually the true Steam path by checking if it contains every file in STEAM_CONTENTS
        if path.isdir(filename):
            for steamfile in STEAM_CONTENTS:
                if not path.exists(path.join(filename, steamfile)):
                    msglogger(f"The directory '{filename}' isn't a valid Steam directory.", "error")
                    break
                else:
                    return True
        else:
            msglogger(f"The directory '{filename}' does not exist.", "error")


    try:
        # Read the SteamPath registry key
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\Valve\Steam")
        folder = winreg.QueryValueEx(hkey, "SteamPath")[0]
        winreg.CloseKey(hkey)

    except Exception:
        msglogger("Couldn't find the Steam path, please specify a directory: ", "loading", "")
        folder = input()

    # Continue asking for path until it is valid
    while not checkPath(folder):
        msglogger("Try again: ", "loading", "")
        folder = input()


    steamlibs = [folder]

    # Find other steam libraries (thanks TeamSpen)
    try:
        with open(path.join(folder, "steamapps/libraryfolders.vdf")) as file:
            conf = Property.parse(file)
    except FileNotFoundError:
            pass
    else:
        for prop in conf.find_key("LibraryFolders"):
            if prop.name.isdigit():
                steamlibs.append(prop.value)

    msglogger(f"Got Steam path '{folder}'", "good")
    return tuple(steamlibs)








def selectGame(steamlibs) -> tuple:
    """
    Let the user select one of their games.
    
    Returns a tuple containing the name of the game, and the location of the library that it belongs to.
    """

    # Populate usingGames with the games that the user has installed and are supported by HammerAddons
    usingGames = []
    for lib in steamlibs:
        common = path.join(lib, "steamapps/common")
        for game in listdir(common):
            if game in AVAILABLE_GAMES:
                usingGames.append((game, lib))
    
    if len(usingGames) == 0:
        # No supported games found, quitting
        msglogger("Couldn't find any game supported by HammerAddons", "error")
        closeScript()
    
    if args.game:
        # Check the string passed from the game argument
        if args.game in AVAILABLE_GAMES:
            for game, lib in usingGames:
                if args.game == game:
                    msglogger(f"Selected game '{args.game}'", "good")
                    return tuple((args.game, lib))
            
            msglogger(f"The game '{args.game}' is not installed", "error")
        else:
            msglogger(f"The game '{args.game}' is not supported", "error")
        
    
    # Print a simple select menu with all the available choices
    msglogger("Select a game to install HammerAddons", "loading")
    for number, game in enumerate(usingGames):
        print(f"\t{number + 1}: {game[0]}")

    while True:
        try:
            usrInput = int(input())
            if usrInput not in range(1, len(usingGames) + 1):
                raise ValueError
            
            # The value is correct, so we move the cursor up the same number of lines taken by the menu to drawn, so then we can override it
            print(f"\x1b[{len(usingGames) + 1}A\x1b[0J", end="")
            msglogger(f"Selected game '{usingGames[usrInput - 1][0]}'", "good")
            return tuple(usingGames[usrInput - 1])

        except (ValueError, IndexError):
            # If the value isn't valid, we move the terminal cursor up and then clear the line. This is done to not cause ugly spam when typing values
            print("\x1b[A\x1b[2K", end="")
            pass








def parseCmdSeq():
    """Read the user's CmdSeq.wc file, and add the postcompiler commands to it. This will also check if there's already a postcompiler command being used."""

    msglogger("Adding postcompiler compile commands", "loading")
    
    gameBin = path.join(commonPath, selectedGame, "bin/")
    cmdSeqPath = path.join(gameBin, "CmdSeq.wc")
    cmdsAdded = 0

    # Postcompiler command definition
    POSTCOMPILER_CMD = {
        "exe": path.join(gameBin, "postcompiler/postcompiler.exe"),
        "args": args.args
    }

    if path.isfile(cmdSeqPath):
        with open(cmdSeqPath, "rb") as cmdfile:
            data = cmdseq.parse(cmdfile)

        # We check for the existence of the bsp command. If found, we append the postcompiler command right after it
        for config in data:
            foundBsp = False
            commands = data.get(config)

            for cmd in commands:
                exeValue = getattr(cmd, "exe")
                argValue = getattr(cmd, "args")
                
                if foundBsp:
                    if "postcompiler" not in str(exeValue).lower():
                        commands.insert(commands.index(cmd), cmdseq.Command(POSTCOMPILER_CMD["exe"], POSTCOMPILER_CMD["args"]))
                        cmdsAdded += 1
                    else:
                        if args.args.lower() != str(argValue).lower():
                            index = commands.index(cmd)
                            commands.pop(index)
                            commands.insert(index, cmdseq.Command(POSTCOMPILER_CMD["exe"], POSTCOMPILER_CMD["args"]))
                            cmdsAdded += 1
                    break
                if exeValue == "$bsp_exe":
                    foundBsp = True
                    continue

        if cmdsAdded == 0:
            # No commands were added, no need to modify
            msglogger("Found already existing commands", "warning")
        else:
            with open(cmdSeqPath, "wb") as cmdfile:
                cmdseq.write(data, cmdfile)
            
            msglogger(f"Added {cmdsAdded} command/s successfully", "good")

    else:
        msglogger(f"Couldn't find the CmdSeq.wc file in the game '{selectedGame}'. Perhaps you forgot to launch Hammer for the first time?", "error")
        closeScript()









def parseGameInfo():
    """Add the 'Game	Hammer' entry into the Gameinfo file while keeping the old contents."""

    msglogger("Checking GameInfo.txt", "loading")
    gameInfoPath = path.join(commonPath, selectedGame, inGameFolder, "gameinfo.txt")
    
    if not path.exists(gameInfoPath):
        msglogger(f"Couldn't find the file '{gameInfoPath}'", "error")
        closeScript()

    with open(gameInfoPath, encoding="utf8") as file:
        data = list(file)
    
    for number, line in reversed(list(enumerate(data))):
        strip_line = clean_line(line)

        if "game" in strip_line.lower() and "hammer" in strip_line.lower():
            # Hammer is already in there, skip
            msglogger("No need to modify", "warning")
            break
        
        elif "|gameinfo_path|" in strip_line:
            # Append Game Hammer right after the |gameinfo_path| entry
            data.insert(number + 1, f"{get_indent(line)}Game\tHammer\n")
            with open(gameInfoPath, "w") as file:
                for line in data:
                    file.write(line)
            msglogger("Added a new entry", "good")
            break













def downloadAddons():
    """Download and unzip all necessary files."""
    
    gamePath = path.join(commonPath, selectedGame)
    releasesUrl = "https://api.github.com/repos/TeamSpen210/HammerAddons/releases"
    vdfUrl = "https://raw.githubusercontent.com/DarviL82/HAInstaller/main/resources/srctools.vdf"


    def getZipUrl(ver) -> str:
        """
        Return a tuple with the version tag, and the url of the zip download page from the version specified. (`(verTag, zipUrl)`)
        
        - `ver` is a string containing a version value, or `latest`.
        """

        verS = stripVersion(ver)
    
        with request.urlopen(releasesUrl) as data:
            data = jsonLoads(data.read())

        # Create a dict with all the versionTags: zipUrls
        # We iterate through every release getting the only values that we need, the "tag_name", and the "browser_download_url"
        versions = {}
        for release in data:
            tag = stripVersion(release.get("tag_name"))
            url = release.get("assets")[0].get("browser_download_url")

            versions[tag] = url


        if ver == "latest":
            # If ver arg is "latest" we get the first key and value from the versions dict
            return (tuple(versions.keys())[0], tuple(versions.values())[0])
        elif verS in versions.keys():
            # If the stripped ver is a key inside versions, return itself and it's value in the dict
            return (verS, versions[verS])
        else:
            # We didn't succeed, generate an error message and exit
            errorMsg = ""
            for x in tuple(versions.keys()):
                errorMsg += f"'{x}', "
            
            msglogger(f"Version '{ver}' does not exist, available versions: {errorMsg}\x1b[2D.\x1b[K", "error")
            closeScript()

     

    try:
        version, zipUrl = getZipUrl(args.version)

        msglogger(f"Downloading required files of version {version}", "loading")

        # Download all required files for HammerAddons
        with request.urlopen(zipUrl) as data, TemporaryFile() as tempfile:
            tempfile.write(data.read())
            with ZipFile(tempfile) as zipfile:
                for file in zipfile.namelist():
                    # Extract the files found to the locations that we want
                    if file.startswith("postcompiler/"):
                        zipfile.extract(file, path.join(gamePath, "bin/"))
                    elif file.startswith("hammer/"):
                        zipfile.extract(file, gamePath)
                    elif file.startswith(f"instances/{inGameFolder}"):
                        zipfile.extract(file, path.join(gamePath, "sdk_content/maps/"))

                # Extract the FGD file to the bin folder
                zipfile.extract(f"{AVAILABLE_GAMES.get(selectedGame)[1]}.fgd", path.join(gamePath, "bin/"))
        

        # Download srctools.vdf, so we can modify it to have the correct game folder inside.
        if not path.exists(path.join(gamePath, "srctools.vdf")):
            with request.urlopen(vdfUrl) as data:
                with open(path.join(gamePath, "srctools.vdf"), "wb") as file:
                    file.write(data.read())
            
        with open(path.join(gamePath, "srctools.vdf")) as file:
            data = list(file)
        
        # Replace the gameinfo entry to match the game that we are installing
        for number, line in reversed(list(enumerate(data))):
            strip_line = clean_line(line)

            if f"\"gameinfo\" \"{inGameFolder}/\"" in strip_line:
                # We found it already in there, skip
                break
            
            elif "\"gameinfo\"" in strip_line:
                # It isn't there, remove it and add a new one to match the game
                data.pop(number)
                data.insert(number, f"{get_indent(line)}\"gameinfo\" \"{inGameFolder}/\"")

                with open(path.join(gamePath, "srctools.vdf"), "w") as file:
                    for line in data:
                        file.write(line)
                
                break
    
    except Exception as error:
        msglogger(f"An error ocurred while downloading the files ({error})", "error")
        closeScript()
    
    msglogger("Downloaded all files!", "good")
















def main():
    global inGameFolder, selectedGame, commonPath

    runsys("")  # This is required to be able to display VT100 sequences on Windows 10
    parseArgs()
    print(f"\n\x1b[4mTeamSpen's Hammer Addons Installer - {VERSION}\x1b[24m\n")

    try:
        steamlibs = getSteamPath()

        selectedGame, steamPath = selectGame(steamlibs)
        commonPath = path.join(steamPath, "steamapps/common")
        inGameFolder = AVAILABLE_GAMES.get(selectedGame)[0]

        # True is enabled
        if args.skipCmdSeq: parseCmdSeq()
        if args.skipGameinfo: parseGameInfo()
        if args.skipDownload: downloadAddons()

    except KeyboardInterrupt:
        msglogger("Installation interrupted", "error")
        closeScript()
    
    msglogger(f"Finished installing HammerAddons for '{selectedGame}'!", "good")
    closeScript()



if __name__ == "__main__":
    main()