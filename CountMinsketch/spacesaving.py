import sys
import os
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

def find(e,element_list):
    try:
        index = [ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index  
    
    
start=time.time()

filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)

size=1024
Top=[]
#item_count=100000

with open(src_data,'r') as file:
    while True:
        element=file.readline().strip('\n')
        if not element:
            print('EOF')
            break
        else:
            item=Tail(element,1)
            #item_count-=1
            # print("read {}th element: {}".format(item_count,element))
            if len(Top)==0:
                Top.append(item)
            else:
                index=find(item,Top)
                if index<0:
                    if len(Top)<size:
                        Top.append(item)
                    else:
                        # replace last element with count 
                        Top[-1].ID=item.ID
                        Top[-1].count+=1
                else:
                    Top[index].count+=1
            Top.sort(key=operator.attrgetter('count'),reverse=True)

end=time.time()
print(Top[:20],len(Top))
print("Total memory {0} bytes :Top-{1} with size {0} bytes.".format(sys.getsizeof(Top),size))
print("Execution time:{} seconds.".format(str(end-start)))


#　conver Top into df    
templi=[]
for i in Top:
    templi.append([i.ID,i.count])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("..\\result\\kosarak\\SS_class_kosarak.csv",index=False)
df.head(20)
