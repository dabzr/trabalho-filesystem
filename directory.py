from inode import INode
class Directory:
    def __init__(self, name, parent=None) -> None:
        self.name = name
        self.inode = INode(name, 0, {})
        self.parent = parent

    def get_path(self):
        string = self.name
        parent = self.parent
        if not parent:
            return f"\033[31m{string}\033[0m"

        while parent.parent:
            string = parent.name + '/' + string
            parent = parent.parent
        return f"\033[31m/{string}\033[0m"
