from directory import Directory
from inode import INode  # File


class FileSystem:
    def __init__(self, num_blocks, block_size):
        self.NUM_BLOCKS = num_blocks
        self.BLOCK_SIZE = block_size
        self.NUM_INODES = num_blocks // INode.MAX_BLOCKS

        self.blocks = [bytearray(block_size) for _ in range(num_blocks)]
        self.free_blocks = set(range(num_blocks))

        self.inodes = [INode() for _ in range(self.NUM_INODES)]
        self.free_inodes = set(range(self.NUM_INODES))

        self.root = Directory(self, "/")

        self.current_dir = self.root

    def alloc_block(self):
        if not self.free_blocks:
            raise RuntimeError("No free blocks available")
        return self.free_blocks.pop()


    def alloc_inode(self):
        if not self.free_inodes:
            raise RuntimeError("No free inodes available")
        idx = self.free_inodes.pop()
        self.inodes[idx].reset()
        return idx


    def get_dir(self, path: str):
        if path == "/":
            return self.root
        if path.startswith("/"):
            dir = self.root
            parts = path.strip("/").split("/")
        else:
            dir = self.current_dir
            parts = path.strip().split("/")

        for part in parts:
            if part == "." or part == "":
                continue

            if part == "..":
                if dir.parent is not None:
                    dir = dir.parent
                continue

            entries = dir.get_entries()

            if part not in entries:
                print(f"Directory '{part}' not found.")
                return None

            inode_idx = entries[part]
            dir = Directory(name=part, parent=dir, inode_idx=inode_idx, fs=self)

        return dir


    def change_directory(self, path):
        if not path:
            return self.root
        self.current_dir = self.get_dir(path[0]) or self.current_dir


    def make_directory(self, path):
        if not path:
            print("mkdir: missing operand")
            return
        if "/" not in path[0]:
            entries = self.current_dir.get_entries()
            if path[0] in entries:
                print(f"mkdir: '{path[0]}' already exists")
                return
            new_dir = Directory(self, path[0], parent=self.current_dir)
            entries[path[0]] = new_dir.inode_idx
            self.current_dir.update_entries(entries)
            return

        p = path[0].rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.get_entries()
        if p[-1] in entries:
            print(f"mkdir: '{p[-1]}' already exists")
            return
        new_dir = Directory(self, p[-1], parent=dir)
        entries[p[-1]] = new_dir.inode_idx
        dir.update_entries(entries)


    def remove_directory(self, path):
        dir = self.get_dir(path[0])
        if dir is None or dir.parent is None:
            return
        entries = dir.parent.get_entries()
        if dir.name in entries:
            inode_idx = entries.pop(dir.name)
            self.free_inodes.add(inode_idx)
            self.inodes[inode_idx].reset()
            dir.parent.update_entries(entries)


    def make_file(self, path):
        if len(path) < 2:
            print("mkfile: Not enough arguments")
            return
        name, content = path[0], " ".join(path[1:])

        if "/" not in name:
            entries = self.current_dir.get_entries()
            if name in entries:
                print(f"mkfile: '{name}' already exists")
                return
            inode_idx = self.alloc_inode()
            inode = self.inodes[inode_idx]
            inode.write_bytes(self, content.encode("utf-8"))
            entries[name] = inode_idx
            self.current_dir.update_entries(entries)
            return

        p = name.rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.get_entries()
        if p[-1] in entries:
            print(f"mkfile: '{p[-1]}' already exists")
            return
        inode_idx = self.alloc_inode()
        inode = self.inodes[inode_idx]
        inode.write_bytes(self, content.encode("utf-8"))
        entries[p[-1]] = inode_idx
        dir.update_entries(entries)


    def remove_file(self, path):
        if not path:
            print("rm: Not enough arguments")
            return

        if "/" not in path[0]:
            entries = self.current_dir.get_entries()
            if path[0] in entries:
                inode_idx = entries.pop(path[0])
                self.free_inodes.add(inode_idx)
                self.inodes[inode_idx].reset()
                self.current_dir.update_entries(entries)
            return

        p = path[0].rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.get_entries()
        if p[-1] in entries:
            inode_idx = entries.pop(p[-1])
            self.free_inodes.add(inode_idx)
            self.inodes[inode_idx].reset()
            dir.update_entries(entries)


    def cat(self, path):
        p = path[0].rpartition("/")
        dir = self.get_dir(p[0])
        if dir is None:
            return
        entries = dir.get_entries()
        if p[-1] not in entries:
            print(f"cat: '{p[-1]}' not found")
            return
        inode_idx = entries[p[-1]]
        data = self.inodes[inode_idx].get_data(self)
        print(data.decode("utf-8"))

    # Mudar quando tiver tipo
    def list_directory(self, path=None):
        dir = self.current_dir if not path else self.get_dir(path[0])

        if dir is None:
            return

        entries = dir.get_entries()
        string = ""
        for name in sorted(entries.keys()):
            inode_idx = entries[name]
            inode = self.inodes[inode_idx]
            if len(inode.blocks) > 0:
                # Para simplificar: se tiver blocos, assuma que é file
                string += f"\033[32m{name}\033[0m "
            else:
                string += f"\033[34m{name}\033[0m "
        if string:
            print(string)
