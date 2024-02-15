from Node import DS
from Tools import Config
import pandas as pd
import os
import spookyhash
import mmh3
import sys

import matplotlib.pyplot as plt
import numpy as np


# ==========================Tools=========================  

# ==========================UpdateSk==========================
def UpdateSk(element,Sk_head,Sk):
    #e_max=Config.e_max
    col,row=position(element)
        # col / row index of element
    # ==========================update sketch==========================
    Sk_head[row].count+=element.count
    Sk_head[row].distinct.add(element.ID)
    Sk[row][col]+=1
    #Sk[row][col]+=element.count
    Update_local_max(Sk_head[row],Sk[row],element,col)

# ==========================update local max==========================       
def Update_local_max(head_item,element_list,element,column):
    # head_item: Sk_head[row]
    # element_list: Sketch[row]
    width,depth=Config.width,Config.depth
    '''
    # small sketh
    if head_item.maxID=='':
        head_item.maxID=element.ID
        head_item.keep=1
    elif head_item.maxID==element.ID:
        head_item.keep+=1
  
    # large sketch
    if head_item.maxID=='':
        head_item.maxID=element.ID
        head_item.keep=element.count
    elif head_item.maxID==element.ID:
        head_item.keep+=element.count    
    '''
    if head_item.maxID=='':
        head_item.maxID=element.ID
        head_item.keep=1
    elif head_item.maxID==element.ID:
        head_item.keep+=1
    else:
        # head_item.maxID != element.ID:
        local_max_col,local_max_row=position(DS.Tail(head_item.maxID,0))
            # element_list[local_max_col]: lhh所屬的bucket
        if local_max_col==column:
            # lhh collision with e
            '''
            # method 1
            head_item.keep-=1
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=1
            
            # method 2 v
            head_item.keep-=element.count
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=element.count
            
            # method 4 
            if not head_item.keep>>1:
                head_item.maxID=element.ID
                head_item.keep=element.count            
            
            # method 5
            head_item.keep-=element.count
            if head_item.keep<0:
                lhh_count=int((element_list[local_max_col]+head_item.keep)/2)
                estimat_count=int((element_list[local_max_col]-lhh_count)/2)
                if estimat_count>lhh_count:
                    head_item.maxID=element.ID
                    head_item.keep=element.count
            '''            
            head_item.keep-=1
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=1
                
        elif element_list[local_max_col]<element_list[column]:
            # no collision
            '''
            # method 1
            head_item.maxID=element.ID
            head_item.keep=1

            # method 2
            head_item.keep-=element.count
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=element.count
            
            
            # method 3
            head_item.maxID=element.ID
            head_item.keep=element.count
            
            
            # method 4 v
            head_item.keep-=element.count
            if not head_item.keep>>1:
                head_item.maxID=element.ID
                head_item.keep=element.count    
                
            # method 5
            lhh_count=head_item.keep+int((element_list[local_max_col]-head_item.keep)/2)
            rate=int(element_list[column]/head_item.count)
            estimate=int(element_list[column]*rate)
            if estimate<1:
                estimate=1
            if estimate>lhh_count:
                head_item.maxID=element.ID
                head_item.keep=estimtae    
            
            # method 6 
            head_item.keep-=element.count
            if not head_item.keep>>1:
                head_item.maxID=element.ID
                head_item.keep=element.count                 

            # method 7
            head_item.keep-=1
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=1       
            '''
            head_item.keep-=1
            if head_item.keep<0:
                head_item.maxID=element.ID
                head_item.keep=1  
            
    # update e_max
    if element_list[column]>Config.e_max.count:
        Config.e_max.ID=element.ID
        Config.e_max.count=element_list[column]

# ========================== BringBack=========================
def BringBack(e_min,Top,head,sketch):
    # bring e_max back to Top
    # e_min=e_max, e_max=Null, delete e_max.count in Sketch, send e_min into Sketch
    Top.pop(e_min.ID)
    Top[Config.e_max.ID]=Config.e_max.count
    DeleteSk(Config.e_max,head,sketch)
    UpdateSk(e_min,head,sketch)
    #col,row=position(DS.Tail(Config.e_max.ID,1))
    #head[row].bringback+=1
    
# ==========================DeleteSk=========================
def DeleteSk(element,head,sketch):
    # e_max in sketch: sketch[r][c]=0, total count-=sketch[row][col]
    #width,depth=get_width_depth()
    col,row=position(element)
    head[row].count-=element.count
        # total_count-=element.count
    sketch[row][col]=0
    head[row].maxID=''
    # reset e_max
    element.ID=""
    element.count=0

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
    
def Get_precision(ground_truth_path,result_dict):
    #gr_truth: path of csv file
    grtruth=pd.read_csv(ground_truth_path)
        # ground truth of whole data set, [Element, Count]
    grtruth['Element'] = grtruth['Element'].astype(str)
    # precision
    gt_set=set(grtruth['Element'][:Config.size])
        # e.ID only
    my_set=set(result_dict.keys())
    tp_set=gt_set & my_set
        # true-positive set
        # &: set 交集運算
    precision=len(tp_set)/len(my_set)
        # &: set 交集運算
    print("Precision: {:8.4f}".format(precision))
    return tp_set,precision

