# Count-Min sketch with built-in index search
# Top-1024+ 4*1024 CMS
# Total memory 9432 bytes :Top-1024 with size 9328 bytes+ CMS with size 104 bytes.
# Execution time:319.18891406059265 seconds.
# Find:339,TP:0,FP:339

import sys
import os
import time
from probables import (CountMinSketch)
import pandas as pd

def find(e,Topk):
    try:
        index = [ele for ele,i in Topk].index(e)
        return index
    except:
        index=-99
    return index

start=time.time()
filename='kosarak.dat'
filepath="..\\dataset\\"
src_data=os.path.join(filepath,filename)
topk=[]
size=1024
# item_count=10000
cms = CountMinSketch(width=1024, depth=4)

if os.path.exists(src_data):
    with open(src_data,'r') as file:
        while True:
            line=file.readline().strip('\n')
            if not line:
                print('EOF')
                break
            else:
                #item_count-=1
                # print("read {}th element: {}".format(item_count,element))
                cms.add(line)
                count=cms.check(line)
                if len(topk)==0:
                    topk.append([line,count])
                else:
                    index=find(line,topk)
                    if index<0:
                        #  element not in topk
                        if len(topk)<size:
                            topk.append([line,count])
                        else:
                            topk[-1][0]=line
                            topk[-1][1]=count
                    else:
                        topk[index][1]=count
                topk=sorted(topk,key = lambda topk:topk[1],reverse=True)
                    
    end=time.time()
    print(topk[:20],len(topk))
    print("Total memory {3} bytes :Top-{0} with size {1} bytes+ CMS with size {2} bytes.".format(len(topk),sys.getsizeof(topk),sys.getsizeof(cms),sys.getsizeof(cms)+sys.getsizeof(topk)))
    print("Execution time:{} seconds.".format(str(end-start)))
else:
    print("file doesn't exist")
#　conver Top into df    
templi=[]
for i in topk:
    templi.append([i[0],i[1]])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("..\\result\\kosarak\\CM_kosarak.csv",index=False)
df.head(50)
