#class File:
#    def __init__(self, name, content) -> None:
#        self.name = name
#        datablob = content.encode('utf-8')
#        self.inode = INode(name, len(datablob), datablob) 

class INode:
    MAX_BLOCKS = 8
    def __init__(self):
        self.reset()

    def reset(self):
        self.used = False
        self.name = ""
        self.size = 0
        self.file_type = ""
        self.blocks = []
        self.next_inode = None

    def get_data(self, fs):
        data = bytearray()
        inode = self
        while inode:
            for blk_idx in inode.blocks:
                data.extend(fs.blocks[blk_idx])
            inode = fs.inodes[inode.next_inode] if inode.next_inode is not None else None
        return bytes(data[: self.size])

    # Do jeito que tá agora ele apaga e reescreve. O que não sei se é massa
    # Solta todo o rabo e escreve
    def update_data(self, fs, data):
        self.free_chain(fs)
        self.write_bytes(fs, data)

    def free_chain(self, fs):
        inode = self
        while inode:
            for blk_idx in inode.blocks:
                fs.free_blocks.add(blk_idx)
            inode.blocks.clear()
            inode.size = 0
            nxt = inode.next_inode
            if nxt is not None:
                fs.free_inodes.add(nxt)
                fs.inodes[nxt].reset()
            inode.next_inode = None
            inode = fs.inodes[nxt] if nxt is not None else None

    def write_bytes(self, fs, data: bytes):
        remaining = memoryview(data)
        inode = self
        while remaining:
            while len(inode.blocks) < INode.MAX_BLOCKS and remaining:
                blk_idx = fs.alloc_block()
                chunk = remaining[:fs.BLOCK_SIZE]
                fs.blocks[blk_idx][:len(chunk)] = chunk
                inode.blocks.append(blk_idx)
                remaining = remaining[len(chunk):]
            if remaining:
                nxt = fs.alloc_inode()
                inode.next_inode = nxt
                inode = fs.inodes[nxt]

        self.size = len(data)
        self.used = True
