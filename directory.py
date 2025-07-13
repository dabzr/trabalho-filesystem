# Diretório salva as entradas no próprio inode e depois lé, coisa engraçada
class Directory:
    def __init__(self, fs, name, parent=None, inode_idx=None) -> None:
        self.name = name
        self.parent = parent
        self.fs = fs
        self.entries = {}

        if inode_idx is not None:
            self.inode_idx = inode_idx
            self._get_entries()
            return

        self.inode_idx = fs.alloc_inode()
        inode = fs.inodes[self.inode_idx]
        inode.used = True
        inode.file_type = "directory"
        inode.write_bytes(fs, b"")

    def _get_entries(self):
        inode = self.fs.inodes[self.inode_idx]
        raw = inode.get_data(self.fs)
        lines = raw.decode('utf-8').splitlines()
        for line in lines:
            if not line.strip():
                continue
            name, idx = line.split(":")
            self.entries[name] = int(idx)

    def get_entries(self):
        return self.entries

    def update_entries(self, entries: dict):
        self.entries = entries
        lines = [f"{name}:{idx}" for name, idx in entries.items()]
        raw = "\n".join(lines).encode('utf-8')
        inode = self.fs.inodes[self.inode_idx]
        inode.update_data(self.fs, raw)

    def get_path(self):
        if self.parent is None:
            return "/"
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))
