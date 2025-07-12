class ChainDirectory:
    def __init__(self, fs, name, parent=None, first_block=None, size=0):
        self.fs = fs
        self.name = name
        self.parent = parent
        self.first_block = first_block
        self.size = size
        if self.first_block is None:
            self.write_entries({})

    def read_entries_raw(self):
        if self.size == 0:
            return b""
        return self.fs.read_chain(self.first_block, self.size)

    def get_entries(self):
        raw = self.read_entries_raw()
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
                self.first_block, self.size, data
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


class ChainFileSystem:
    def __init__(self, num_blocks, block_size):
        self.BLOCK_SIZE = block_size
        self.blocks = [bytearray(block_size) for _ in range(num_blocks)]
        self.next_block: list[None | int] = [None] * num_blocks
        self.free_blocks = set(range(num_blocks))

        self.root = ChainDirectory(self, "/", None)
        self.current_dir = self.root

    def alloc_block(self):
        if not self.free_blocks:
            raise RuntimeError("No free blocks available")
        return self.free_blocks.pop()

    def free_chain(self, first_block):
        idx = first_block
        while idx is not None:
            nxt = self.next_block[idx]
            self.next_block[idx] = None
            self.free_blocks.add(idx)
            idx = nxt

    def write_chain(self, data: bytes):
        remaining = memoryview(data)
        first = last = None
        while remaining:
            idx = self.alloc_block()
            if first is None:
                first = idx
            if last is not None:
                self.next_block[last] = idx
            chunk = remaining[: self.BLOCK_SIZE]
            self.blocks[idx][: len(chunk)] = chunk
            remaining = remaining[len(chunk) :]
            last = idx
        if first is None:
            first = self.alloc_block()
        return first, len(data)

    def read_chain(self, first_block, size):
        buf = bytearray()
        idx = first_block
        read = 0
        while idx is not None and read < size:
            chunk_len = min(self.BLOCK_SIZE, size - read)
            buf.extend(self.blocks[idx][:chunk_len])
            read += chunk_len
            idx = self.next_block[idx]
        return bytes(buf[:size])

    def rewrite_chain(self, first_block, old_size, data: bytes):
        self.free_chain(first_block)
        return self.write_chain(data)

    def split_path(self, path: str):
        if "/" not in path:
            return "", path
        dir_path, _, base = path.rpartition("/")
        return dir_path, base

    def get_dir(self, path: str):
        if path in ("", "."):
            return self.current_dir
        if path == "/":
            return self.root
        parts = path.strip("/").split("/")
        node = self.root if path.startswith("/") else self.current_dir
        for part in parts:
            if part in ("", "."):
                continue
            if part == "..":
                node = node.parent or node
                continue
            entries = node.get_entries()
            meta = entries.get(part)
            if not meta or meta[0] != "directory":
                return None
            node = ChainDirectory(self, part, node, first_block=meta[1], size=meta[2])
        return node

    def change_directory(self, args):
        if not args:
            self.current_dir = self.root
            return
        target = self.get_dir(args[0])
        if target:
            self.current_dir = target

    def make_directory(self, args):
        if not args:
            print("mkdir: missing operand")
            return
        dir_path, name = self.split_path(args[0])
        parent = self.get_dir(dir_path)
        if not parent:
            print(f"mkdir: cannot access '{dir_path}': No such directory")
            return
        entries = parent.get_entries()
        if name in entries:
            print(f"mkdir: '{name}' already exists")
            return
        new_dir = ChainDirectory(self, name, parent)
        entries[name] = ("directory", new_dir.first_block, new_dir.size)
        parent.update_entries(entries)

    def remove_directory(self, args):
        if not args:
            print("rmdir: missing operand")
            return
        target = self.get_dir(args[0])
        if not target or target.parent is None:
            return
        entries = target.parent.get_entries()
        del entries[target.name]
        self.free_chain(target.first_block)
        target.parent.update_entries(entries)

    def make_file(self, args):
        if len(args) < 2:
            print("mkfile: Not enough arguments")
            return
        path, content = args[0], " ".join(args[1:])
        dir_path, name = self.split_path(path)
        parent = self.get_dir(dir_path)
        if not parent:
            print(f"mkfile: cannot access '{dir_path}': No such directory")
            return
        entries = parent.get_entries()
        if name in entries:
            print(f"mkfile: '{name}' already exists")
            return
        first, size = self.write_chain(content.encode("utf-8"))
        entries[name] = ("file", first, size)
        parent.update_entries(entries)

    def remove_file(self, args):
        if not args:
            print("rm: Not enough arguments")
            return
        dir_path, name = self.split_path(args[0])
        parent = self.get_dir(dir_path)
        if not parent:
            return
        entries = parent.get_entries()
        if name in entries:
            meta = entries.pop(name)
            self.free_chain(meta[1])
            parent.update_entries(entries)

    def move(self, args):
        if len(args) < 2:
            print("mv: Not enough arguments")
            return
        src, dst = args
        s_dir, s_name = self.split_path(src)
        src_parent = self.get_dir(s_dir) or self.current_dir
        entries_src = src_parent.get_entries()
        if s_name not in entries_src:
            print(f"mv: source '{s_name}' not found")
            return
        meta = entries_src.pop(s_name)
        dst_parent = self.get_dir(dst)
        if dst_parent:
            d_name = s_name
        else:
            d_dir, d_name = self.split_path(dst.rstrip("/"))
            dst_parent = self.get_dir(d_dir)
            if not dst_parent:
                print(f"mv: destination '{d_dir}' not found")
                return
        entries_dst = dst_parent.get_entries()
        if d_name in entries_dst:
            print(f"mv: destination '{d_name}' already exists")
            return
        src_parent.update_entries(entries_src)
        entries_dst[d_name] = meta
        dst_parent.update_entries(entries_dst)

    def cat(self, args):
        if not args:
            print("cat: missing operand")
            return
        dir_path, name = self.split_path(args[0])
        parent = self.get_dir(dir_path) or self.current_dir
        entries = parent.get_entries()
        if name not in entries:
            print(f"cat: '{name}' not found")
            return
        meta = entries[name]
        data = self.read_chain(meta[1], meta[2])
        print(data.decode("utf-8"))

    def list_directory(self, args=None):
        target = self.current_dir if not args else self.get_dir(args[0])
        entries = target.get_entries() if target else {}
        out = []
        for name in sorted(entries):
            t = entries[name][0]
            color = "\033[34m" if t == "directory" else "\033[32m"
            out.append(f"{color}{name}\033[0m")
        print(" ".join(out))
