import spookyhash
import mmh3
from numpy import random
import os
import time
import operator
import hyperloglog
import sys
import pandas as pd
import cProfile

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
        return '[total:{}, dist:{}, max:{}]'.format(self.count,len(self.distinct),self.maxID)
    def __repr__(self):
        return '[total:{}, dist:{}, max:{}]'.format(self.count,len(self.distinct),self.maxID)

class Tail(Node):
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return '[ID:{}, count:{}]'.format(self.ID,self.count)
    def __repr__(self):
        return '[ID:{}, count:{}]'.format(self.ID,self.count)
# ==========================data structure==========================


# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    # print("In UpdateSk()")
    e_max=get_emax()
    ID,row=position(element)
        # row position of e and ID=h(e) in Sketch 
    avg=0
    item=Tail(ID, element.count)
        # ID in Sketch is hash value
    # print("{} -> {},send to Sk[{}]".format(element,item,row))
    # ==========================update sketch==========================
    index=find(item,Sk[row])
        # find index of e in Sk[row]
    if index >=0:
        # e matches in Sk[row]
        Sk[row][index].count+=item.count
    else:
        # e doesn't match in Sk[row]
        if len(Sk[row])==0:
            Sk[row].append(item)
            index=0
            Sk_head[row].maxID=element.ID
                # unhashed ID
        elif len(Sk[row])<width:
            # Sk[row] is not full
            Sk[row].append(item)
            index=len(Sk[row])-1      
            # match=True
        else:
            # Sk[row] is full
            count_sum=sum(Sk[row][i].count for i in range(len(Sk[row])))
            if Sk_head[row].count==count_sum:
                # no other, send e to Other
                Sk_head[row].distinct.add(element.ID)
                # match=False
            else:
                # something in other and total count > sum
                if len(Sk_head[row].distinct)>0:
                    Sk_head[row].distinct.add(element.ID)
                    avg=(Sk_head[row].count-count_sum)//len(Sk_head[row].distinct)
                    # print("avg:{}".format(avg))
                else:
                    Sk_head[row].distinct.add(element.ID)
                    # print("distinct element:{}".format(len(Sk_head[row].distinct)))
                    # print("avg< last one,send to distinct")
                    # match=False
    Sk_head[row].count+=item.count
        # total count最後再+1 在line 82要compare distinct
    # now we have:
    # ID: h2(h1(e)), hash value of e
    # row: h1(e), row index of e
    # index: column index of e
    # Sk_head[row].count: total count of Sk[row]
    # Sk_head[row].maxID: local max count element of Sk[row]
    # Sk_head[row].distinct: estimated element of Other part in Sk[row]
    # count_sum: sum of count in Sketch[row]
    # avg: average count of Other part in Sk[row]
    # ==========================update local max==========================
    Update_local_max(Sk_head[row],Sk[row],avg,element,index)
    # Sk[row].sort(key=operator.attrgetter('count'),reverse=True)
    
    # ==========================update e_max==========================
    Update_emax(Sk_head[row],Sk[row],element,avg)
    
    Sk[row].sort(key=operator.attrgetter('count'),reverse=True)
    # print("e_max:{}".format(e_max))
    # print("Sk_head[{}]:{}".format(row,Sk_head[row]))
    '''
    for i in range(len(Sk)):
        print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
    '''


