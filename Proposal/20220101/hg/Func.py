import mmh3
import random
import Config
import HG
import operator
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import sys

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
    try:
        d=random.randint(0,sys.maxsize) % int(pow(Config.exponential_decay,element.count))
    except:
        d=1
    return d

def InsertHG(e,HG_table):
    # type(e): Node()
    b_index,l_index=position(e)
        # bucket index & light part index
    n_index=find(e,HG_table[b_index].heavy_part)
        # node index
    if n_index<0:
        # not found in HG_list[i].heavy
        if len(HG_table[b_index].heavy_part)<Config.heavy:
            # HG_table[b_index] is not full
            HG_table[b_index].heavy_part.append(e)
            n_index=len(HG_table[b_index].heavy_part)-1
        else:
            # heavy part is full
            if not(Decay(HG_table[b_index].heavy_part[-1])):
                HG_table[b_index].heavy_part[-1].count-=1
                if HG_table[b_index].heavy_part[-1].count<=0:
                    # send weakest guardian to lightpart                    
                    wg_bindex,wg_lindex=position(HG_table[b_index].heavy_part[-1])
                    HG_table[wg_bindex].light_part[wg_lindex]+=1
                    
                    # replace weakest guardian
                    HG_table[b_index].heavy_part[-1].ID=e.ID
                    HG_table[b_index].heavy_part[-1].count=1
            else:
                # Light part insert
                HG_table[b_index].light_part[l_index]+=1
    else:
        # e is in HG_list[i].heavy[j]
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
    grdf=pd.read_csv(ground_truth_path)
    grdf['Element']=grdf['Element'].astype('str')
    grdf=grdf[:topk]
                                           
    result_df=pd.DataFrame(result_dict.items(),columns=['Element','Count'])
    result_df=result_df[:topk]
    
    tp_df=grdf.merge(result_df,how='inner',on='Element',suffixes=('_t', '_r'))
    tp_set=set(tp_df['Element'])
    precision=len(tp_set)/topk
    return tp_set,precision

def Get_Top_ARE_AAE(ground_truth_path,result_dict):
    # Top_dict is sorted by count 
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    grtruth['Element'] = grtruth['Element'].astype(str)
        # ID transfer to str
    gt_df=grtruth[:Config.topk]
    result_df=pd.DataFrame(result_dict.items(),columns=['Element','Count'])
    top_df=gt_df.merge(result_df,how='inner',on='Element',suffixes=('_t', '_r'))
        # true top-k element
    # Top-k ARE/AAE
    hare=0
    haae=0
    for item in top_df['Element']:
        true_c=top_df.loc[top_df['Element']==item,'Count_t'].iloc[0]
        est_c=top_df.loc[top_df['Element']==item,'Count_r'].iloc[0]
        hare+=abs(true_c-est_c)/true_c
        haae+=abs(true_c-est_c)
    return hare/len(top_df),haae/len(top_df)
    
    
def Get_ARE_AAE(ground_truth_path,result_list,Top_dict):
    # Top_dict is sorted by count 
    # =============================Read Ground Truth=============================
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    grtruth['Element'] = grtruth['Element'].astype(str)
        # ID transfer to str
    gt_dict=dict(grtruth.values.tolist())
        # all ground truth
    gr_top=grtruth[:Config.topk]
        #top k
    distinct=len(gt_dict)
    # ============================= result=============================    
    result=pd.DataFrame(Top_dict.items(),columns=['Element','Count'])
    result=result[:Config.topk]
    tp_heavy=gr_top.merge(result,how='inner',on='Element',suffixes=('_t', '_r'))
        # TP in Heavy
    # ============================= ARE for TP in Heavy=============================           
    # Heavy part ARE/AAE
    hare,haae=Get_HH_ARE_AAE(tp_heavy)
    # ============================= ARE for Others=============================     
    all_are=0
    all_aae=0
    tp_set=set(tp_heavy['Element'])
    for item in gt_dict:
        estimate=HG_Query(item,result_list)
        all_are+=abs(estimate-gt_dict[item])/gt_dict[item]
        all_aae+=abs(estimate-gt_dict[item])
    
    all_are=all_are/(distinct-len(tp_set))
    all_aae=all_aae/(distinct-len(tp_set))
    #print('all_are:{:8.3f},all_aae:{:8.3f}'.format(all_are,all_aae))
    return hare,haae,all_are,all_aae

