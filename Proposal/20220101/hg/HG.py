import Config
import Func
import numpy as np

class Node():
    def __init__(self,ID='Null',count=0):
        self.count=count
        self.ID=str(ID)
    def __str__(self):
        return '({},{})'.format(self.ID,self.count)
    def __repr__(self):
        return '({},{})'.format(self.ID,self.count)

class HeavyGuardian():
    def __init__(self):
        self.heavy_part=[]
        #self.light_part=[0]*Config.light
        self.light_part=np.zeros(Config.light,dtype='int32')
        #    HG_list=[HeavyGuardian(Config.light) for _ in range(Config.size)]
    def __str__(self):
        return '[H:{}L:{}]\n'.format(self.heavy_part,self.light_part)
    def __repr__(self):
        return '[H:{}L:{}]\n'.format(self.heavy_part,self.light_part)
    


    

        