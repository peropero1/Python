import ds
import spookyhash
import mmh3
from numpy import random
import os

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
        return '[total count: {}, distinct: {}]'.format(self.count,len(self.distinct))
    def __repr__(self):
        return '[total count: {}, distinct: {}]'.format(self.count,len(self.distinct))

class Tail(Node):
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)
    def __repr__(self):
        return '[ID: {}, count: {}]'.format(self.ID,self.count)
# ==========================data structure==========================


def find(e,element_list):
    try:
        print("In find({}):".format(e))
        print("\te:{}".format(e))
        print("\telement_list:{}".format(element_list))
        index_in_for=-99
        for i in range(len(element_list)):
            if e.ID==i.ID:
                index_in_for=i
                break
        print("index_in_for={}".format(index_in_for))
        
        #index = [ele.ID for ele in element_list].index(e.ID)
        # print("index={]}".format(index))
    except:
        index_in_for
        # index=-99
    return index_in_for



# ========================== Update Sketch==========================
def UpdateSk(element,width,depth):
    width+=1
        # 要扣掉head node佔用的長度
    e_max=get_emax()
    # print("first read e_max in UpdateSK, id(e_max):{}".format(id(e_max)))
    hash1=spookyhash.hash32(bytes((element.ID),encoding='utf-8'))
        # input of spooky hash: binary, encoding is parameter of bytes()
        # output of spooky hash: unsigned- 32 bit int
    hash2=mmh3.hash(str(hash1), signed=False)
        # input of mmh3 is str, output unsigned- 32 bit int
    row=hash1 % depth
        # index of row in SK[row]
    ID=hash2 % ((width*3)//2)
        # hash-value(ID) of e
        # range: 2^k *3/2= 3*(2^k-1)
    match=False
        # match= True if e is in Sk[row]
    index=0
    item=Tail(ID, element.count)
        # ID in Sketch is hash value
    print("\t{} -> {},send to Sk[{}]".format(element,item,row))
    Sk[row][0].add_count(item.count)
        # total count+=count
    if len(Sk[row])==1:
        # Head only, append e directly
        Sk[row].append(item)
        # Sk[row][0].maxID=element.ID
        match=True
        index=1
    elif len(Sk[row])<=width:
        put_in=random.choice([0,1],size=1,p=[len(Sk[row])/width,1-len(Sk[row])/width])[0]
            # send into SK[row] with prob. 1-len(SK[row])/width
            # 讓avg(distinct) count >Sk[row]裡的max element時有愈高的機率回到Sk[row]中 ??
        index=find(item,Sk[row])
        print("index={},put_in={}".format(index,put_in))
        if index>0:
            print("{} matches in Sk[{}]".format(item,row))
        else:
            print("doesn't match")
        
            # checks whether h(e) in Sk[row]
        if index<0:
            # h(e) isn't in Sk[row]
            if put_in==1:
                # send h(e) to Sk[row] with prob.(1-r/w)
                Sk[row].append(item)
                match=True
                index=len(Sk[row])-1
            else:
                # send h(e) to other
                match=False
                Sk[row][0].distinct.add(ID)
        else:
            # h(e) is in Sk[row]
            match=True
            Sk[row][index].add_count(item.count)
    else:
        # print("len(Sk):{}".format(len(Sk)))
        # print("send {} to other".format(item.ID))
        match=False
        Sk[row][0].distinct.add(ID)
    
    # update e_max in Sketch
    # print("match={},ID of [{}]= {}".format(match,element.ID,ID))
    # print("Sk[{}]={}".format(row,Sk[row]))
    if match:
        # e.count in Sk[row]> e_max.count
        if Sk[row][index].count>e_max.count:
            e_max.ID=element.ID
            e_max.count=Sk[row][index].count
    else:
        # avg(e.count) in other > e_max.count
        avg=(Sk[row][0].count-sum(Sk[row][i].count for i in range(len(Sk[row]))))/len(Sk[row][0].distinct)
        if avg >e_max.count:
            e_max=Tail(element.ID,avg)
    for i in range(len(Sk)):
        print("SK[{}]:{}.".format(i,Sk[i]))
    print("e_max:{}\n".format(e_max))
# ========================== Update Sketch==========================
def get_emax():
    return e_max




filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)


depth=4
width=4
Sk=[[ds.Head(0)] for j in range(depth)]
item_count=50
e_max=Tail('',0)
read_item=0

with open(src_data,'r') as file:
    while item_count:
        element=file.readline().strip('\n')
        if not element:
            break
        else:
            read_item+=1
            print("read {}-th: {}".format(read_item,element))
            item_count-=1
            item=Tail(element,1)
            UpdateSk(item,width,depth)
            