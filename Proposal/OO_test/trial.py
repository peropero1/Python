# dictionary implementation

from Node import DS
from Tools import Func
from Tools import Config
import pandas as pd
import numpy as np
import os
import time
import operator
import sys


# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    #e_max=Config.e_max
    col,row=Func.position(element)
        # col / row index of element
    #print("{} send to Sk[{}][{}]".format(element,row,col))
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    Sk_head[row].distinct.add(element.ID)
    Sk[row][col]+=1
    Update_local_max(Sk_head[row],Sk[row],element,col)
    #Update_emax(Sk_head,Sk,row)

# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,column):
    # local max need only 1 row
    #print("In Update_local_max:")
    width,depth=Config.width,Config.depth
    if head_item.maxID=='':
        head_item.maxID=element.ID
        head_item.keep=1
    elif head_item.maxID==element.ID:
        head_item.keep+=1
    else:
        # head_item.maxID != element.ID:
        local_max_col,local_max_row=Func.position(DS.Tail(head_item.maxID,0))
            # element_list[local_max_col]: lhh的估計值
        if local_max_col==column:
            # lhh collision with e
            head_item.keep-=1
            if head_item.keep==0:
                head_item.maxID=element.ID
                head_item.keep=1
        elif element_list[local_max_col]<element_list[column]:
            # not collision
            head_item.maxID=element.ID
            head_item.keep=1
    if element_list[column]>Config.e_max.count:
        Config.e_max.ID=element.ID
        Config.e_max.count=element_list[column]
        

# ==========================update e_max==========================
def Update_emax(head,sketch,sk_row):
    local_max_col,local_max_row=Func.position(DS.Tail(head[sk_row].maxID,0))
    if sketch[local_max_row][local_max_col]>Config.e_max.count:
        Config.e_max.ID=head[sk_row].maxID
        Config.e_max.count=sketch[local_max_row][local_max_col]    


# ========================== BringBack=========================
def BringBack(e_min,Top,head,sketch):
    # bring e_max back to Top
    # e_min=e_max, e_max=Null, delete e_max.count in Sketch, send e_min into Sketch
    Top.pop(e_min.ID)
    Top[Config.e_max.ID]=Config.e_max.count
    DeleteSk(e_max,head,sketch)
    UpdateSk(e_min,head,sketch)
    c,r=Func.position(Config.e_max)
    #head[r].bringback+=1


# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # e_max in sketch: sketch[r][c]=0, total count-=sketch[row][col]
    #width,depth=get_width_depth()
    col,row=Func.position(element)
    head[row].count-=element.count
        # total_count-=element.count
    sketch[row][col]=0
    head[row].maxID=''
    # reset e_max
    element.ID=""
    element.count=0

    
# ==========================main=========================    

filename='kosarak.dat'
dataset='kosarak'
filepath=r"..\dataset\kosarak"
src_data=os.path.join(filepath,filename)

w=128
d=128
size=4096
Config.Set_default(w,d,size)
    # set width, depth, size of Sk, random seed of hash
    # Config.width, Config.depth
e_max=Config.e_max
    # initialize e_max
    
Sk_head=[DS.Head(0) for j in range(Config.depth)]
Sketch=np.zeros((Config.depth,Config.width),dtype='int32')
Top_dict=dict()
e_min=DS.Tail("",1)

item_count=100
#income=0
start=time.time()
with open(src_data,'r') as file:
    while True:
        e=file.readline().strip('\n')
        if not e:
            print('EOF')
            break
        else:
            #item_count-=1
            item=DS.Tail(e,1)
            #print("read {},e_min={}".format(e,e_min))
            if Top_dict.get(item.ID):
                # e in Top
                Top_dict[item.ID]+=1
            else:
                if len(Top_dict)<Config.size:
                    Top_dict[item.ID]=1
                else:
                    UpdateSk(item,Sk_head,Sketch)
        if Config.e_max.count>e_min.count:
            min_ele = min(Top_dict, key=Top_dict.get)
                # 找dict中的最小key元素
            e_min=DS.Tail(min_ele,Top_dict[min_ele])
            BringBack(e_min,Top_dict,Sk_head,Sketch)

end=time.time()

print("Top-{},Sketch:{}*{}".format(Config.size,Config.depth,Config.width))
print("Execution time:{:8.3f} seconds.".format(end-start))
Top_dict=dict(sorted(Top_dict.items(), key=lambda item: item[1],reverse=True))
