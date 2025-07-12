from directory import ChainDirectory, INodeDirectory
from inode import INode

class FileAllocationMethod:
    pass
class ChainAllocation(FileAllocationMethod):

    def __init__(self, num_blocks) -> None:
        self.next_block: list[None | int] = [None] * num_blocks
        self.free_blocks = set(range(num_blocks))


    def free_chain(self, first_block):
        idx = first_block
        while idx is not None:
            nxt = self.next_block[idx]
            self.next_block[idx] = None
            self.free_blocks.add(idx)
            idx = nxt

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

    def rewrite_chain(self, first_block, data: bytes):
        self.free_chain(first_block)
        return self.write_chain(data)
    
    def make_dir(self, name, entries=None, parent=None, fs=None):
        if entries:
            meta = entries.get(name)
            return ChainDirectory(self, name, parent=parent, first_block=meta[1], size=meta[2])

    def is_directory(self, entries, part):
        meta = entries.get(part)
        return True if meta or meta[0] != "directory" else False

    def add_entry(self, entries, name, new_entry):
        entries[name] = ("directory", new_entry.first_block, new_entry.size)
        return entries

    def clean_allocation(self, entries, name):
        pass

class INodeAllocation(FileAllocationMethod):
    def __init__(self, num_blocks):
        self.NUM_INODES = num_blocks // INode.MAX_BLOCKS
        self.inodes = [INode() for _ in range(self.NUM_INODES)]
        self.free_inodes = set(range(self.NUM_INODES))

    def alloc_inode(self):
        if not self.free_inodes:
            raise RuntimeError("No free inodes available")
        idx = self.free_inodes.pop()
        self.inodes[idx].reset()
        return idx

    def is_directory(self, entries, part):
        inode_idx = entries[part]
        inode = self.inodes[inode_idx]
        return inode.file_type == "directory"

    def make_dir(self, name, entries=None, parent=None, fs=None):
        if entries:
            inode_idx = entries[name]
            return INodeDirectory(fs, name, parent, inode_idx)
        return INodeDirectory(fs, name, parent)

    def add_entry(self, entries, name, new_entry):
        entries[name] = new_entry.inode_idx
        return entries

    def clean_allocation(self, entries, name):
        inode_idx = entries.pop(name)
        self.free_inodes.add(inode_idx)
        self.inodes[inode_idx].reset()
        self.inodes[inode_idx].free_chain()
        return entries
    
    def make_file(self, entries, name, content):
        inode_idx = self.alloc_inode()
        inode = self.inodes[inode_idx]
        inode.file_type = "file"
        inode.update_data(self, content.encode("utf-8"))
        entries[name] = inode_idx
