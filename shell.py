import os
from directory import Directory
from inode import File
from functools import reduce

root = Directory("/")


class Shell:
    def __init__(self) -> None:
        self.current_dir: Directory = root
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
            func = self.commands.get(user_input[0])
            if func is None:
                print(f"Command not found: {user_input[0]}")
                continue

            func(list(map(lambda x: str(x), user_input[1:])))

    def get_dir(self, path: str):
        if path == "/":
            return root
        if path.startswith("/"):
            dir = root
            parts = path.strip("/").split("/")
        else:
            dir = self.current_dir
            parts = path.strip().split("/")
        for part in parts:
            entries = dir.inode.get_data()
            if part == "." or part == "":
                continue
            elif part == "..":
                if dir.parent is not None:
                    dir = dir.parent
            elif part in entries and isinstance(entries[part], Directory):
                dir = entries[part]
            else:
                print(f"Directory '{part}' not found.")
                return None
        return dir

    def change_directory(self, input):
        if not input:
            self.current_dir = root
            return
        self.current_dir = self.get_dir(input[0]) or self.current_dir

    def remove_directory(self, input):
        dir = self.get_dir(input[0])
        if dir is None:
            return
        if dir.parent is None:
            return
        entries = dir.parent.inode.get_data()
        entries.pop(dir.name)
        dir.parent.inode.update_data(entries)

    def remove_file(self, input):
        if not input:
            print("rm: Not enough arguments")
            return
        if "/" not in input[0]:
            entries = self.current_dir.inode.get_data()
            entries.pop(input[0])
        pass
        #WORK IN PROGRESS

    def make_file(self, input):
        if len(input) < 2:
            print("mkfile: Not enough arguments")
            return
        name, content = input[0], reduce(lambda x, y: x + " " + y, input[1:])
        if "/" not in name:
            entries = self.current_dir.inode.get_data()
            entries[name] = File(name, content)
        p = name.rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.inode.get_data()
        entries[p[-1]] = File(p[-1], content)
        dir.inode.update_data(entries)

    def make_directory(self, input):
        if not input:
            print("mkdir: missing operand")
            return
        if "/" not in input[0]:
            entries = self.current_dir.inode.get_data()
            entries[input[0]] = Directory(input[0], parent=self.current_dir)
            self.current_dir.inode.update_data(entries)
            return
        p = input[0].rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        p2 = p[0].rpartition("/")
        entries = dir.inode.get_data()
        entries[p[-1]] = Directory(p[-1], parent=p2[-1])
        dir.inode.update_data(entries)

    def cat(self, input):
        p = input[0].rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.inode.get_data()
        if not entries.get(p[-1]) or not isinstance(entries[p[-1]], File):
            print(f"cat: {p[-1]} is not a valid file")
            return
        print(entries[p[-1]].inode.get_data().decode("utf-8"))

    def exit_(self, input):
        exit()

    def clear(self, input):
        os.system("clear")
    
    def list_directories(self, input):
        if not input:
            dir = self.current_dir
        else:
            dir = self.get_dir(input[0])
        if dir is None:
            return
        string = ""
        for name, f in sorted(dir.inode.get_data().items()):
            if isinstance(f, Directory):
                string += f'\033[34m{name}\033[0m'
                continue
            string += f"\033[32m{name}\033[0m "
        if string:
            print(string)
