pyinstaller -F HAInstaller.py --distpath . --workpath .\buildshit --clean -i .\resources\icon.ico
rmdir /s /q buildshit __pycache__
del *.spec