from pytrends.request import TrendReq
from wikidata_helpers import *
from qwikidata.sparql import return_sparql_query_results
import time
import copy


def get_difficulty_features(Q_str:str,A_str:str,Q_tag:str,A_tag:str,pytrend:TrendReq):

    '''
    Returns the difficulty features given the extracted entities of the question and answer and their 
    Wikidata identifiers. Pytrend needs to be TrendReq().
    '''
    
    features = []
    
    pop_score_Q = get_threshold(Q_str,pytrend)
    features.append(pop_score_Q)
    
    pop_score_A = get_threshold(A_str,pytrend)
    features.append(pop_score_A)
  
    query = amount_distinct_prop(Q_tag)
    raw_result = return_sparql_query_results(query)
    features.append(int(raw_result["results"]["bindings"][0]["count"]["value"]))
   
    query = amount_distinct_prop(A_tag)
    raw_result = return_sparql_query_results(query)
    features.append(int(raw_result["results"]["bindings"][0]["count"]["value"]))

    query = jaccard_similarity(Q_tag,A_tag)
    raw_result = return_sparql_query_results(query)
    features.append(int(raw_result["results"]["bindings"][0]["count"]["value"]))

    return features

def get_threshold(token,pytrend=TrendReq):
    
    '''
    Obtains the 'absolute' Google Trends popularity of the given token between 2017-03-10 and 2022-03-10. 
    time.sleep() to prevent hitting the API limit. Tokens that are compared to the given token are '4g', 'linux', 'reddit' and 'instagram'.
    '''

    time.sleep(2)
    pytrend.build_payload(kw_list=[token,'4g'],geo='',timeframe = '2017-03-10 2022-03-10')
    interest_over_time_df = pytrend.interest_over_time()
    described = interest_over_time_df.describe()
    pop_token, pop_4g= described[token]["mean"], described["4g"]["mean"]
    if pop_token == 0:
        return 0
    if pop_token < pop_4g:
        ratio = pop_4g / pop_token
        return 5 / ratio
    
    time.sleep(2)
    pytrend.build_payload(kw_list=[token,'4g','linux'],geo='',timeframe = '2017-03-10 2022-03-10')
    interest_over_time_df = pytrend.interest_over_time()
    described = interest_over_time_df.describe()
    pop_token, pop_4g, pop_linux  = described[token]["mean"], described["4g"]["mean"], described["linux"]["mean"]
    # linux is 2 times as popular as 4g
    if pop_token <= pop_linux and pop_token > pop_4g:
        division_factor = pop_4g / 5.0
        ratio = pop_token / division_factor
        return ratio
    else:
        time.sleep(2)
        pytrend.build_payload(kw_list=[token,'linux','reddit'],geo='',timeframe = '2017-03-10 2022-03-10')
        interest_over_time_df = pytrend.interest_over_time()
        described = interest_over_time_df.describe()
        pop_token, pop_reddit, pop_linux  = described[token]["mean"], described["reddit"]["mean"], described["linux"]["mean"]
        # reddit is about 3.5 times more popular than linux
        if (pop_token <= pop_reddit and pop_token > pop_linux):
            division_factor = pop_linux / 10.0
            ratio = pop_token / division_factor
            return ratio
        else:
            time.sleep(2)
            pytrend.build_payload(kw_list=[token,'instagram','reddit'],geo='',timeframe = '2017-03-10 2022-03-10')
            interest_over_time_df = pytrend.interest_over_time()
            described = interest_over_time_df.describe()
            pop_token, pop_reddit, pop_instagram  = described[token]["mean"], described["reddit"]["mean"], described["instagram"]["mean"]
            #  instagram is about 3.8 times more popular than reddit
            if (pop_token <= pop_instagram and pop_token > pop_reddit):
                division_factor = pop_reddit / 35.0
                ratio = pop_token / division_factor
                return ratio
            elif (pop_token > pop_instagram):
                return 140
            else:
                print("If this appears, something happened that I didn't account for. token:", token)
                return 0

def amount_inserts(to_check:list,ground_truth:list) -> int:
    
    '''
    Function that returns the amount of inserts required such that for every i, to_check[i] == ground_truth[i]. 
    '''

    if (to_check == ground_truth):
        return 0
    
    #queue
    queue = [to_check]
    checked= []
    inserts = 1
    while len(queue) != 0 :
        to_enqueue= []
        for elem in queue:
            # make new posibilities
            next_up = new_insert_possibilities(elem)
            # add to checked
            checked.append(elem)
            # checks if it is the same
            for made_insert_new_list in next_up:
                if made_insert_new_list == ground_truth:
                    return inserts
            #if nothing found, candidate for creating new combinations
            for made_insert_new_list in next_up:
                if not(made_insert_new_list in checked) and not(made_insert_new_list in to_enqueue):
                    to_enqueue.append(made_insert_new_list)
        #if everything is checked, increment amount of inserts
        inserts +=1
        queue.clear()
        queue= copy.deepcopy(to_enqueue)

    return 0
        
def new_insert_possibilities(to_check:list) -> int:
    
    '''
    Makes new combinations of the to_check list inserting at different posititions.
    '''

    made_lists = []

    for i in range(0,len(to_check)):
        for j in range(0,len(to_check)):
            if (i==j):
                continue
            else:
                new = copy.deepcopy(to_check)
                to_move_element = new[i]
                new.remove(new[i])
                new.insert(j,to_move_element)
                made_lists.append(new)

    return made_lists

