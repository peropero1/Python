# space saving caida_0, StreamSummary with 1024 elements, full test
# class implement


import sys
import time
import operator
import pandas as pd

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

start=time.time()
'''
datapath=r'X:\\NTU\\ML-sketch\\dataset\\caida2016\\'
datali=os.listdir(datapath)[0]
'''
src_data='caida_0.dat'
size=1024
Top=[]
item_count=0
# Space-Saving

with open(src_data,'rb') as file:
    while True:
        element=str(file.read(13))
        if len(element)<13:
            print('EOF')
            break
        else:
            item_count+=1
            print("read {}th element: {}".format(item_count,element))
            if len(Top)==0:
                Top.append(Tail(element,1))
            else:
                found=False
                for i in range(len(Top)):
                    if Top[i].ID==element:
                        found=True
                        Top[i].add_count()
                        break
                if not found:
                    if len(Top)<size:
                        Top.append(Tail(element,1))
                    else:
                        Top[-1].ID=element
                        Top[-1].add_count()
                # Top= sorted(Top, key=operator.attrgetter('count'),reverse=True)
                # non-inplace sort
                Top.sort(key=operator.attrgetter('count'),reverse=True)
                    # inplce sort
end=time.time()
print(Top[:50],len(Top))
print("Top-{} with size {} bytes.".format(len(Top),sys.getsizeof(Top)))
print("Execution time:{} seconds.".format(str(end-start)))

#　conver Top into df    
templi=[]
for i in Top:
    templi.append([i.ID,i.count])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("SpaceSaving_caida_0_distinct_count.csv",index=False)
df.head(50)