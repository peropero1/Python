# hash-map array version.
import numpy as np
import spookyhash
import mmh3
import os
import pandas as pd
import time
import operator
import hyperloglog
import sys

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
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)
    def __repr__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)




# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    # print("In UpdateSk()")
    e_max=get_emax()
    width,depth=get_width_depth()
    numerator,denominator=get_fraction()
    col,row=position(element)
        # col / row index of element 
    avg=0
        # ID in Sketch is hash value
    #print("{} send to Sk[{}][{}]".format(element,row,col))
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    if col<width:
        # e in Sketch
        Sk[row][col]+=1
    else:
        # e in Other
        count_sum=sum(i for i in Sk[row])
        avg=(Sk_head[row].count-count_sum)//(width*((numerator/denominator)-1))
    Update_local_max(Sk_head[row],Sk[row],element,col)
    Update_emax(Sk_head,Sk)

    
    # now we have:
    # ID: h2(h1(e)), hash value of e
    # row: h1(e), row index of e
    # index: column index of e
    # Sk_head[row].count: total count of Sk[row]
    # Sk_head[row].maxID: local max count element of Sk[row]
    # Sk_head[row].distinct: estimated element of Other part in Sk[row]
    # count_sum: sum of count in Sketch[row]
    # avg: average count of Other part in Sk[row]

    '''
    print("e_max:{}".format(e_max))
    for i in range(len(Sk)):
        print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
    print('')
    '''

# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,column):
    # pass single row
    numerator,denominator=get_fraction()
    width,depth=get_width_depth()
    if head_item.maxID=='':
        head_item.maxID=element.ID
    else:
        local_max_col=(mmh3.hash(head_item.maxID,signed=False))% ((width*numerator)//denominator)
        if local_max_col<width:
            # local max in Sketch
            if column<width:
                # e in Sketch
                if element_list[column]>element_list[local_max_col]:
                       head_item.maxID=element.ID
            else:
                # e in Other
                count_sum=sum(i for i in element_list)
                avg=(head_item.count-count_sum)//(width*((numerator/denominator)-1))
                if avg>element_list[local_max_col]:
                     head_item.maxID=element.ID
        else:
            # local max in Other
            count_sum=sum(i for i in element_list)
            avg=(head_item.count-count_sum)//(width*((numerator/denominator)-1))  
            if column<width:
                if column<width:
                    if element_list[column]>avg:
                           head_item.maxID=element.ID
                else:
                    pass

# ==========================update e_max==========================
def Update_emax(head,sketch):
    # pass whole array
    e_max=get_emax()
    numerator,denominator=get_fraction()
    width,depth=get_width_depth()
    for i in range(len(head)):
        if head[i].maxID=='':
            continue
        else:
            local_max_col,local_max_row=position(Tail(head[i].maxID,0))
            if local_max_col<width:
                if sketch[local_max_row][local_max_col]>e_max.count:
                    e_max.ID=head[i].maxID
                    e_max.count=sketch[local_max_row][local_max_col]
            else:
                # local max in Other
                count_sum=sum(j for j in sketch[i])
                avg=(head[i].count-count_sum)//(width*((numerator/denominator)-1))
                if avg>e_max.count:
                    e_max.ID=head[i].maxID
                    e_max.count=avg
# ==========================Tools=========================    
def get_emax():
    return e_max
def get_width_depth():
    return width,depth

def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index

def position(element):
    numerator,denominator=get_fraction()
    width,depth=get_width_depth()
    hash1=spookyhash.hash32(bytes(str(element.ID),encoding='utf-8'))
        # input of spooky: byte
        # output of spooky:unsigned- 32 bit int
    hash2=mmh3.hash(element.ID, signed=False)
        # input of mmh: str
        # output: unsigned- 32 bit int
    col=hash2 % ((width*numerator)//denominator)
    row=hash1 % depth
    return col,row
def get_fraction():
    return numerator,denominator    
    
# ==========================main=========================    

filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
depth=4
width=128
size=1024
numerator=12
denominator=10

start=time.time()
Sk_head=[Head(0) for j in range(depth)]

Sketch=np.zeros((depth,width),dtype='int')

e_max=Tail('',0)

item_count=100
income=0
with open(src_data,'r') as file:
    while True:
        e=file.readline().strip('\n')
        if not e:
            break
        else:
            #item_count-=1
            # income+=1
            # print("read {}-th element:".format(income))
            item=Tail(e,1)
            UpdateSk(item,Sk_head,Sketch)
end=time.time()
print("Execution time:{} seconds.".format(str(end-start)))
print("e_max:{}".format(e_max))
for i in range(len(Sketch)):
    print("Sk[{}]:{},{}".format(i,Sk_head[i],Sketch[i]))
print('') 