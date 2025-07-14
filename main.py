from shell import Shell
from inodefilesystem import INodeFileSystem
from chainfilesystem import ChainFileSystem
from sys import argv

types = {
    'i': {
        "name": "I-node",
        "cls": INodeFileSystem
    },
    'l': {
        "name": "Linked list",
        "cls": ChainFileSystem
    }
}

types_message = "Types:\n'i': i-node\n'l': linked list"

if __name__ == "__main__":
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <type>\n{types_message}")
        exit(1)
    type_selected_arg = argv[1]
    if type_selected_arg not in types:
        print(f"Type '{type_selected_arg}' not exist\n{types_message}") 
        exit(2)
    type_selected = types[type_selected_arg]
    print(f"{type_selected["name"]} selected!")
    fs = type_selected["cls"](1024, 512)
    shell = Shell(fs)
    shell.start()