def Get_HH_ARE_AAE(diff_df):
    # diff_df: ['Element','Count_t','Count_r']
    are=0
    aae=0
    for item in diff_df['Element']:
        true_c=diff_df.loc[diff_df['Element']==item,'Count_t'].iloc[0]
        est_c=diff_df.loc[diff_df['Element']==item,'Count_r'].iloc[0]
        are+=abs(true_c-est_c)/true_c
        aae+=abs(true_c-est_c)    
    return are/len(diff_df),aae/len(diff_df)
    

def Get_ground_truth(ground_truth_path,topk=None):
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    grtruth['Element'] = grtruth['Element'].astype(str)
        # sorted, not use set.
    gt_dict=dict(grtruth[:topk].values.tolist())
        # top-k e.ID only    
    return gt_dict


def Plot_topk_compare(ground_truth_path,result_dict,method):
    #ground_truth_path:csv
    gt_df=pd.read_csv(ground_truth_path)
    gt_df['Element']=gt_df['Element'].astype('str')
    gt_df=gt_df[:Config.topk]
    
    
    result_df=pd.DataFrame(result_dict.items(),columns=['Element','Count'])
    result_df=result_df[:Config.topk]
    
    tp_df=gt_df.merge(result_df,how='inner',on='Element',suffixes=('_t', '_r'))

    # set max y ticks
    max_element=max(max(tp_df['Count_t']),max(tp_df['Count_r']))
    y_max=int(np.log2(max_element))     
    
    x_index=[i for i in range (len(tp_df))]
    #plt.figure()
    plt.figure(figsize=[12,8])
    #plt.xticks([j for j in range(0,len(tp_list),50)])
    plt.xticks([j for j in range(0,int(Config.topk*1.02),int(Config.topk/10))])
    plt.yticks([j for j in range(0,y_max+1)])
    plt.xlim(-int(Config.topk*0.02),int(Config.topk*1.02))
    plt.ylim(-1,y_max+1)
    plt.xlabel('Top-{}/{}'.format(len(tp_df),Config.topk))
    plt.ylabel('Count, log scale')
    
    #my_line,=plt.plot(indexli,np.log2(my_count),'g.',label=method,alpha=0.7)
    my_line,=plt.plot(x_index,np.log2(list(tp_df['Count_r'])),'g.',label=method,alpha=0.3)
    gr_line,=plt.plot(x_index,np.log2(list(tp_df['Count_t'])),'r.',label='GroundTruth',alpha=0.5)
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
    

def Plot_hh_compare(ground_truth_df,result_dict,method):
    #
    gt_dict=dict(ground_truth_df.values)
    tp_set=set(gt_dict.keys()) & set(result_dict.keys())
    gt_dict=dict(sorted(gt_dict.items(), key=lambda item: item[1],reverse=True))
    
    x_axis=[i for i in range(len(tp_set))]
    y1=[result_dict[item] for item in tp_set]
    y1.sort(reverse=True)
    y_my=np.log2(y1)
    y2=[gt_dict[item] for item in tp_set]
    y2.sort(reverse=True)    
    y_gt=np.log2(y2)

    ymax=np.log2(max(max(gt_dict.values()),max(result_dict.values())))
    ymin=np.log2(min(min(gt_dict.values()),min(result_dict.values())))
    plt.figure(figsize=[12,8])
    #plt.xticks([j for j in range(0,int(len(x_axis)*1.1),int(len(x_axis)*1.1/10))])
    #plt.yticks([j for j in range(ymin,ymax)])
    #plt.xlim(0,int(len(tp_set)*1.02))
    plt.xticks([i for i in range(0,int(len(gt_dict)*1.1),int(len(gt_dict)/10))])
    plt.xlim(-int(len(gt_dict)/20),int(len(gt_dict)*1.1))
    plt.ylim(ymin-1,ymax+1)
    plt.xlabel('HH-{} in {}'.format(len(tp_set),len(gt_dict)))
    plt.ylabel('Count, log scale')
    my_line,=plt.plot(x_axis,y_my,'g*',label=method,alpha=1,markersize=10)
    gr_line,=plt.plot(x_axis,y_gt,'ro',label='GroundTruth',alpha=0.8,markersize=4)

    plt.legend(handles=[gr_line,my_line],loc='best')
    plt.show()