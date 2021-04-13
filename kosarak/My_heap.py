
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

# ==========================Heap==========================

class BinHeap():
    def __init__(self):
        self.heap_list=[0]
        self.current_size=0
    def perc_up(self,i):
        while i >>1 >0:
            if self.heap_list[i].count< self.heap_list[i>>1].count:
                self.heap_list[i].count, self.heap_list[i>>1].count=self.heap_list[i>>1].count,self.heap_list[i].count
            i=i>>1
    def insert(self,k):
        self.heap_list.append(k)
        self.current_size+=1
        self.perc_up(self.current_size)
    def __str__(self):
        return str(self.heap_list)
       
    def perc_down(self,i):
        while (i<<1)<=self.current_size:
            minchild=self.min_child(i)
            if self.heap_list[i].count>self.heap_list[minchild].count:
                
                self.heap_list[i], self.heap_list[minchild]=self.heap_list[minchild],self.heap_list[i]
            i=minchild

    def min_child(self,i):
        if (i <<1)+1>self.current_size:
            return i<<1
            # 若只剩1個child就只能return 它
        else:
            if self.heap_list[i<<1].count< self.heap_list[(i <<1)+1].count:
                # 左小於右
                return i<<1
            else:
                return (i <<1)+1

    def del_min(self):
        return_value=self.heap_list[1]
            # return root
        #print("swap:")
        self.heap_list[1],self.heap_list[self.current_size]=self.heap_list[self.current_size],self.heap_list[1]
        #print(self.heap_list)
            # swap(root, last)
        self.current_size-=1
        self.heap_list.pop()
            # remove list[last element]
        #print("after pop: {}".format(self.heap_list))
        self.perc_down(1)
            # 從root往下調整
        return return_value    

# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    #print("In UpdateSk:")
    #print("Top:{}".format(Top))
    e_max=get_emax()
    width,depth=get_width_depth()
    col,row=position(element)
        # col / row index of element 
    avg=0
    #print("{} send to Sk[{}][{}]".format(element,row,col))
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    Sk_head[row].distinct.add(element.ID)
    Sk[row][col]+=1
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
    width,depth=get_width_depth()
    if head_item.maxID=='':
        head_item.maxID=element.ID
    else:
        # local_max_col=(mmh3.hash(head_item.maxID,signed=False))% ((width*numerator)//denominator)
        local_max_col=(mmh3.hash(head_item.maxID,signed=False))% width
        if element_list[local_max_col]<element_list[column]:
            head_item.maxID=element.ID

# ==========================update e_max==========================
def Update_emax(head,sketch):
    # pass whole array
    #print("In Update_emax:")
    e_max=get_emax()
    width,depth=get_width_depth()
    for i in range(len(head)):
        if head[i].maxID=='':
            continue
        else:
            local_max_col,local_max_row=position(Tail(head[i].maxID,0))
            if sketch[local_max_row][local_max_col]>e_max.count:
                e_max.ID=head[i].maxID
                e_max.count=sketch[local_max_row][local_max_col]

# ========================== BringBack=========================
def BringBack(Heap,head,sketch):
    # bring e_max back to Top
    # e_min=e_max, e_max=Null, delete e_max.count in Sketch, send e_min into Sketch
    #print("In BringBack:")
    #print("Top before bringback:\n{}".format(Heap))
    e_max=get_emax()
    e_min=Heap.heap_list[1]
    #print("e_min:{}".format(e_min))
    Heap.insert(Tail(e_max.ID,e_max.count))
    #print("After insert e_max:\n{}".format(Heap))
    Heap.del_min()
    #print("After delmin:\n{}".format(Heap))
    DeleteSk(e_max,head,sketch)
    UpdateSk(e_min,head,sketch)
    #print("Leave BringBack")
    
    '''
    e_max=get_emax()
    temp=Tail(e_min.ID,e_min.count)
    e_min.ID=e_max.ID
    e_min.count=e_max.count
    DeleteSk(e_max,head,sketch)
    UpdateSk(temp,head,sketch)
    '''

# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # e_max in sketch: sketch[r][c]=0, total count-=sketch[row][col]
    #print("In DeleteSk:")
    
    width,depth=get_width_depth()
    col,row=position(element)
    head[row].count-=element.count
        # total_count-=element.count
    sketch[row][col]=0
    head[row].maxID=''
    element.ID=""
    element.count=0
    '''
    print("Top :\n{}".format(Top))
    print("Leave DeleteSk:")       
    '''
 
