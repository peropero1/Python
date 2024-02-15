import mmh3
import Config
import os
import time
import random
import operator
import sys
from memory_profiler import profile

class Node():
    def __init__(self,ID='Null',count=0):
        self.count=count
        self.ID=str(ID)
    def __str__(self):
        return '({},{})'.format(self.ID,self.count)
    def __repr__(self):
        return '({},{})'.format(self.ID,self.count)
    
class HeavyGuardian():
    def __init__(self,light_size=0):
        self.heavy=[]
        self.light=[0]*light_size
    def __str__(self):
        return '[H:{}L:{}]\n'.format(self.heavy,self.light)
    def __repr__(self):
        return '[H:{}L:{}]\n'.format(self.heavy,self.light)


def position(e):
    hash1=mmh3.hash(e.ID,seed=Config.seed[0], signed=False)
    hash2=mmh3.hash(e.ID,seed=Config.seed[1], signed=False)
    
    x=hash1 % Config.size
    y=hash2 % Config.light
    return x,y     

def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index

def Decay(element):
    random.seed()
    return int(random.randint(0,1)% int(pow(Config.exponential_decay,element.count)))


# ==========================main=========================    
@profile
def main():
    filename='kosarak.dat'
    dataset='kosarak'
    filepath=r"..\dataset\kosarak"
    src_data=os.path.join(filepath,filename)


    heavy_size=32
    light_size=32
    size=128
    # 128*32=4096, top 4096+sketch 128*32
    b=1.08
    Config.Set_default(heavy_size,light_size,size,b)

    HG_list=[HeavyGuardian(Config.light) for _ in range(Config.size)]
        # error reference by using [HG()]*size

    item_count=50

    start=time.time()
    with open(src_data,'r') as file:
        while True:
            e=file.readline().strip('\n')
            #print("\nread {}".format(e))
            if not e:
                print('EOF')
                break
            else:
                # Heavy part insert
                #item_count-=1

                item=Node(str(e),1)
                h_index,l_index=position(item)
                    # bucket index & light part index
                n_index=find(item,HG_list[h_index].heavy)
                    # node index

                if n_index<0:
                    # not found in HG_list[i].heavy[j]
                    if len(HG_list[h_index].heavy)<Config.heavy:
                        # HG_list[h_index] is not full
                        HG_list[h_index].heavy.append(item)
                        n_index=len(HG_list[h_index].heavy)-1
                    else:
                        #exponential decay
                        if HG_list[h_index].heavy[-1].count-Decay(HG_list[h_index].heavy[-1])==0:
                            HG_list[h_index].heavy[-1].ID=item.ID
                            HG_list[h_index].heavy[-1].count=1
                        else:
                            # Light part insert
                            HG_list[h_index].light[l_index]+=1
                else:
                    HG_list[h_index].heavy[n_index].count+=1
                    if n_index==0 or HG_list[h_index].heavy[n_index].count< HG_list[h_index].heavy[n_index-1].count:
                        pass
                    else:
                        HG_list[h_index].heavy.sort(key=operator.attrgetter('count'),reverse=True)                       
    end=time.time()
    print("Execution time:{:8.3f} seconds.".format(end-start))
    #print("Total memory {} bytes=".format(sys.getsizeof(Top)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*Config.depth),end='')
    print(HG_list)

if __name__=='__main__':
    main()