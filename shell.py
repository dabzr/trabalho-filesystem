from directory import Directory
root = Directory("/")
class Shell:
    def __init__(self) -> None:
        self.current_dir: Directory = root
        self.commands = {
            "ls": self.list_directories,
            "cd": self.change_directory,
            "rmdir": self.remove_directory,
            "rm": self.remove_archive,
            "mkfile": self.make_file,
            "mkdir": self.make_directory,
            "exit": self.exit_,
            "cat": self.cat,
        }
    def start(self):
        while(True):
            user_input = input("> ").split()
            func = self.commands.get(user_input[0])
            if func is None:
                print(f"Command not found: {user_input[0]}")
                continue
            func(user_input[1:])
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
            if part == "." or part == "":
                continue
            elif part == "..":
                if dir.parent is not None:
                    dir = dir.parent
            elif part in dir.entries and isinstance(dir.entries[part], Directory):
                dir = dir.entries[part]
            else:
                print(f"Directory '{part}' not found.")
                return None
        return dir

    def list_directories(self, input):
        if not input:
            dir = self.current_dir
        else:
            dir = self.get_dir(input[0])
        if dir is None:
            return
        for entry in dir.entries:
            print(entry.name)

    def change_directory(self, input):
        pass
    def remove_directory(self, input):
        pass
    def remove_archive(self, input):
        pass
    def make_file(self, input):
        pass
    def make_directory(self, input):
        pass
    def cat(self, input):
        pass
    def exit_(self, input):
        exit()