# ==========================Tools=========================    
def get_emax():
    return e_max
def get_width_depth():
    return width,depth

def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)+1
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
# ==========================main==========================    
import numpy as np
import spookyhash
import mmh3
import os
import pandas as pd
import time
import operator
import hyperloglog
import sys
import random

filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)

depth=4
width=256
size=1024
Sk_head=[Head(0) for j in range(depth)]
Sketch=np.zeros((depth,width),dtype='int32')
e_max=Tail('',0)
numerator=1
denominator=1
Top=BinHeap()

start=time.time()

item_count=100
income=0
with open(src_data,'r') as file:
    while True:
        e=file.readline().strip('\n')
        if not e:
            break
        else:
            #item_count-=1
            #income+=1
            #print("\nread {}-th element:{}".format(income,e))
            item=Tail(e,1)
            index=find(item,Top.heap_list[1:])
            if index<0:
                if Top.current_size<size:
                    Top.insert(item)
                    # append last then perc_up
                else:
                    UpdateSk(item,Sk_head,Sketch)
            else:
                #print("Match in Top[{}]:\n{}".format(index,Top))
                Top.heap_list[index].count+=1
                #print("Top after update:\n{}".format(Top))
                while(index>0):
                    Top.perc_down(index)
                    index-=1
                #print("after perc_down:\n{}".format(Top))
        if e_max.count>Top.heap_list[1].count:
            BringBack(Top,Sk_head,Sketch)
            #print("Top after BringBack:\n{}".format(Top))

end=time.time()
print("Execution time:{} seconds.".format(str(end-start)))
print("Total memory {} bytes".format(sys.getsizeof(Top.heap_list)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*depth))
print("Top:{} bytes, Sketch:{} bytes, Sketch_head:{} bytes.".format(sys.getsizeof(Top.heap_list),Sketch.nbytes,sys.getsizeof(Sk_head[0])*depth))
print("Top:\n{}".format(Top.heap_list[1:21]))
for i in range(len(Sketch)):
    print("Sk[{}]:{},{}".format(i,Sk_head[i],Sketch[i]))
print('')

#====================result compare=============================

templi=[[i.ID,i.count] for i in Top.heap_list[1:]]
df=pd.DataFrame(templi,columns=['ID', 'Count'])
df=df.sort_values(by='Count',ascending=False)

path='..\\result\\kosarak\\'
name="MyBinHeap_kosarak"+'_'+str(size)+'_'+str(depth)+'_'+str(width)
df.to_csv(path+name+".csv",index=False)

groundtruth='kosarak_ground_truth.csv'
final=name+".csv"

# ====================precision, ARE, AAE====================
grtruth=pd.read_csv(os.path.join(path,groundtruth))
    # compare with Top-k and groundtruth[k]
My_result=pd.read_csv(os.path.join(path,final))

# precision
gt_set=set(grtruth['Element'][:size])
my_set=set(My_result['ID'])
precision=len(gt_set & my_set)/len(my_set)
    # &: set 交集運算
print("Precision: {}".format(precision))

# ARE in Top
gt_dict=dict(grtruth.values.tolist())
my_dict=dict(My_result.values.tolist())
distinct=len(gt_dict)
are_error=0
aae_error=0
tp=0
fp=0


for item in my_dict:
    if item in gt_dict:
        are_error+=abs(my_dict[item]-gt_dict[item])/my_dict[item]
        aae_error+=abs(my_dict[item]-gt_dict[item])
        if my_dict[item] == gt_dict[item]:
            tp+=1
        else:
            fp+=1
    else:
        item_col,item_row=position(Tail(item,1))
        are_error+=abs(Sketch[item_row][item_col]-gt_dict[item])/Sketch[item_row][item_col]
        aae_error+=abs(Sketch[item_row][item_col]-gt_dict[item])
        
ARE=are_error/distinct
AAE=aae_error/distinct
print("Find:{}, TP:{}, FP:{}".format(len(gt_set & my_set),tp,fp))
print("ARE: {}".format(ARE))
print("AAE: {}".format(AAE))