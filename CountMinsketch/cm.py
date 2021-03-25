# count-min sketch webdocs, top-512, full read
import sys
import os
import time
from probables import (CountMinSketch)

start=time.time()
topk=[]
size=512
item_count=0
cms = CountMinSketch(width=1024, depth=4)
'''
datapath=r'X:\\NTU\\ML-sketch\\dataset\\caida2016\\'
datali=os.listdir(datapath)[0]
'''
src_data='caida_0.dat'


# if os.path.exists(os.path.join(datapath,datali)):
if os.path.exists(src_data):
    with open(src_data,'rb') as file:
        while True:
            line=str(file.read(13))
            if len(line)<13:
                print('EOF')
                break
            else:
                item_count+=1
                print("read {}th element: {}".format(item_count,line))
                cms.add(line)
                count=cms.check(line)
                if len(topk)==0:
                    topk.append([line,count])
                else:
                    find=False
                    for i in range(len(topk)):
                        if line==topk[i][0]:
                            topk[i][1]=count
                            find=True
                            break
                    if find==False:
                        if len(topk)<size:
                            topk.append([line,count])
                        else:
                            topk.append([line,count])
                            topk=sorted(topk,key = lambda topk:topk[1],reverse=True)
                            topk.pop()
                topk=sorted(topk,key = lambda topk:topk[1],reverse=True)
                    
    end=time.time()
    print(topk[:50],len(topk))
    print("Total memory {3} bytes :Top-{0} with size {1} bytes+ CMS with size {2} bytes.".format(len(topk),sys.getsizeof(topk),sys.getsizeof(cms),sys.getsizeof(cms)+sys.getsizeof(topk)))
    print("Execution time:{} seconds.".format(str(end-start)))
else:
    print("file doesn't exist")

#　conver Top into df    
templi=[]
for i in topk:
    templi.append([i[0],i[1]])

df=pd.DataFrame(templi,columns=['ID', 'Count'])
df.to_csv("CM_caida_0_distinct_count.csv",index=False)
df.head(50)