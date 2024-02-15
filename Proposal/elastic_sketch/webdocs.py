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

datapath='..\dataset\webdocs'
pattern='out_.*'
r=re.compile(pattern)
filelist=list(filter(r.match,os.listdir(datapath)))
d=32
w=256
size=512
cms = CountMinSketch(width=w, depth=d)
Top=[None]*size
threshold=8

item_count=10000
income=0
collision=0

start=time.time()
for datafile in filelist[:1]:
    src_data=os.path.join(datapath,datafile)
    with open(src_data,'r') as file:
        while True:
            e=file.readline().strip('\n')
            #income+=1
            #print("read {}-th item:{}".format(income,e)) 
            if not e:
                print("EOF")
                break
            else:
                #item_count-=1
                index=position(e,size)
                #print("index={}".format(index))
                if Top[index]==None:
                    Top[index]=Tail(e)
                    #print(Top)
                else:
                    if Top[index].ID ==e:
                        Top[index].vote_pos+=1
                    elif Top[index].ID !=e:
                        Top[index].vote_neg+=1
                        vote_threshold=Top[index].vote_neg/Top[index].vote_pos
                        if vote_threshold<threshold:
                            cms.add(e)
                        else:
                            cms.add(e,Top[index].vote_pos)
                            Top[index]=Tail(e,1,True,1)
end=time.time()
print("Top-{},Sketch:{}*{}".format(size,d,w))
print("Execution time:{:8.3f} seconds.".format(end-start))
print("Total memory {} bytes= ".format(sys.getsizeof(Top)+sys.getsizeof(cms._bins)),end='')
print("Top:{} bytes, Sketch:{} bytes.".format(sys.getsizeof(Top),sys.getsizeof(cms._bins)))


#====================Top to csv=============================
templi=[[i.ID,Query(i.ID)] for i in Top]
df=pd.DataFrame(templi,columns=['ID', 'Count'])
df=df.sort_values(by='Count',ascending=False)
name="Ela_webdocs_Top-"+str(size)+'_'+str(d)+'_'+str(w)+'.csv'
df.to_csv(os.path.join(r'..\result',name),index=False)
    #儲存Top的結果
#====================result compare=============================
gr_path='..\dataset\webdocs'
gr_file_name='webdocs_00_ground_truth.csv'
grtruth=pd.read_csv(os.path.join(gr_path,gr_file_name))
Ela_result=pd.read_csv(os.path.join(r'..\result',name))

# precision
gt_set=set(grtruth['Element'][:size])
    # Top-k ID of ground truth
my_set=set(Ela_result['ID'])
precision=len(gt_set & my_set)/len(my_set)
    # &: set 交集運算
print("Precision: {:8.4f}".format(precision))

# ====================ARE/AAE of Top====================
gt_li=grtruth.values.tolist()[:size]
    # ground truth of top-k with count
top_li=Ela_result.values.tolist()
    # result of top-k with count
ID=[j[0] for j in gt_li]
top_are=0
top_aae=0
tp=0
fp=0
for item in top_li:
    if item[0] in ID:
        index=ID.index(item[0])
        top_are+=abs(gt_li[index][1]-item[1])/gt_li[index][1]
        top_aae+=abs(gt_li[index][1]-item[1])
        tp+=1
    else:
        fp+=1
top_are=top_are/size
top_aae=top_aae/size

# ====================ARE/AAE of all====================
# ARE/AAE
gt_dict=dict(grtruth.values.tolist())
    # ground truth for all
top_dict=dict(Ela_result.values.tolist())
distinct=len(gt_dict)
    # cardinality of all incoming elements

all_are_error=0
all_aae_error=0
count_estimate=0

startx=time.time()
for item in gt_dict:
    count_estimate=Query(str(item))
        # Query(item)已包含Top及CMS中的 estimate count
    all_are_error+=abs(count_estimate-gt_dict[item])/gt_dict[item]
    all_aae_error+=abs(count_estimate-gt_dict[item])
endx=time.time()

all_ARE=all_are_error/distinct
all_AAE=all_aae_error/distinct
print("Find:{}, TP:{}, FP:{}".format(len(gt_set & my_set),tp,fp))
print("Top_ARE: {:8.6f}".format(top_are))
print("Top_AAE: {:8.6f}".format(top_aae))
print("all_ARE: {:8.6f}".format(all_ARE))
print("all_AAE: {:8.6f}".format(all_AAE))
print("Estimate time:{:8.3f} seconds.".format(endx-startx))