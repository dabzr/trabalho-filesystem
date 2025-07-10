datablocks = []
last_index = -1

class File:
    def __init__(self, name, content) -> None:
        self.name = name
        datablob = content.encode('utf-8')
        self.inode = INode(name, len(datablob), datablob) 

class INode:
    def __init__(self, name, size, data):
        datablocks.append(data)
        self.name = name
        self.size = size
        global last_index
        last_index += 1
        self.index = last_index
    def get_data(self):
        global datablocks
        return datablocks[self.index]
    def update_data(self, data):
        global datablocks
        datablocks[self.index] = data