# ==========================update local max==========================    
def Update_local_max(head_item,element_list,avg,incoming_element,index):
    # Sk_head[row],Sk[row],avg
    # print("In Update_local_max():")
    numertor,denominator=get_fraction()
    width,depth=get_width_depth()
    if head_item.maxID=='':
        head_item.maxID=incoming_element.ID
    else:
        local_max_ID=mmh3.hash(str(spookyhash.hash32(bytes(str(head_item.maxID),encoding='utf-8'))), signed=False) % ((width*numertor)//denominator)
        #print("local_max_ID:{}".format(local_max_ID))
        local_max_index=find(Tail(local_max_ID,1),element_list)
        #print("local_max_index:{}".format(local_max_index))
        # 此處當hashed ID相同時暫不更新 local max
        if local_max_index>=0:
            # local max exists
            if index>=0:
                # e in Sk[row]
                if element_list[index].count>element_list[local_max_index].count:
                    head_item.maxID=incoming_element.ID
            else:
                # e in Other
                if avg>element_list[local_max_index].count:
                    head_item.maxID=incoming_element.ID
        else:
            # local max doesn't exists
            head_item.maxID=incoming_element.ID

# ==========================update e_max==========================
def Update_emax(head_item,element_list,incoming_element,avg_count):
    # Sk_head[row],Sk[row],e_max
    # print("In Update_emax():")
    e_max=get_emax()
    numerator,denominator=get_fraction()
    # local_max_ID=""
    # local_max_index=""
    # print("e_max before update:{}".format(e_max))
    # print("Sk_head:{}".format(head_item))
    width,depth=get_width_depth()
    if head_item.maxID!="":
        local_max_ID=mmh3.hash(str(spookyhash.hash32(bytes(str(head_item.maxID),encoding='utf-8'))), signed=False) % ((width*numerator)//denominator)
        # print("local_max_ID:{}".format(local_max_ID))
        local_max_index=find(Tail(local_max_ID,1),element_list)        
        # print("local_max_index:{}".format(local_max_index))
        if local_max_index>=0:
            if element_list[local_max_index].count>e_max.count:
                e_max.ID=head_item.maxID
                e_max.count=element_list[local_max_index].count
        else:
            if avg_count>e_max.count:
                e_max.ID=head_item.maxID
                e_max.count=avg_count
    #print("e_max after update:{}".format(e_max))

# ========================== BringBack=========================
def BringBack(e_min,head,sketch):
    # Bring e_max back into Top
    # Sk_head,Sk[row]
    e_max=get_emax()
    # print("\nIn BringBack():")
    temp=Tail(e_min.ID,e_min.count)
    e_min.ID=e_max.ID
    e_min.count=e_max.count
    # print('Top after BringBack:\n\t{}'.format(Top))
    DeleteSk(e_max,head,sketch)
    # update e_max in Sk[row]
    # print("e_max after delete:{},id(e_max):{}".format(e_max,id(e_max)))
    UpdateSk(temp,head,sketch)
    # print("Sk[] after Update {}:\n\t{}".format(e_min,Sk))

# ========================== BringBack=========================
# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # 刪除e_max in Sk[row]
    # print("\nIn DeleteSK({}):".format(element))
    width,depth=get_width_depth()
    ID,row=position(element)
    # print("row:{},ID:{} of e_max".format(row,ID))
    head[row].count-=element.count
        # total_count=total_count-e_max.count
    # print("Sk[{}]:{}".format(row,sketch[row]))
    index=find(Tail(ID,1),sketch[row])
    # print("index:{} in Sk[{}]".format(index,row))
    if index>=0:
        sketch[row].pop(index)
        # element_list[row].sort(key=operator.attrgetter('count'),reverse=True)
        head[row].maxID=""

    element.ID=""
    element.count=0
    # print("e_max After DeleteSk(element):{},id(e_max):{}".format(e_max,id(e_max)))
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
    hash2=mmh3.hash(str(hash1), signed=False)
        # input of mmh: str
        # output: unsigned- 32 bit int
    ID=hash2 % ((width*numertor)//denominator)
    row=hash1 % depth    
    return ID,row
def get_fraction():
    return numerator,denominator

# ==========================main=========================   
        
start=time.time()

filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
depth=4
width=128
size=1024
numerator=12
denominator=10
    # numerator/denominator decides ratio of Other+Sketch /Sketch


Top=[]
Sk_head=[Head(0) for j in range(depth)]
Sk=[[] for i in range(depth)]
item_count=1000
i=0
e_max=Tail('',0)

with open(src_data,'r') as file:
    while True:
        element=file.readline().strip('\n')
        if not element:
            break
        else:
            # i+=1
            # print("\nread {}-th element: {}".format(i,element))
            # item_count-=1
            item=Tail(element,1)
            if len(Top)==0:
                Top.append(item)
                # print("len(Top)==0, Top append:{}".format(Top))
            else:
                index=find(item,Top)
                # print("index={}".format(index))
                if index<0:
                    if len(Top)<size:
                        Top.append(item)
                        # print("index={},Top after append: {},\nlen(Top):{}".format(index,Top,len(Top)))
                    else:
                        UpdateSk(item,Sk_head,Sk)
                else:
                    # print("update Top[{}]:".format(index))
                    Top[index].count+=1
            Top.sort(key=operator.attrgetter('count'),reverse=True)
            # ID,row=position(Top[-1])
            if e_max.count>Top[-1].count:
                BringBack(Top[-1],Sk_head,Sk)
                # print('Top after BringBack: \n\t{}'.format(Top))            


end=time.time()
print("Sk_head:{}".format(Sk_head))
print("TOP[20]:{}".format(Top[:20]))
# print("\nSketch:{}".format(Sk))
print("Total memory {} bytes".format(sys.getsizeof(Top)+sys.getsizeof(Sk)+sys.getsizeof(Sk_head)))
print("Top:{} bytes, Sketch:{} bytes, Sketch_head:{} bytes.".format(sys.getsizeof(Top),sys.getsizeof(Sk),sys.getsizeof(Sk_head)))
print("Execution time:{} seconds.".format(str(end-start)))

#　conver Top into df    
templi=[]
for i in Top:
    templi.append([i.ID,i.count])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("..\\result\\kosarak\\Myalgo_kosarak_100k_count.csv",index=False)
df.head(20)

