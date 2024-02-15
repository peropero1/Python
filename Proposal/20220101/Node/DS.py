
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
        #super().__init__(count)
        self.maxID=''
        self.keep=super().__init__(count)
    def __str__(self):
        return '[LHH: {}, keep:{}]'.format(self.maxID,self.keep)
    def __repr__(self):
        return '[LHH: {}, keep:{}]'.format(self.maxID,self.keep)    
    
'''

class Head(Node):
    def __init__(self,count=1):
        super().__init__(count)
        #self.remove=hyperloglog.HyperLogLog(0.05)
        self.distinct = hyperloglog.HyperLogLog(0.05)
        self.maxID=''
        self.keep=0
    def __str__(self):
        return '[total count: {}, distinct: {}, max: {}, keep: {}]'.format(self.count,len(self.distinct),self.maxID,self.keep)
    def __repr__(self):
        return '[total count: {}, distinct: {}, max: {}, keep: {}]'.format(self.count,len(self.distinct),self.maxID,self.keep)
'''

class Tail(Node):
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)
    def __repr__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)

class ssNode(Node):
    def __init__(self,ID,count,error=0):
        self.ID = ID
        super().__init__(count)    
        self.error=error
    def __str__(self):
        return '[ID: {}, count: {},error: {}]'.format(self.ID,self.count,self.error)
    def __repr__(self):
        return '[ID: {}, count: {},error: {}]'.format(self.ID,self.count,self.error)      
    
class esNode(Tail):
    def __init__(self,ID,vote_pos=1,flag=False,vote_neg=0):
        self.ID = str(ID)
        self.vote_pos=vote_pos
        self.flag=flag
        self.vote_neg=vote_neg
        #super().__init__(count)
    def __str__(self):
        return '[{},{},{},{}]'.format(self.ID,self.vote_pos,self.flag,self.vote_neg)
    def __repr__(self):
        return '[{},{},{},{}]'.format(self.ID,self.vote_pos,self.flag,self.vote_neg) 