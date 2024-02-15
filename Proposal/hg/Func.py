import mmh3
import random
import Config
import HG
import operator
import pandas as pd


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

def Topk_Precision(ground_truth_path,result):
    gt_df=pd.read_csv(ground_truth_path)
    gt_df['Element'] = gt_df['Element'].astype(str)
    gt_set=set(gt_df['Element'][:Config.size*Config.heavy])

    result_set=set(result.keys())
    tp_set=gt_set & result_set
    return (len(tp_set)/len(result_set))

def Count_ARE_AAE(ground_truth_path,result_list,result_dict):
    gt_df=pd.read_csv(ground_truth_path)
    gt_df['Element'] = gt_df['Element'].astype(str)
    gt_dict=dict(gt_df.values.tolist())
    distinct=len(gt_dict)
    
    heavy_are=0
    heavy_aae=0
    all_are=0
    all_aae=0
    
    # ARE/AAE of heavy_part element
    for item in result_dict:
        estimate=HG_Query(item,result_list)
        #print('result:{},truth:{}'.format(result_dict[item],gt_dict[item]))
        heavy_are+=abs(estimate-gt_dict[item])/gt_dict[item]
        heavy_aae+=abs(estimate-gt_dict[item])
    print('heavy_are:{:8.3f},heavy_aae:{:8.3f}'.format(heavy_are,heavy_aae))
    
    # ARE/AAE of others no heavy
    [gt_dict.pop(key) for key in result_dict]
        # pop out heavy item in result
    for item in gt_dict:
        estimate=HG_Query(item,result_list)
        all_are+=abs(estimate-gt_dict[item])/gt_dict[item]
        all_aae+=abs(estimate-gt_dict[item])
    
    all_are=all_are/(distinct-len(result_dict))
    all_aae=all_aae/(distinct-len(result_dict))
    print('all_are:{:8.3f},all_aae:{:8.3f}'.format(all_are,all_aae))
    return heavy_are,heavy_aae,all_are,all_aae


        
        
    