def Get_ARE_AAE(ground_truth_path,result_dict,Sk_head,Sketch,method):
    grtruth=pd.read_csv(ground_truth_path)
        # DF of ground truth of whole data set
    grtruth['Element'] = grtruth['Element'].astype(str)
        # ID transfer to str
    gt_dict=dict(grtruth[:Config.size].values.tolist())
        # Top-k in ground truth
    distinct=len(gt_dict)
        # cardinality of all incoming elements
    # row_cardinality=[len(i.distinct) for i in Sk_head]
    row_cardinality=[len(i.distinct) for i in Sk_head]
        # number of distinct elements in each row in Sk_head
    LHH_list=[i.maxID for i in Sk_head]
        # list of local max elements in each row of Sketch    
    tp=0
    fp=0
    
    # top are/aae:
    top_set=result_dict.keys() & gt_dict.keys()
        # True positive set
    tp=len(top_set)
    fp=Config.size-tp
    top_are=0
    top_aae=0
    
    top_count_list=[]
    gr_count_list=[]
    
    for item in top_set:
        top_are+=abs(result_dict[item]-gt_dict[item])/gt_dict[item]
        top_aae+=abs(result_dict[item]-gt_dict[item])
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
            count=Query2(str(item),result_dict,Sk_head,Sketch,row_cardinality)
        elif method==3:
            count=Query3(str(item),result_dict,Sk_head,Sketch,row_cardinality)
        elif method==4:
            count=Query4(str(item),result_dict,Sk_head,Sketch,row_cardinality)
        elif method==5:
            count=Query5(str(item),result_dict,Sk_head,Sketch,row_cardinality)   
        elif method==6:
            count=Query6(str(item),result_dict,Sk_head,Sketch,row_cardinality)               
        if item in LHH_list:
            lhh_are+=abs(count-gt_all_dict[item])/gt_all_dict[item]
            lhh_aae+=abs(count-gt_all_dict[item])
        all_are+=abs(count-gt_all_dict[item])/gt_all_dict[item]
        all_aae+=abs(count-gt_all_dict[item])    

    all_are=all_are/len(other_set)
    all_aae=all_aae/len(other_set)
    lhh_are=lhh_are/Config.depth
    lhh_aae=lhh_aae/Config.depth
    print("lhh_are:{},lhh_aae:{}".format(lhh_are,lhh_aae))
    
    '''
    # drawing Top-k TP figure
    plt.figure(figsize=[6,16])
    length=len(top_set)
    indexli=[i for i in range (length)]
    
    plt.xticks([j for j in range(0,length,int(length/20))])
    gr_list=np.log2(gr_count_list)
    result_li=np.log2(top_count_list)
    plt.xlabel('Top-{} element'.format(length))
    plt.ylabel('Count(log2 scale)')
    
    gr_line,=plt.plot(indexli,gr_list,'r',label='GroundTruth')
    result_line,=plt.plot(indexli,result_li,'g',label='My algo')
        # 注意此處的,= 且必須同時設定label
    plt.legend(handles=[gr_line,result_line],loc='best')
    plt.show()    
    
    '''
    
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
    
    
def Query2(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
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
    

def Query3(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    '''
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
    '''
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
        else:
            # e is not LHH
            count=int(avg_count*ratio)
            #count=int((avg_count-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count         
    

def Query4(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/(row_cardinality[row])
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            #count=(Sk_head[row].keep+int(Sketch[row][col]*ratio))
        else:
            # e is not LHH
            count=int((avg_count-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count    

def Query5(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/row_cardinality[row]
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            count=Sketch[row][col]
        else:
            # e is not LHH
            count=int((avg_count-Sk_head[row].keep)*ratio)
    if count<=1:
        count=1
    return count

def Query6(e,Top_dict,Sk_head,Sketch,row_cardinality):
    # e is ID, type(e)=str
    # row_cardinality is list of number of distinct elements in each row in Sk_head
    # local_maxID is list of local max element in each row of Sketch
    count=0
    if Top_dict.get(e):
        count=Top_dict[e]
    else:
        # e in Sketch
        col,row=position(DS.Tail(e,0))
        ratio=Config.width/(row_cardinality[row])
        avg_count=Sk_head[row].count/Config.width
        if e == Sk_head[row].maxID:
            # e is LHH
            #count=Sk_head[row].keep+int((Sketch[row][col]-Sk_head[row].keep)*ratio)
            #count=int(Sketch[row][col]*ratio)+bringback_count
            count=int((Sketch[row][col]+Sk_head[row].keep))>>1
        else:
            # e is not LHH
            count=int(Sketch[row][col]*ratio)
    if count<=1:
        count=1
    return count