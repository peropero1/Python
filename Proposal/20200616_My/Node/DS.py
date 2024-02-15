import hyperloglog


# ==========================data structure==========================
class Node():
    def __init__(self,count=0):
        self.count=count
    def add_count(self,count=1):
        self.count+=count
    def __str__(self):
        return 'count: {}'.format(self.count)
    def __repr__(self):
        return ''

class Head(Node):
    def __init__(self,count=1):
        super().__init__(count)
        self.distinct = hyperloglog.HyperLogLog(0.01)
        self.maxID=''
        self.keep=0
        #self.bringback=0
    def __str__(self):
        return '[total count: {}, distinct: {}, max: {}, keep: {}]'.format(self.count,len(self.distinct),self.maxID,self.keep)
    def __repr__(self):
        return '[total count: {}, distinct: {}, max: {}, keep: {}]'.format(self.count,len(self.distinct),self.maxID,self.keep)


class Tail(Node):
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)
    def __repr__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)