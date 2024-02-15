import numpy as np
import spookyhash
import mmh3
import os
import pandas as pd
import time
import operator
import sys
import re
from probables import (CountMinSketch)

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
    def __str__(self):
        return '[total count: {}, distinct: {}, max: {}]'.format(self.count,len(self.distinct),self.maxID)
    def __repr__(self):
        return '[total count: {}, distinct: {}, max: {}]'.format(self.count,len(self.distinct),self.maxID)

class Tail(Node):
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
    
# ==========================Tools=========================    
def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index
    
def position(element,size):
    hash1=spookyhash.hash32(bytes(element,encoding='utf-8'))% size
        # input: byte
        # output:unsigned- 32 bit int
    '''
    hash2=mmh3.hash(str(element.ID), signed=False)
    # input: str
    # output: unsigned- 32 bit int
    
    '''
    return hash1

def Query(e):
    index=position(e,size)
    count=0
    if Top[index].ID==e:
        if Top[index].flag==False:
            count=Top[index].vote_pos
        else:
            count=Top[index].vote_pos+cms.check(e)
    else:
        count=cms.check(e)
    return count
    
# ==========================main=========================   

filename='kosarak.dat'
filepath=r"..\dataset\kosarak"

src_data=os.path.join(filepath,filename)
d=8
w=512
size=512
cms = CountMinSketch(width=w, depth=d)
Top=[None]*size
threshold=4

item_count=100
income=0

start=time.time()
with open(src_data,'r') as file:
    while True:
        e=file.readline().strip('\n')
        if not e:
            print('EOF')
            break
        else:
            #item_count-=1
            #income+=1
            index=position(e,size)
            print("\nread {}-th element:{}".format(income,e))
            if Top[index]==None:
                Top[index]=Tail(e)
            else:
                if Top[index].ID ==e:
                    print("Hit in Top[{}]".format(index))
                    Top[index].vote_pos+=1
                elif Top[index].ID !=e:
                    print("Collision at Top[{}]".format(index))
                    Top[index].vote_neg+=1
                    vote_threshold=Top[index].vote_neg/Top[index].vote_pos
                    if vote_threshold<threshold:
                        print("vote_threshold={}".format(vote_threshold))
                        cms.add(e)
                    else:
                        print("vote_threshold>{}".format(threshold))
                        cms.add(e,Top[index].vote_pos)
                        Top[index]=Tail(e,1,True,1)
            print(Top)
end=time.time()
print("Top-{},Sketch:{}*{}".format(size,d,w))
print("Execution time:{:8.3f} seconds.".format(end-start))
print("Total memory {} bytes= ".format(sys.getsizeof(Top)+sys.getsizeof(cms._bins)),end='')
print("Top:{} bytes, Sketch:{} bytes.".format(sys.getsizeof(Top),sys.getsizeof(cms._bins)))

#====================Top to csv=============================
templi=[[i.ID,Query(i.ID)] for i in Top]
df=pd.DataFrame(templi,columns=['ID', 'Count'])
name="Ela_kosarak_Top-"+str(size)+'_'+str(d)+'_'+str(w)+'.csv'
df.to_csv(os.path.join(r'..\result',name),index=False)
    #儲存Top的結果

#====================result compare=============================
gr_path=r"..\dataset\kosarak"
gr_file_name='kosarak_ground_truth.csv'
grtruth=pd.read_csv(os.path.join(gr_path,gr_file_name))
Ela_result=pd.read_csv(os.path.join(r'..\result',name))

# precision
gt_set=set(grtruth['Element'][:size])
    # Top-k ID of ground truth
my_set=set(Ela_result['ID'])
precision=len(gt_set & my_set)/len(my_set)
    # &: set 交集運算
print("Precision: {:8.4f}".format(precision))
