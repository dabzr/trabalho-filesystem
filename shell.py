def list_directories():
    pass
def change_directory():
    pass
def remove_directory():
    pass
def remove_archive():
    pass
def make_archive():
    pass
def make_directory():
    pass

commands = {
    "ls": list_directories,
    "cd": change_directory,
    "rmdir": remove_directory,
    "rm": remove_archive,
    "touch": make_archive,
    "mkdir": make_directory,
    "exit": exit
}

def shell():
    while(True):
        user_input = input("> ").split()
        func = commands.get(user_input[0])
        if func is None:
            print(f"Command not found: {user_input[0]}")
            continue
        func()

def parse():
    pass
