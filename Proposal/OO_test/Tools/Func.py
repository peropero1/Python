from Node import DS
from Tools import Config
import pandas as pd
import os
import spookyhash
import mmh3
import sys


# ==========================Tools=========================  

def find(e,element_list):
    # return index of e in element_list
    try:
        index=[ele.ID for ele in element_list].index(e.ID)
    except:
        index=-99
    return index

def position(element):
    hash1=mmh3.hash(element.ID,seed=Config.seed[0], signed=False)
    hash2=mmh3.hash(element.ID,seed=Config.seed[1], signed=False)
    col=hash1 % Config.width
    row=hash2 % Config.depth
    return col,row 

def Top_to_csv(Top,dataset_name):
    templi=[[i.ID,i.count] for i in Top]
    df=pd.DataFrame(templi,columns=['ID', 'Count'])
    df=df.sort_values(by='Count',ascending=False)
    name="My_OO_"+dataset_name+"_Top"+'_'+str(Config.size)+'_'+str(Config.depth)+'_'+str(Config.width)+'.csv'
    # My_OO_kosarak_Top_size_d_w.csv" for algorithm result
    df.to_csv(os.path.join(r'..\result',name),index=False)
    print(name)
    return name
    
def Get_precision(ground_truth_path,result_path):
    #gr_truth,result: path of csv file
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    My_result=pd.read_csv(result_path)
        # Top-k of algorithm result
    # precision
    gt_set=set(grtruth['Element'][:Config.size])
        # e.ID only
    my_set=set(My_result['ID'])
    tp_set=gt_set & my_set
        # true-positive set
        # &: set 交集運算
    precision=len(tp_set)/len(my_set)
        # &: set 交集運算
    print("Precision: {:8.4f}".format(precision))
    return tp_set,precision

def Get_ARE_AAE(ground_truth_path,result_path,Top,Sk_head,Sketch,method):
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    My_result=pd.read_csv(result_path)
        # DF of algorithm result
    gt_dict=dict(grtruth[:Config.size].values.tolist())
        # Top-k in ground truth
    top_dict=dict(My_result.values.tolist())
    distinct=len(gt_dict)
        # cardinality of all incoming elements
    row_cardinality=[len(i.distinct) for i in Sk_head]
        # number of distinct elements in each row in Sk_head
    LHH_list=[i.maxID for i in Sk_head]
        # list of local max elements in each row of Sketch    
    tp=0
    fp=0
    
    # top are/aae:
    top_set=top_dict.keys() & gt_dict.keys()
        # True positive set
    tp=len(top_set)
    fp=Config.size-tp
    top_are=0
    top_aae=0
    for item in top_set:
        top_are+=abs(top_dict[item]-gt_dict[item])/gt_dict[item]
        top_aae+=abs(top_dict[item]-gt_dict[item])
    top_are=top_are/len(top_set)
    top_aae=top_aae/len(top_set)
    
    # other are/aae:
    all_are=0
    all_aae=0
    lhh_are=0
    lhh_aae=0
    gt_all_dict=dict(grtruth.values.tolist())
        # all ground truth
    other_set=gt_all_dict.keys()-top_set
    for item in other_set:
        if method==1:
            count=Query(str(item),Top,LHH_list,Sketch,row_cardinality)
        elif method==2:
            count=Query2(str(item),Top,Sk_head,Sketch,row_cardinality)
        elif method==3:
            count=Query3(str(item),Top,Sk_head,Sketch,row_cardinality)
        elif method==4:
            count=Query4(str(item),Top,Sk_head,Sketch,row_cardinality)
        if item in LHH_list:
            lhh_are+=abs(count-gt_all_dict[item])/gt_all_dict[item]
            lhh_aae+=abs(count-gt_all_dict[item])
        all_are+=abs(count-gt_all_dict[item])/gt_all_dict[item]
        all_aae+=abs(count-gt_all_dict[item])    

    all_are=all_are/len(other_set)
    all_aae=all_aae/len(other_set)
    lhh_are=lhh_are/Config.depth
    lhh_aae=lhh_aae/Config.depth
    print("lhh_are:{},lhh_aae:{}".format(lhh_are,lhh_aae) )
    return top_are,top_aae,all_are,all_aae,tp,fp

def To_df(Top,Sketch,Sk_head,*args):
    (startx,endx,true_positive_set,precision,top_are,top_aae,all_are,all_aae,tp,fp)=args
    sketch_size=str(Config.depth)+'*'+str(Config.width)
    temp=sys.getsizeof(Top)+Sketch.nbytes+sys.getsizeof(Sk_head[0])*Config.depth
    memory_usage=str(temp)+' bytes ='+'Top:'+str(sys.getsizeof(Top))+'+ Sketch:'+str(Sketch.nbytes)+'+ Sk_head:'+str(sys.getsizeof(Sk_head[0])*Config.depth)

    result_df=pd.DataFrame(columns=['Top-k',
                                    'Sketch',
                                    'Total memory',
                                    'Exe_time',
                                    'Find',
                                    'Precision',
                                    'ARE-Top',
                                    'AAE-Top',
                                    'ARE-all',
                                    'AAE-all'])
    output_dict={
        'Top-k':Config.size,
        'Sketch':sketch_size,
        'Total memory':memory_usage,
        'Exe_time':float('{:.3f}'.format(endx-startx)),
        'Find':"Find:{}, TP:{}, FP:{}".format(len(true_positive_set),tp,fp),
        'Precision':float("{:8.4f}".format(precision)),
        'ARE-Top':float('{:8.6f}'.format(top_are)),
        'AAE-Top':float('{:8.6f}'.format(top_aae)),
        'ARE-all':float('{:8.6f}'.format(all_are)),
        'AAE-all':float('{:8.6f}'.format(all_aae))}

    result_df=result_df.append(output_dict,ignore_index=True)
    file="My_OO_kosarak_result"+'_'+str(Config.size)+'_'+str(Config.depth)+'_'+str(Config.width)+'_.csv'
    result_df.to_csv(file,index=False)
    return result_df

        
def Query(e,Top,local_maxID,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        if e in local_maxID:
            # e is LHH
            count=Sketch[row][col]
        else:
            # e is not LHH
            ratio=Config.width/row_cardinality[row]
            count=int(Sketch[row][col]*ratio)
    if count<=1:
        count=1
    return count    
    
    
def Query2(e,Top,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            count=int((Sketch[row][col]-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count

def Query3(e,Top,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/(row_cardinality[row]-Sk_head[row].bringback)
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            lhh_col,lhh_row=position(DS.Tail(Sk_head[row].maxID,0))
            if col==lhh_col:
                count=int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            else:
                count=int(Sketch[row][col]*ratio)
    if count<=1:
        count=1
    return count

def Query4(e,Top,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    index=find(DS.Tail(e,0),Top)
    if index>=0:
        # e in Top
        count=Top[index].count
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        # ratio=Config.width/(row_cardinality[row]-Sk_head[row].bringback)
        ratio=Config.width/(row_cardinality[row])
        if e == Sk_head[row].maxID:
            # e is LHH
            #count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            count=Sk_head[row].keep+int((Sketch[row][col]*ratio))
        else:
            # e is not LHH
            #count=int(Sketch[row][col]*ratio)
            count=int((Sketch[row][col]-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count