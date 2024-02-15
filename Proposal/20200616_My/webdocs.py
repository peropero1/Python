from Node import DS
from Tools import Func
from Tools import Config
import pandas as pd
import numpy as np
import os
import time
import operator
import sys

import re

def main():
    # set dataset and ground truth file path
    filepath='..\dataset\webdocs'
    pattern='out_.*'
    r=re.compile(pattern)
    filelist=list(filter(r.match,os.listdir(filepath)))    
        # dataset file list

    gr_file_name='webdocs_ground_truth.csv'        
    gr_path=os.path.join(filepath,gr_file_name)
        # ground truth path

    # Top and Sketch parameter config
    w=1024
    d=1024
    size=4096
    Config.Set_default(w,d,size)
        # set width, depth, size of Sk, random seed of hash,e_max
        
    # Initialize Top, Sketch and Sk_head
    Sk_head=[DS.Head(0) for j in range(Config.depth)]
    Sketch=np.zeros((Config.depth,Config.width),dtype='int32')
    Top_dict=dict()
    e_min=DS.Tail("",1)
    
    start=time.time()
    for datafile in filelist[:]:
        src_data=os.path.join(filepath,datafile)
        with open(src_data,'r') as file:
            while True:
                e=file.readline().strip('\n')
                if not e:
                    print("EOF")
                    break
                else:    
                    item=DS.Tail(e,1)
                    if Top_dict.get(item.ID):
                        # e in Top
                        Top_dict[item.ID]+=1
                    else:
                        if len(Top_dict)<Config.size:
                            Top_dict[item.ID]=1
                        else:
                            Func.UpdateSk(item,Sk_head,Sketch)
                if Config.e_max.count>e_min.count:
                    min_ele = min(Top_dict, key=Top_dict.get)
                        # 找dict中的最小key元素
                    e_min=DS.Tail(min_ele,Top_dict[min_ele])
                    Func.BringBack(e_min,Top_dict,Sk_head,Sketch)
    end=time.time()
    print("Top-{},Sketch:{}*{}".format(Config.size,Config.depth,Config.width))
    print("Execution time:{:8.3f} seconds.".format(end-start))
    Top_dict=dict(sorted(Top_dict.items(), key=lambda item: item[1],reverse=True))

    # Element-Precision
    tp_set,precision=Func.Get_precision(gr_path,Top_dict)

    # Count ARE/AAE
    startx=time.time()
    top_are,top_aae,all_are,all_aae,tp,fp=Func.Get_ARE_AAE(gr_path,Top_dict,Sk_head,Sketch,2)
    endx=time.time()
    print("Find:{}, TP:{}, FP:{}".format(len(tp_set),tp,fp))
    print("Top_ARE: {:8.6f}".format(top_are))
    print("Top_AAE: {:8.6f}".format(top_aae))
    print("all_ARE: {:8.6f}".format(all_are))
    print("all_AAE: {:8.6f}".format(all_aae))
    print("Estimate time:{:8.3f} seconds.".format(endx-startx))

    startx=time.time()
    top_are,top_aae,all_are,all_aae,tp,fp=Func.Get_ARE_AAE(gr_path,Top_dict,Sk_head,Sketch,3)
    endx=time.time()
    print("Find:{}, TP:{}, FP:{}".format(len(tp_set),tp,fp))
    print("Top_ARE: {:8.6f}".format(top_are))
    print("Top_AAE: {:8.6f}".format(top_aae))
    print("all_ARE: {:8.6f}".format(all_are))
    print("all_AAE: {:8.6f}".format(all_aae))
    print("Estimate time:{:8.3f} seconds.".format(endx-startx))    

    startx=time.time()
    top_are,top_aae,all_are,all_aae,tp,fp=Func.Get_ARE_AAE(gr_path,Top_dict,Sk_head,Sketch,4)
    endx=time.time()
    print("Find:{}, TP:{}, FP:{}".format(len(tp_set),tp,fp))
    print("Top_ARE: {:8.6f}".format(top_are))
    print("Top_AAE: {:8.6f}".format(top_aae))
    print("all_ARE: {:8.6f}".format(all_are))
    print("all_AAE: {:8.6f}".format(all_aae))
    print("Estimate time:{:8.3f} seconds.".format(endx-startx))        
if __name__=='__main__':
    main()