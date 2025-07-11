import os
from directory import Directory
from filesystem import FileSystem

class Shell:
    def __init__(self, fs: FileSystem) -> None:
        self.fs = fs
        self.current_dir: Directory = self.fs.root
        self.commands = {
            "ls": self.list_directories,
            "cd": self.change_directory,
            "rmdir": self.remove_directory,
            "rm": self.remove_file,
            "mkfile": self.make_file,
            "mkdir": self.make_directory,
            "exit": self.exit_,
            "cat": self.cat,
            "clear": self.clear,
        }

    def start(self):
        while True:
            user_input = input(f"{self.current_dir.get_path()} > ").strip().split()
            if not user_input:
                continue
            func = self.commands.get(user_input[0])
            if func is None:
                print(f"Command not found: {user_input[0]}")
                continue
            func(user_input[1:])

    def change_directory(self, path):
        self.current_dir = self.fs.change_directory(self.current_dir, path)

    def remove_directory(self, path):
        self.fs.remove_directory(self.current_dir, path)

    def remove_file(self, path):
        self.fs.remove_file(self.current_dir, path)

    def make_file(self, path):
        self.fs.make_file(self.current_dir, path)

    def make_directory(self, path):
        self.fs.make_directory(self.current_dir, path)

    def cat(self, path):
        self.fs.cat(self.current_dir, path)

    def list_directories(self, path):
        self.fs.list_directory(self.current_dir, path)

    def exit_(self, _):
        exit()

    def clear(self, _):
        os.system("clear")
