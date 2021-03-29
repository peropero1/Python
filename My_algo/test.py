import ds
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



# ========================== Update Sketch==========================
def UpdateSk(element,width,depth):
    e_max=get_emax()
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
    avg=0
    item=Tail(ID, element.count)
        # ID in Sketch is hash value
    print("\t{} -> {},send to Sk[{}]".format(element,item,row))
    # print("id(Sk[{}]):{}".format(row,id(Sk[row])))
    Sk_head[row].count+=item.count
        # total count+=count
    if len(Sk[row])==0:
        # Sk[row] is empty,append e directly
        Sk[row].append(item)
        Sk_head[row].maxID=element.ID
        match=True
        index=0
    else:
        # Sk[row] is not empty
        index=find(item,Sk[row])
        print("index={}".format(index))
        if index >=0:
            # matches in Sk[row]
            Sk[row][index].count+=item.count
            match=True
        else:
            # doesn't match in Sk[row]
            if len(Sk[row])<width:
                Sk[row].append(item)
                match=True
                index=len(Sk[row])-1
            else:
                # Sk[row] is full
                count_sum=sum(Sk[row][i].count for i in range(len(Sk[row])))
                print("count_sum={}".format(count_sum))
                print("total count={}".format(Sk_head[row].count))
                if Sk_head[row].count==count_sum:
                    # no element in other
                    # print("no element in Other, send to distinct")
                    Sk_head[row].distinct.add(element.ID)
                    match=False
                elif Sk_head[row].count>count_sum:
                    avg=(Sk_head[row].count-count_sum)//len(Sk_head[row].distinct)
                    print("avg:{}".format(avg))
                    if avg>Sk[row][-1].count:
                        # print("avg>last one, update Sk[{}]".format(row))
                        Sk[row][-1].ID=item.ID
                        Sk[row][-1].count=avg
                        match=True
                        index=-1
                    else:
                        Sk_head[row].distinct.add(element.ID)
                        # print("avg< last one,send to distinct")
                        match=False

    
    print("Sk_head[{}]: {}".format(row,Sk_head[row]))
    print("e_max before update:{}".format(e_max))
    # Sk[row].sort(key=operator.attrgetter('count'),reverse=True)
    h1=spookyhash.hash32(bytes((Sk_head[row].maxID),encoding='utf-8'))
    h2=mmh3.hash(str(h1), signed=False)
    max_id=h2 % ((width*3)//2)
    max_id_index=find(Tail(max_id,1),Sk[row])
    print("Sk[{}]:{} before update e_max".format(row,Sk[row]))
    print("index:{},max_id:{}, max_id_index:{}, in Sk[{}]".format(index,max_id,max_id_index,row))
    print("Sk[max_id_index]:{}")
    print("match={}".format(match))
    if max_id_index>0:
        if match:
            # incoming element in Sk[row]:
            print("Sk_head[{}].maxID: {}".format(row,Sk_head[row].maxID))
            if Sk_head[row].maxID=="":
                Sk_head[row].maxID=element.ID
            elif element.ID==Sk_head[row].maxID:
                # update e_max
                if Sk[row][index].count>e_max.count:
                    e_max.ID=element.ID
                    e_max.count=Sk[row][index].count
                else:
                    pass
                # element.ID ≠ maxID
            if Sk[row][index].count>=Sk[row][max_id_index].count:
                Sk_head[row].maxID=element.ID
                if Sk[row][index].count>e_max.count:
                    e_max.ID=element.ID
                    e_max.count=Sk[row][index].count
        else:
            # e not in Sk[row]
            if avg>Sk[row][max_id_index].count:
                Sk_head[row].maxID=element.ID
                if avg>e_max.count:
                    e_max.ID=element.ID
                    e_max.count=avg
    else:
        Sk_head[row].maxID=element.ID

    Sk[row].sort(key=operator.attrgetter('count'),reverse=True)
    
    # print("after sorting id(Sk[{}]):{}".format(row,id(Sk[row])))

    for i in range(len(Sk)):
        print("Sk[{}]:{},{}".format(i,Sk_head[i],Sk[i]))
    print("e_max:{} after UpdateSK()".format(e_max))

# ========================== Update Sketch==========================
    
# ========================== BringBack=========================
def BringBack(e_min,e_max):
    print("BringBack({},{})".format(e_min,e_max))
    print("Top before Bringback:\n\t{}".format(Top))
    e_max=get_emax()
    # print('e_max at first Bringback:{},id(e_max):{}'.format(e_max,id(e_max)))
    temp=Tail(e_min.ID,e_min.count)
    Top[-1].ID=e_max.ID
    Top[-1].count=e_max.count
    Top.sort(key=operator.attrgetter('count'),reverse=True)
    print('Top after BringBack:\n\t{}'.format(Top))
    DeleteSk(e_max)
        # e_max in Sk[row]
    e_max.ID=''
    e_max.count=0
    print("e_max after delete:{},id(e_max):{}".format(e_max,id(e_max)))
    UpdateSk(temp,width,depth)
    
    # print("Sk[] after Update {}:\n\t{}".format(e_min,Sk))

# ========================== BringBack=========================
# ==========================DeleteSk=========================
def DeleteSk(element):
    # 刪除e_max in Sk[row]，找新的e_max
    print("DeleteSK({})".format(element))
    hash1=spookyhash.hash32(bytes((element.ID),encoding='utf-8'))
    hash2=mmh3.hash(str(hash1), signed=False)
    ID=hash2 % ((width*3)//2)
    row=hash1 % depth
    print("row:{},ID:{}".format(row,ID))
    Sk_head[row].count-=element.count
    print("Sk[{}]:{}".format(row,Sk[row]))
    index=find(Tail(ID,1),Sk[row])
    print("index:{}".format(index))
    if index<0:
        pass
    else:
        Sk[row].pop(index)
        Sk_head[row].maxID=""
    '''
    print("index:{}".format(index))
    print('After pop:')
    print("\tSk[{}]={}".format(row,Sk[row]))
    print("Top:\n\t{}".format(Top))
    '''
# ==========================DeleteSk=========================
def get_emax():
    return e_max

def find(e,element_list):
    try:
        # type(element_list[i].ID):int
        # print("e:{}".format(e))
        # print("element_list[1:]: {}".format(element_list[1:]))
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        # print("raise error")
        index=-99
    return index

# ========================main==============================

start=time.time()
filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
depth=4
width=128
size=512

Top=[]
Sk_head=[Head(0) for j in range(depth)]
Sk=[[] for i in range(depth)]
item_count=10000
e_max=Tail('',0)

with open(src_data,'r') as file:
    while item_count:
        element=file.readline().strip('\n')
        if not element:
            break
        else:
            print("read {}-th element: {}".format(-(item_count-51),element))
            item_count-=1
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
                        print("send {} into Sk".format(element))
                        UpdateSk(item,width,depth)
                else:
                    # print("update Top[{}]:".format(index))
                    Top[index].count+=1
            print("Top after read {}:{}\n".format(element,Top))
            Top.sort(key=operator.attrgetter('count'),reverse=True)
            if e_max.count>Top[-1].count:
                BringBack(Top[-1],e_max)
                # print('Top after BringBack: \n\t{}'.format(Top))            
            # print("TOP:{}".format(Top))
end=time.time()
print("e_max:{}".format(e_max))
print("Execution time:{} seconds.".format(str(end-start)))