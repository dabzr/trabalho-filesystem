datablocks = []
last_index = -1

class INode:
    def __init__(self, name, size, data):
        datablocks.append(data)
        self.name = name
        self.size = size
        global last_index
        last_index += 1
        self.index = last_index
        pass
