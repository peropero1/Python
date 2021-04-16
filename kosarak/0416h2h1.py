
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
    width,depth=get_width_depth()
    col,row=position(element)
    head[row].count-=e_max.count
        # total_count-=element.count
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
    width,depth=get_width_depth()
    hash1=spookyhash.hash32(bytes(str(element.ID),encoding='utf-8'))
        # input: byte
        # output:unsigned- 32 bit int
    hash2=mmh3.hash(str(hash1), signed=False)
    #hash2=mmh3.hash(element.ID, signed=False)
        # input: str
        # output: unsigned- 32 bit int
    col=hash2 % width
    row=hash1 % depth
    return col,row 
    
# ==========================main=========================    

filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
depth=64
width=1024
size=1024

start=time.time()

Sk_head=[Head(0) for j in range(depth)]
Sketch=np.zeros((depth,width),dtype='int32')
e_max=Tail('',0)
Top=[]

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
            #print("read {}-th element:{}".format(income,e))
            item=Tail(e,1)            
            index=find(item,Top)
            if index<0:
                if len(Top)<size:
                    Top.append(item)
                else:
                    UpdateSk(item,Sk_head,Sketch)
            else:
                Top[index].count+=1                
                if index==0 or Top[index].count< Top[index-1].count:
                    pass
                else:
                    Top.sort(key=operator.attrgetter('count'),reverse=True)                
        if e_max.count>Top[-1].count:
            BringBack(Top[-1],Sk_head,Sketch)
            Top.sort(key=operator.attrgetter('count'),reverse=True)
            #print('Top after BringBack: \n\t{}'.format(Top)) 

end=time.time()
print("Top-{},Sketch:{}*{}".format(size,depth,width))
print("Execution time:{:8.3f} seconds.".format(end-start))
print("Total memory {} bytes=".format(sys.getsizeof(Top)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*depth),end='')
print("Top:{} bytes, Sketch:{} bytes, Sketch_head:{} bytes.".format(sys.getsizeof(Top),Sketch.nbytes,sys.getsizeof(Sk_head[0])*depth))

'''
print("TOP[20]:\n{}".format(Top[:20]))
print("e_max:{}".format(e_max))
for i in range(len(Sketch)):
    print("Sk[{}]:{},{}".format(i,Sk_head[i],Sketch[i]))
print('')

'''
#====================Top to csv=============================
templi=[[i.ID,i.count] for i in Top]
df=pd.DataFrame(templi,columns=['ID', 'Count'])
path='..\\result\\kosarak\\'
name="My_kosarak_distinct"+'_'+str(size)+'_'+str(depth)+'_'+str(width)
final=name+".csv"
df.to_csv(path+final,index=False)

# ====================precision====================
groundtruth='kosarak_ground_truth.csv'
grtruth=pd.read_csv(os.path.join(path,groundtruth))
    # ground truth of whole data set
My_result=pd.read_csv(os.path.join(path,final))
    # ground truth of Top

# precision
gt_set=set(grtruth['Element'][:size])
my_set=set(My_result['ID'])
precision=len(gt_set & my_set)/len(my_set)
    # &: set 交集運算
print("Precision: {:8.4f}".format(precision))

# ====================ARE/AAE of Top====================
gt_li=grtruth.values.tolist()[:size]
top_li=My_result.values.tolist()
ID=[j[0] for j in gt_li]
top_are=0
top_aae=0
for item in top_li:
    if item[0] in ID:
        index=ID.index(item[0])
        top_are+=abs(gt_li[index][1]-item[1])/gt_li[index][1]
        top_aae+=abs(gt_li[index][1]-item[1])
top_are=top_are/size
top_aae=top_aae/size
# print(top_are,top_aae)

# ====================ARE/AAE of all====================
# ARE/AAE
gt_dict=dict(grtruth.values.tolist())
top_dict=dict(My_result.values.tolist())
distinct=len(gt_dict)
    # cardinality of all incoming elements
row_cardinality=[len(i.distinct) for i in Sk_head]

all_are_error=0
all_aae_error=0
tp=0
fp=0

for item in gt_dict:
    if item in top_dict:
        # item in Top
        all_are_error+=abs(top_dict[item]-gt_dict[item])/gt_dict[item]
        all_aae_error+=abs(top_dict[item]-gt_dict[item])
        if top_dict[item]==gt_dict[item]:
            tp+=1
        else:
            fp+=1
    else:
        # item in Sketch
        item_col,item_row=position(Tail(item,1))
        ratio=width/row_cardinality[item_row]
        all_are_error+=abs(Sketch[item_row][item_col]*ratio-gt_dict[item])/gt_dict[item]
            # 此dataset暫無count為0的情況
        all_aae_error+=abs(Sketch[item_row][item_col]*ratio-gt_dict[item])

all_ARE=all_are_error/distinct
all_AAE=all_aae_error/distinct
print("Find:{}, TP:{}, FP:{}".format(len(gt_set & my_set),tp,fp))
print("Top_ARE: {:8.6f}".format(top_are))
print("Top_AAE: {:8.6f}".format(top_aae))
print("all_ARE: {:8.6f}".format(all_ARE))
print("all_AAE: {:8.6f}".format(all_AAE))

# ====================Cover result into a dataframe====================
sketch_size=str(depth)+'*'+str(width)
temp=sys.getsizeof(Top)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*depth
memory_usage=str(temp)+' bytes ='+'Top:'+str(sys.getsizeof(Top))+'+ Sketch:'+str(Sketch.nbytes)+'+ Sk_head:'+str(sys.getsizeof(Sk_head[0])*depth)

result_df=pd.DataFrame(columns=['Top-k',
                                'Sketch',
                                'Total memory',
                                'Exe_time',
                                'Find',
                                'Precision',
                                'ARE-Top',
                                'AAE-Top',
                                'ARE-all',
                                'AAE-all'])
output_dict={
    'Top-k':size,
    'Sketch':sketch_size,
    'Total memory':memory_usage,
    'Exe_time':float('{:.3f}'.format(end-start)),
    'Find':"Find:{}, TP:{}, FP:{}".format(len(gt_set & my_set),tp,fp),
    'Precision':float("{:8.4f}".format(precision)),
    'ARE-Top':float('{:8.6f}'.format(top_are)),
    'AAE-Top':float('{:8.6f}'.format(top_aae)),
    'ARE-all':float('{:8.6f}'.format(all_ARE)),
    'AAE-all':float('{:8.6f}'.format(all_AAE))}
result_df=result_df.append(output_dict,ignore_index=True)
file="My_kosarak_distinct_ratio"+'_'+str(size)+'_'+str(depth)+'_'+str(width)+'_.csv'
result_df.to_csv(file,index=False)
result_df