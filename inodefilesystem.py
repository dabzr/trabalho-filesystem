from directory import Directory
from inode import INode


class INodeFileSystem:
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
            if part in (".", ""):
                continue

            if part == "..":
                if dir.parent is not None:
                    dir = dir.parent
                continue

            entries = dir.get_entries()

            if part not in entries:
                # print(f"Directory '{part}' not found.")
                return None

            inode_idx = entries[part]
            inode = self.inodes[inode_idx]

            if inode.file_type != "directory":
                # print(f"Path error: '{part}' is not a directory")
                return None

            dir = Directory(name=part, parent=dir, inode_idx=inode_idx, fs=self)

        return dir

    def change_directory(self, args):
        if not args:
            self.current_dir = self.root
            return
        self.current_dir = self.get_dir(args[0]) or self.current_dir

    def make_directory(self, path):
        if not path:
            print("mkdir: missing operand")
            return

        name = path[0]

        if "/" not in name:
            dir = self.current_dir
            dirname = name
        else:
            p = name.rpartition("/")
            dir = self.get_dir(p[0])
            if dir is None:
                return
            dirname = p[-1]

        entries = dir.get_entries()
        if dirname in entries:
            print(f"mkdir: '{dirname}' already exists")
            return

        new_dir = Directory(self, dirname, parent=dir)
        entries[dirname] = new_dir.inode_idx
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
            self.inodes[inode_idx].free_chain()
            dir.parent.update_entries(entries)

    def make_file(self, path):
        if len(path) < 2:
            print("mkfile: Not enough arguments")
            return

        name, content = path[0], " ".join(path[1:])

        if "/" not in name:
            dir = self.current_dir
            fname = name
        else:
            p = name.rpartition("/")
            dir = self.get_dir(p[0])
            if dir is None:
                return
            fname = p[-1]

        entries = dir.get_entries()
        if fname in entries:
            print(f"mkfile: '{fname}' already exists")
            return

        inode_idx = self.alloc_inode()
        inode = self.inodes[inode_idx]
        inode.file_type = "file"
        inode.update_data(self, content.encode("utf-8"))
        entries[fname] = inode_idx
        dir.update_entries(entries)

    def remove_file(self, path):
        if not path:
            print("rm: Not enough arguments")
            return

        name = path[0]

        if "/" not in name:
            dir = self.current_dir
            fname = name
        else:
            p = name.rpartition("/")
            dir = self.get_dir(p[0])
            if dir is None:
                return
            fname = p[-1]

        entries = dir.get_entries()
        if fname in entries:
            inode_idx = entries.pop(fname)
            self.free_inodes.add(inode_idx)
            self.inodes[inode_idx].reset()
            self.inodes[inode_idx].free_chain()
            dir.update_entries(entries)

    def move(self, args):
        if len(args) < 2:
            print("mv: Not enough arguments")
            return

        src, dst = args

        # pega o path do source e dps o inode
        p_src = src.rpartition("/")
        src_dir = self.get_dir(p_src[0]) if p_src[0] else self.current_dir
        if src_dir is None:
            print(f"mv: source directory '{p_src[0]}' not found")
            return
        src_name = p_src[-1]

        src_entries = src_dir.get_entries()
        if src_name not in src_entries:
            print(f"mv: source '{src_name}' not found")
            return

        inode_idx = src_entries[src_name]

        # pega o path do dst, dst_candidate pode ser um arquivo, ou um path
        dst_dir_candidate = self.get_dir(dst)
        if dst_dir_candidate is not None:
            dst_dir = dst_dir_candidate
            dst_name = src_name
        else:
            dst = dst.rstrip("/")
            p_dst = dst.rpartition("/")
            dst_dir = self.get_dir(p_dst[0]) if p_dst[0] else self.current_dir
            if dst_dir is None:
                print(f"mv: destination directory '{p_dst[0]}' not found")
                return
            dst_name = p_dst[-1] or src_name

        dst_entries = dst_dir.get_entries()
        if dst_name in dst_entries:
            print(f"mv: destination '{dst_name}' already exists")
            return

        # mantem o tal do inode
        del src_entries[src_name]
        src_dir.update_entries(src_entries)

        dst_entries[dst_name] = inode_idx
        dst_dir.update_entries(dst_entries)

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

    def list_directory(self, path=None):
        dir = self.current_dir if not path else self.get_dir(path[0])

        if dir is None:
            return

        entries = dir.get_entries()
        string = ""
        for name in sorted(entries.keys()):
            inode_idx = entries[name]
            inode = self.inodes[inode_idx]
            if inode.file_type == "file":
                string += f"\033[32m{name}\033[0m "
            if inode.file_type == "directory":
                string += f"\033[34m{name}\033[0m "
        if string:
            print(string)
