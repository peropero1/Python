import mmh3
import random
import Config
import HG
import operator
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

def position(e):
    # type(e): Node
    hash1=mmh3.hash(e.ID,seed=Config.seed[0], signed=False)
    hash2=mmh3.hash(e.ID,seed=Config.seed[1], signed=False)

    x=hash1 % Config.size
    y=hash2 % Config.light
    return x,y     

def find(e,element_list):
    # type(e): Node()
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index

def Decay(element):
    random.seed()
    return int(random.randint(0,1)% int(pow(Config.exponential_decay,element.count)))

def InsertHG(e,HG_table):
    # type(e): Node()
    b_index,l_index=position(e)
        # bucket index & light part index
    n_index=find(e,HG_table[b_index].heavy_part)
        # node index
    if n_index<0:
        # not found in HG_list[i].heavy[j]
        if len(HG_table[b_index].heavy_part)<Config.heavy:
            # HG_table[b_index] is not full
            HG_table[b_index].heavy_part.append(e)
            n_index=len(HG_table[b_index].heavy_part)-1
        else:
            #exponential decay
            if HG_table[b_index].heavy_part[-1].count-Decay(HG_table[b_index].heavy_part[-1])==0:
                HG_table[b_index].heavy_part[-1].ID=e.ID
                HG_table[b_index].heavy_part[-1].count=1
            else:
                # Light part insert
                HG_table[b_index].light_part[l_index]+=1
    else:
        HG_table[b_index].heavy_part[n_index].count+=1
        if n_index==0 or HG_table[b_index].heavy_part[n_index].count< HG_table[b_index].heavy_part[n_index-1].count:
            pass
        else:
            HG_table[b_index].heavy_part.sort(key=operator.attrgetter('count'),reverse=True)
    return HG_table

def HG_Query(e,HG_table):
    count=0
    item=HG.Node(e,1)
    b_index,l_index=position(item)
        # bucket index & light part index
    n_index=find(item,HG_table[b_index].heavy_part)
    if n_index<0:
        count=HG_table[b_index].light_part[l_index]
    else:
        count=HG_table[b_index].heavy_part[n_index].count
    return count

def Get_precision(ground_truth_path,result_dict,topk):
    grtruth=pd.read_csv(ground_truth_path)
    grtruth['Element'] = grtruth['Element'].astype(str)
    gt_set=set(grtruth['Element'][:topk])
    my_set=set(result_dict.keys())
    tp_set=gt_set & my_set
    precision=len(tp_set)/topk
    return tp_set,precision

def Get_ARE_AAE(ground_truth_path,result_list,Top_dict):
    # Top_dict is sorted by count 
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    grtruth['Element'] = grtruth['Element'].astype(str)
        # ID transfer to str
    gt_dict=dict(grtruth.values.tolist())
        # all ground truth
    distinct=len(gt_dict)
    
    heavy_are=0
    heavy_aae=0
    all_are=0
    all_aae=0
    
    # ARE/AAE of heavy_part element
    for item in Top_dict:
        #estimate=Func.HG_Query(item,result_list)
        heavy_are+=abs(Top_dict[item]-gt_dict[item])/gt_dict[item]
        heavy_aae+=abs(Top_dict[item]-gt_dict[item])
    #print('heavy_are:{:8.3f},heavy_aae:{:8.3f}'.format(heavy_are,heavy_aae))
    
    # all non-heavy element
    [gt_dict.pop(key) for key in Top_dict]
        # pop out heavy item in result
    for item in gt_dict:
        estimate=HG_Query(item,result_list)
        all_are+=abs(estimate-gt_dict[item])/gt_dict[item]
        all_aae+=abs(estimate-gt_dict[item])
    
    all_are=all_are/(distinct-len(Top_dict))
    all_aae=all_aae/(distinct-len(Top_dict))
    #print('all_are:{:8.3f},all_aae:{:8.3f}'.format(all_are,all_aae))
    return heavy_are,heavy_aae,all_are,all_aae

def Get_ground_truth(ground_truth_path,topk=None):
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    grtruth['Element'] = grtruth['Element'].astype(str)
        # sorted, not use set.
    gt_dict=dict(grtruth[:topk].values.tolist())
        # top-k e.ID only    
    return gt_dict


def Plot_topk_compare(ground_truth_path,result_dict,method):
    topk=Config.size*Config.heavy
    gt_dict=Get_ground_truth(ground_truth_path,topk)
    gr_count=[]
    my_count=[]
    tp_list=[]
    
    # set max y ticks
    max_element=max(gt_dict, key=gt_dict.get)
    y_max=int(np.log2(gt_dict[max_element]))
    
    for item in gt_dict:
        if item in result_dict:
            tp_list.append(item)
            gr_count.append(gt_dict[item])
            my_count.append(result_dict[item])
    indexli=[i for i in range (len(tp_list))]
    plt.figure(figsize=[14,8])
    plt.xticks([j for j in range(0,len(tp_list),50)])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-{}/{}'.format(len(tp_list),topk))
    plt.ylabel('Count, log scale')

    my_line,=plt.plot(indexli,np.log2(my_count),'g.',label='Heavy Guardian',alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(gr_count),'r.',label='GroundTruth',alpha=0.3)

    plt.legend(handles=[gr_line,my_line],loc='best')
    plt.show()
    
    
def Plot_all_compare(gt_dict,result_dict,method):
    #gt_dict=Get_ground_truth(ground_truth_path)
    #result_dict=dict(sorted(result_dict.items(), key=lambda item: item[1],reverse=True))

    gr_count=[]
    my_count=[]
    for item in gt_dict:
        if item in result_dict:
            gr_count.append(gt_dict[item])
            my_count.append(result_dict[item])
        else:
            my_count.append(1)
    
    # set max y ticks
    max_element=max(gt_dict, key=gt_dict.get)
    y_max=int(np.log2(gt_dict[max_element]))
    
    # Plot Figure
    indexli=[i for i in range (len(gt_dict))]
    
    # Comparison
    plt.figure(figsize=[20,8])
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-k Element sorted by count')    
    plt.ylabel('Count, log scale')
    my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label=method,alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(list(gt_dict.values())),'r.',label='GroundTruth',alpha=0.3)
    plt.legend(handles=[gr_line,my_line],loc='best')
    plt.show()
    
    
    # Ground Truth
    plt.figure(figsize=[20,8])
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    #plt.xlabel('Top-{}/{}'.format(len(tp_list),Config.topk))
    plt.xlabel('Top-k Element sorted by count')    
    plt.ylabel('Count, log scale')
    #my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label='Cyclic Sketch',alpha=0.5)
    gr_line,=plt.plot(indexli,np.log2(list(gt_dict.values())),'r.',label='GroundTruth',alpha=0.3)

    #plt.legend(handles=[gr_line,my_line],loc='best')
    plt.legend(handles=[gr_line],loc='best')
    plt.show()
    
    # Algo result
    plt.figure(figsize=[20,8])
    #plt.xlabel('Top-{}/{}'.format(len(tp_list),Config.topk))
    plt.xticks([j for j in range(0,len(gt_dict),int(len(gt_dict)/20))])
    plt.yticks([j for j in range(0,y_max)])
    plt.xlabel('Top-k Element')    
    plt.ylabel('Count, log scale')
    my_line,=plt.plot(indexli,np.log2(list(result_dict.values())),'g.',label=method,alpha=0.5)
    plt.legend(handles=[my_line],loc='best')
    plt.show()
    
    #return gr_count,my_count    