from shell import Shell
from filesystem import FileSystem
if __name__ == "__main__":
    fs = FileSystem(1024, 512)
    shell = Shell(fs)
    shell.start()
