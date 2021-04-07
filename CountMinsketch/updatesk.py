import spookyhash
import mmh3
from numpy import random
import os
import time
import operator
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
    ID,row=position(element)
        # row position of e and ID=h(e) in Sketch 
    avg=0
    item=Tail(ID, element.count)
        # ID in Sketch is hash value
    #print("{} -> {},send to Sk[{}]".format(element,item,row))
    # ==========================update sketch==========================
    index=find(item,Sk[row])
        # find index of e in Sk[row]
    Sk_head[row].count+=item.count
    if index >=0:
        # e matches in Sk[row]
        Sk[row][index].count+=item.count
    else:
        # e doesn't match in Sk[row]
        if len(Sk[row])<width:
            Sk[row].append(item)
            index=len(Sk[row])-1
        else:
            Sk_head[row].distinct.add(element.ID)
            
    Update_local_max(Sk_head[row],Sk[row],element,index)
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

    
    # Sk[row].sort(key=operator.attrgetter('count'),reverse=True)
    # print("e_max:{}".format(e_max))
    # print("Sk_head[{}]:{}".format(row,Sk_head[row]))
    
    '''
    print("e_max:{}".format(e_max))
    for i in range(len(Sk)):
        print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
    print('')    
    '''


# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,index):
    #print("In Update_local_max, Sk[row]:{}".format(element_list))
    numertor,denominator=get_fraction()
    width,depth=get_width_depth()
    if head_item.maxID=='':
        head_item.maxID=element.ID
    else:
        local_max_ID=(mmh3.hash(head_item.maxID, signed=False))% ((width*numertor)//denominator)
        local_max_index=find(Tail(local_max_ID,1),element_list)
        # print("local_max_index:{}".format(local_max_index))
        if local_max_index>=0:
            if index>=0:
                if element_list[index].count >element_list[local_max_index].count:
                    head_item.maxID=element.ID
            else:
                # index=-99
                count_sum=sum(element_list[i].count for i in range(len(element_list)))
                try:
                    avg=(head_item.count-count_sum)//(len(element_list)+1)
                except ZeroDivisionError:
                    print("len(head_item.distinct)={}".format(len(self.distinct)))
                else:
                    if avg>element_list[local_max_index].count:
                        head_item.maxID=element.ID
        else:
            #　local_max_inde＝-99, local max is in Other
            count_sum=sum(element_list[i].count for i in range(len(element_list)))
            try:
                avg=(head_item.count-count_sum)//(len(element_list)+1)
            except ZeroDivisionError:
                print("len(head_item.distinct)={}".format(len(self.distinct)))
            else:
                if index>=0:
                    if element_list[index].count >avg:
                        head_item.maxID=element.ID
                else:
                    head_item.maxID=element.ID
 # ==========================update e_max==========================
def Update_emax(head,sketch):
    e_max=get_emax()
    numerator,denominator=get_fraction()
    width,depth=get_width_depth()
    for i in range(len(head)):
        if head[i].maxID=='':
            continue
        else:
            local_max_ID=(mmh3.hash(head[i].maxID, signed=False))% ((width*numerator)//denominator)
            local_max_index=find(Tail(local_max_ID,1),sketch[i])
            if local_max_index>=0:
                if sketch[i][local_max_index].count>e_max.count:
                    e_max.ID=head[i].maxID
                    e_max.count=sketch[i][local_max_index].count

    
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
    numertor,denominator=get_fraction()
    width,depth=get_width_depth()
    hash1=spookyhash.hash32(bytes(str(element.ID),encoding='utf-8'))
        # input of spooky: byte
        # output of spooky:unsigned- 32 bit int
    hash2=mmh3.hash(element.ID, signed=False)
        # input of mmh: str
        # output: unsigned- 32 bit int
    ID=hash2 % ((width*numertor)//denominator)
    row=hash1 % depth
    return ID,row
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
Sk=[[] for i in range(depth)]

e_max=Tail('',0)
# item_count=10000
with open(src_data,'r') as file:
    while True:
        element=file.readline().strip('\n')
        if not element:
            break
        else:
            #item_count-=1
            item=Tail(element,1)
            UpdateSk(item,Sk_head,Sk)
end=time.time()
print("Execution time:{} seconds.".format(str(end-start)))
print("e_max:{}".format(e_max))
for i in range(len(Sk)):
    print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
print('')