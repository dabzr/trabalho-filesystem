
def list_directories(input):
    pass
def change_directory(input):
    pass
def remove_directory(input):
    pass
def remove_archive(input):
    pass
def make_archive(input):
    pass
def make_directory(input):
    pass
def cat(input):
    pass
def exit_(input):
    exit()

commands = {
    "ls": list_directories,
    "cd": change_directory,
    "rmdir": remove_directory,
    "rm": remove_archive,
    "touch": make_archive,
    "mkdir": make_directory,
    "exit": exit_,
    "cat": cat,
}

def shell():
    while(True):
        user_input = input("> ").split()
        func = commands.get(user_input[0])
        if func is None:
            print(f"Command not found: {user_input[0]}")
            continue
        func(user_input[1:])

def parse_path():
    pass
