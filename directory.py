class Directory:
    def __init__(self, name, parent=None) -> None:
        self.name = name
        self.entries = {}
        self.parent = parent
