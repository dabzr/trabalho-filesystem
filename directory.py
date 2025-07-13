# Diretório salva as entradas no próprio inode e depois lé, coisa engraçada
class Directory:
    def __init__(self):
        self.parent = None
        self.name = None
        self.fs = None

    def get_entries(self):
        raise NotImplementedError
    def update_entries(self, entries: dict):
        raise NotImplementedError
    def write_entries(self, entries: dict):
        raise NotImplementedError
    def get_path(self):
        raise NotImplementedError

class ChainDirectory(Directory):
    def __init__(self, fs, name, parent=None, first_block=None, size=0):
        self.fs = fs
        self.name = name
        self.parent = parent
        self.first_block = first_block
        self.size = size
        if self.first_block is None:
            self.write_entries({})

    def _read_entries_raw(self):
        if self.size == 0:
            return b""
        return self.fs.read_chain(self.first_block, self.size)

    def get_entries(self):
        raw = self._read_entries_raw()
        text = raw.decode("utf-8")
        entries = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            name, ftype, first, size = line.split(":")
            entries[name] = (ftype, int(first), int(size))
        return entries

    def write_entries(self, entries):
        lines = [
            f"{name}:{ftype}:{first}:{size}"
            for name, (ftype, first, size) in entries.items()
        ]
        data = "\n".join(lines).encode("utf-8")
        if self.first_block is None:
            self.first_block, self.size = self.fs.write_chain(data)
        else:
            self.first_block, self.size = self.fs.rewrite_chain(
                self.first_block, data
            )
        if self.parent:
            parent_entries = self.parent.get_entries()
            parent_entries[self.name] = ("directory", self.first_block, self.size)
            self.parent.write_entries(parent_entries)

    def update_entries(self, entries):
        self.write_entries(entries)

    def get_path(self):
        if self.parent is None:
            return "/"
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))



class INodeDirectory(Directory):
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
    
