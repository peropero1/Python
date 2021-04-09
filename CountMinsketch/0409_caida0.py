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
    e_max=get_emax()
    width,depth=get_width_depth()
    col,row=position(element)
        # col / row index of element 
    avg=0
    #print("{} send to Sk[{}][{}]".format(element,row,col))
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    if col<width:
        # e in Sketch
        Sk[row][col]+=1
    else:
        # e in Other
        pass
    Update_local_max(Sk_head[row],Sk[row],element,col)
    Update_emax(Sk_head,Sk)

'''
    print("e_max:{}".format(e_max))
    for i in range(len(Sk)):
        print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
    print('')
'''


# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,column):
    # local max need only 1 row
    #print("In Update_local_max:")
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
            avg=int((head_item.count-count_sum)//(width*((numerator/denominator)-1)))
            if column<width:
                # e in Sketch
                if column<width:
                    if element_list[column]>avg:
                           head_item.maxID=element.ID
                else:
                    pass

# ==========================update e_max==========================
def Update_emax(head,sketch):
    # pass whole array
    #print("In Update_emax:")
    e_max=get_emax()
    numerator,denominator=get_fraction()
    width,depth=get_width_depth()
    for i in range(len(head)):
        if head[i].maxID=='':
            continue
        else:
            local_max_col,local_max_row=position(Tail(head[i].maxID,0))
            if local_max_col<width:
                # local max in Sketch
                if sketch[local_max_row][local_max_col]>e_max.count:
                    e_max.ID=head[i].maxID
                    e_max.count=sketch[local_max_row][local_max_col]
            else:
                pass
                '''
                # local max in Other
                count_sum=sum(j for j in sketch[i])
                avg=int((head[i].count-count_sum)//(width*((numerator/denominator)-1)))
                if avg>e_max.count:
                    e_max.ID=head[i].maxID
                    e_max.count=avg
                '''
# ========================== BringBack=========================
def BringBack(e_min,head,sketch):
    # bring e_max back to Top
    # e_min=e_max, e_max=Null, delete e_max.count in Sketch, send e_min into Sketch
    e_max=get_emax()
    temp=Tail(e_min.ID,e_min.count)
    e_min.ID=e_max.ID
    e_min.count=e_max.count
    DeleteSk(e_max,head,sketch)
    UpdateSk(temp,head,sketch)

# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # e_max in sketch: sketch[r][c]=0, total count-=sketch[row][col]
    # e_max in Other: total count-=e_max.count
    width,depth=get_width_depth()
    col,row=position(element)
    head[row].count-=e_max.count
        # total_count-=element.count

    if col<width:
        # e_max in sketch, need to config sk[r][c]=0
        sketch[row][col]=0
        head[row].maxID=''
    element.ID=""
    element.count=0
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
        # input: byte
        # output:unsigned- 32 bit int
    hash2=mmh3.hash(element.ID, signed=False)
        # input: str
        # output: unsigned- 32 bit int
    col=hash2 % ((width*numerator)//denominator)
    row=hash1 % depth
    return col,row
def get_fraction():
    return numerator,denominator    
    
# ==========================main=========================    

filename='caida_0.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
depth=4
width=128
size=1024
numerator=12
denominator=10

start=time.time()

Sk_head=[Head(0) for j in range(depth)]
Sketch=np.zeros((depth,width),dtype='int32')
e_max=Tail('',0)
Top=[]

item_count=1000
income=0
with open(src_data,'rb') as file:
    while True:
        e=str(file.read(13))
        if len(e)<13:
            print('EOF')
            break
        else:
            # item_count-=1
            # income+=1
            # print("read {}-th element:{}".format(income,e))
            item=Tail(e,1)            
            index=find(item,Top)
            if index<0:
                if len(Top)<size:
                    Top.append(item)
                else:
                    UpdateSk(item,Sk_head,Sketch)
            else:
                Top[index].count+=1
        Top.sort(key=operator.attrgetter('count'),reverse=True)
        if e_max.count>Top[-1].count:
            BringBack(Top[-1],Sk_head,Sketch)
            #print('Top after BringBack: \n\t{}'.format(Top)) 

end=time.time()
print("Execution time:{} seconds.".format(str(end-start)))
print("Total memory {} bytes".format(sys.getsizeof(Top)+sys.getsizeof(Sketch)+sys.getsizeof(Sk_head)))
print("Top:{} bytes, Sketch:{} bytes, Sketch_head:{} bytes.".format(sys.getsizeof(Top),sys.getsizeof(Sketch),sys.getsizeof(Sk_head)))
print("TOP[20]:\n{}".format(Top[:20]))
print("e_max:{}".format(e_max))
for i in range(len(Sketch)):
    print("Sk[{}]:{},{}".format(i,Sk_head[i],Sketch[i]))
print('')


templi=[]
for i in Top:
    templi.append([i.ID,i.count])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("..\\result\\caida_0\My_caida0_hash.csv",index=False)
df.head(20)