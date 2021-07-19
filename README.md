<div align="center">
	<img src="https://raw.githubusercontent.com/TeamSpen210/HammerAddons/master/logo/icon_256.png" alt="Hammer Addons" height="200">
	<h1> TeamSpen's Hammer Addons Installer </h1>
</div>

## Features
Automatic installer for [TeamSpen's Hammer Addons](https://github.com/TeamSpen210/HammerAddons), featuring:
* Find the user's Steam path location.
* Game selector which displays what games the user has installed, and compatible with the addons.
* Download the latest files from TeamSpen's repository.
* Add the compile commands for the Hammer compile steps.
* Add the required folder in "gameinfo.txt".
* Modify "srctools.vdf" with the correct game.

<br>

![HAInstaller](https://user-images.githubusercontent.com/48654552/126181869-163ab1bf-1774-475a-bafe-199380f38926.gif)

```
usage: HAInstaller.py [-h] [-a ARGS] [-g GAME] [-v VERSION] [--skipCmdSeq] [--skipGameinfo] [--skipDownload] [--ignoreHammer]
                      [--chkup]

optional arguments:
  -h, --help            show this help message and exit
  -a ARGS, --args ARGS  Arguments for a hammer compile step. Default are '--propcombine $path\$file'
  -g GAME, --game GAME  The name of the game folder in which the addons will be installed.
  -v VERSION, --version VERSION
                        Select the version of HammerAddons to install. Please keep in mind that all versions
                        might not be compatible with all the games. Default value is 'latest'.
  --skipCmdSeq          Do not modify the CmdSeq.wc file.
  --skipGameinfo        Do not modify the gameinfo.txt file.
  --skipDownload        Do not download any files.
  --ignoreHammer        Do not check if Hammer is running.
  --chkup               Check for new versions of the installer.

Using version 1.5

Repositories:
    HAInstaller:    https://github.com/DarviL82/HAInstaller
    HammerAddons:   https://github.com/TeamSpen210/HammerAddons
```

<hr>

## Download
There is a standalone executable available at the [releases page](https://github.com/DarviL82/HAInstaller/releases/latest). Or you can [download the script directly](https://github.com/DarviL82/HAInstaller/blob/main/HAInstaller.py) (It requires at least Python 3.9, and the [srctools](https://github.com/TeamSpen210/srctools) package)
> **Note:** The binary will most likely be detected as a virus. But it obviusly isn't (I swear).

## Special Thanks
* TeamSpen for creating the addons and srctools.
