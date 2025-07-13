from shell import Shell
from inodefilesystem import INodeFileSystem
from chainfilesystem import ChainFileSystem

if __name__ == "__main__":
    fs = INodeFileSystem(1024, 512)
    # fs = ChainFileSystem(1024, 512)
    shell = Shell(fs)
    shell.start()
