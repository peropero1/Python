
import sys
import os
import time
import operator
import pandas as pd
import re

class Node():
    def __init__(self,count=0):
        self.count=count
    def add_count(self,count=1):
        self.count+=count
    def __str__(self):
        return 'ID: {}, count: {}'.format(self.ID,self.count)
    def __repr__(self):
        return ''

class Head(Node):
    def __init__(self):
        super().__init__()
        self.distinct = hyperloglog.HyperLogLog(0.01)
    def __str__(self):
        return 'total count: {}, distinct element: {}'.format(self.count,len(self.distinct))
    def __repr__(self):
        return '[count: {}, distinct: {}]'.format(self.count,len(self.distinct))

class Tail(Node):
    def __init__(self,ID,count):
        self.ID = ID
        super().__init__(count)
    def __str__(self):
        return 'ID: {}, count: {}'.format(self.ID,self.count)
    def __repr__(self):
        return "'{}', count: {}".format(self.ID,self.count)

def find(e,element_list):
    try:
        index = [ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index  


# ==========================main========================= 
# path='X:\\NTU\\ML-sketch\\dataset\\Webpage\\webdocs'
datapath='..\dataset\webdocs'
pattern='out_.*'
r=re.compile(pattern)
filelist=list(filter(r.match,os.listdir(datapath)))

size=512
Top=[]
#item_count=100000

start=time.time()
for datafile in filelist[:1]:
    src_data=os.path.join(datapath,datafile)
    with open(src_data,'r') as file:
        while True:
            e=file.readline().strip('\n')
            if not e:
                print('EOF')
                break
            else:
                item=Tail(e,1)
                #item_count-=1
                # print("read {}th element: {}".format(item_count,element))
                if len(Top)==0:
                    Top.append(item)
                else:
                    index=find(item,Top)
                    if index<0:
                        # e not in Top
                        index=len(Top)-1
                        if len(Top)<size:
                            Top.append(item)
                        else:
                            # replace last element with count 
                            Top[-1].ID=item.ID
                            Top[-1].count+=1
                    else:
                        Top[index].count+=1
                    if index==0 or Top[index].count< Top[index-1].count:
                        pass
                    else:
                        Top.sort(key=operator.attrgetter('count'),reverse=True)                      
end=time.time()

#print(Top[:20],len(Top))
print("Top-{}".format(size))
print("Total memory {0} bytes=Top-{1} with size {0} bytes.".format(sys.getsizeof(Top),size))
print("Execution time:{:8.3f} seconds.".format(end-start))


#====================Top to csv=============================
templi=[[i.ID,i.count] for i in Top]
df=pd.DataFrame(templi,columns=['ID', 'Count'])
df=df.sort_values(by='Count',ascending=False)
name="SS_webdocs_Top-"+str(size)+'_'+'.csv'
df.to_csv(os.path.join(r'..\result',name),index=False)
    #儲存Top的結果

#====================result compare=============================
gr_path='..\dataset\webdocs'
gr_file_name='webdocs_ground_truth.csv'
grtruth=pd.read_csv(os.path.join(gr_path,gr_file_name))
SS_result=pd.read_csv(os.path.join(r'..\result',name))

# precision
gt_set=set(grtruth['Element'][:size])
    # Top-k of ground truth
my_set=set(SS_result['ID'])
tp_set=gt_set & my_set
precision=len(tp_set)/len(my_set)
    # &: set 交集運算
print("Precision: {:8.4f}".format(precision))

# ====================ARE/AAE for top and all====================
gt_dict=dict(grtruth.values.tolist()[:size])
    # SS只能和Top-k比
my_dict=dict(SS_result.values.tolist())
distinct=len(gt_dict)
top_are=0
top_aae=0
tp=0
fp=0

startx=time.time()
for item in gt_dict:
    # len(gt_dict)=512
    if item in my_dict:
        # ARE/AAE for Top
        top_are+=abs(my_dict[item]-gt_dict[item])/gt_dict[item]
        top_aae+=abs(my_dict[item]-gt_dict[item])
        tp+=1
    else:
        fp+=1
endx=time.time()

ARE=top_are/distinct
AAE=top_aae/distinct
print("Find:{}, TP:{}, FP:{}".format(len(tp_set),tp,fp))
print("ARE: {:8.6f}".format(ARE))
print("AAE: {:8.6f}".format(AAE))
