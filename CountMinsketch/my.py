# Caida 2016
# 只讀1個檔(0.dat)
# Execution time: 582.126701593399 seconds

import sys
import os
import time
import spookyhash
import mmh3
import hyperloglog
import operator
import pandas as pd
from numpy import random

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

# ========================== Update Sketch==========================
def UpdateSk(element,width,depth):
    #　width+=1
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
    item=Tail(ID,element.count)
    
    # print('UpdateSk:{}->ID {}'.format(element,ID))
    # print("hash1: {}".format(hash1))
    # print("hash2: {}".format(hash2))
    # print("match row: {}".format(row))
    # print("SK[{}]:{}".format(row,Sk[row]))
    # print("len(Sk[{}]:{})".format(row,len(Sk[row])))
    
    Sk[row][0].add_count(item.count)
        # total count+=count
    if len(Sk[row])==1:
        # Head only, append e directly
        Sk[row].append(item)
        Sk[row][0].maxID=element.ID
        match=True
        index=1
            # e is in Sk[row][1]
        # print('Sk[{}] when len(Sk[{}])==1:\n\t{}'.format(row,row,Sk[row]))
        # print("After append:\n{}".format(Sk[row]))
        # print("length of Sk[row]: {}".format(len(Sk[row])))
    elif len(Sk[row])<width:
        put_in=random.choice([0,1],size=1,p=[len(Sk[row])/width,1-len(Sk[row])/width])[0]
            # send into SK[row] with prob. 1-len(SK[row])/width
        for i in range(1,len(Sk[row])):
            # checks whether e is in SK[row]
            if ID == Sk[row][i].ID:
                match=True
                Sk[row][i].add_count(item.count)
                index=i
                '''
                print('{} matches in Sk[{}][{}]:{}'.format(item.ID,row,index,Sk[row][index].ID))
                print('Sk[{}]:\n\t{}'.format(row,Sk[row]))
                '''

                break
            else:
                match=False
        if not match:
            if put_in==1:
                # send e into SK[row]
                # print('put_in={}, send e into SK[{}]'.format(put_in,row))
                Sk[row].append(item)
                match=True
                index=len(Sk[row])-1
                # print('Sk[{}]:\n\t{}\n'.format(row,Sk[row]))
            else:
                Sk[row][0].distinct.add(ID)
                ''' 
                print('put_in={}, send e into other,update distinct'.format(put_in,len(Sk[row][0].distinct)))
                print('Sk[{}]:\n\t {}'.format(row,Sk[row]))
                '''

    elif len(Sk[row])==width:
        # len(Sk[row])=width, put e into other
        Sk[row][0].distinct.add(ID)
    # print("match:{}".format(match))
   
    # 這段會影響e_max
    if match:
        # print("e_max in UpdateSK line 114, id(e_max):{}".format(id(e_max)))
        if Sk[row][index].count>e_max.count:
            e_max.ID=element.ID
            e_max.count=Sk[row][index].count
        # print('line 115 e_max: e_max={}'.format(e_max))
            
    else:
        # avg count of other > e_max.count
        avg=(Sk[row][0].count-sum(Sk[row][i].count for i in range(len(Sk[row]))))/len(Sk[row][0].distinct)
        if avg >e_max.count:
            e_max=Tail(element.ID,Sk[row][index].count)
        # print('line 122 e_max: e_max={}'.format(e_max))
    # print('line 123 e_max:{}'.format(get_emax()))
    # print('')
# ========================== Update Sketch==========================
def get_emax():
    return e_max
# ========================== BringBack=========================
def BringBack(e_min,e_max):
    # print("Top before Bringback:\n\t{}".format(Top))
    e_max=get_emax()
    # print('e_max at first Bringback:{},id(e_max):{}'.format(e_max,id(e_max)))
    temp=Tail(e_min.ID,e_min.count)
    Top[-1].ID=e_max.ID
    Top[-1].count=e_max.count
    Top.sort(key=operator.attrgetter('count'),reverse=True)
    # print('Top after BringBack:\n\t{}'.format(Top))
    DeleteSk(e_max)
        # e_max in Sk[row]
    e_max.ID=''
    e_max.count=0
    # print("e_max after delete:{},id(e_max):{}".format(e_max,id(e_max)))
    UpdateSk(temp,width,depth)
    
    # print("Sk[] after Update {}:\n\t{}".format(e_min,Sk))

# ========================== BringBack=========================
def DeleteSk(element):
    # 刪除e_max，找新的e_max
    # print('Delete start======================================')
    hash1=spookyhash.hash32(bytes((element.ID),encoding='utf-8'))
    hash2=mmh3.hash(str(hash1), signed=False)
    ID=hash2 % ((width*3)//2)
    row=hash1 % depth
    index=0
    for i in range(1,len(Sk[row])):
        if Sk[row][i].ID==ID:
            # print("found {} at SK[{}][{}], ID={}".format(element.ID,row,i,Sk[row][i].ID))
            index=i
            # print("pop element:{}".format(Sk[row][index]))
            Sk[row].pop(index)
            break
    # print('Delete Sk for find max of Sk[i] len(Sk):{}'.format(len(Sk)))
    Sk[row][0].count-=element.count
    '''
    print("index:{}".format(index))
    print('After pop:')
    print("\tSk[{}]={}".format(row,Sk[row]))
    print("Top:\n\t{}".format(Top))
    print('Delete Sketch over======================================')
    '''

# ========================== BringBack=========================

start=time.time()
'''
datapath=r'X:\\NTU\\ML-sketch\\dataset\\caida2016\\'
datali=os.listdir(datapath)[0]
'''
src_data='caida_0.dat'

depth=4
width=128
size=512
Top=[]
Sk=[[Head(0)] for j in range(depth)]
e_max=Tail('',0)
item_count=0


# os.path.join(datapath,datali),'rb'
with open(src_data,'rb') as file:
    # print("file open now: {}".format(file.name))
     #以binary讀取，資料型態也為byte
    while True:
        element=str(file.read(13))
        if len(element)<13:
            print('EOF')
            break
        else:
            item_count+=1
            print("read {}th element: {}".format(item_count,element))
            # Update_Top(Tail(element,1))
            # item_count-=1
            if len(Top)==0:
                Top.append(Tail(element,1))
            else:
                found=False
                for i in range(len(Top)):
                    if Top[i].ID==element:
                        found=True
                        Top[i].add_count(1)
                        break
                if not found:
                    if len(Top)<size:
                        Top.append(Tail(element,1))
                    else:
                        # print("e_max in main, id(e_max):{}".format(id(e_max)))
                        UpdateSk(Tail(element,1),width,depth)
            Top.sort(key=operator.attrgetter('count'),reverse=True)
            # print("Top:{}".format(Top))
            if e_max.count>Top[-1].count:
                BringBack(Top[-1],e_max)
                # bring back
                # 要去掉SK[row]中的e_max.ID及count的node
                # print('Top after BringBack: \n\t{}'.format(Top))

    end=time.time()
    print("Top[50]:\n\t{}".format(Top[:50]))
    print("Sk:\n\t{}".format(Sk))
    print("Total memory {} bytes.".format(sys.getsizeof(Top)+sys.getsizeof(Sk)))
    print('Execution time: {} seconds'.format(str(end-start)))

    
#　conver Top into df    
templi=[]
for i in Top:
    templi.append([i.ID,i.count])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("My_algo_caida_0_distinct_count.csv",index=False)
df.head(50)

