from wikidata_helpers import *
from qwikidata.sparql import return_sparql_query_results
import requests
import time

def expand_two_slot_template(q_identifier:str,a_identifier:str,direct_relation_identifier:str,template:str,aq_direction:bool):

    if aq_direction:
        type_first,type_second = human_type_check(a_identifier,q_identifier,True)
    else:
        type_first,type_second = human_type_check(a_identifier,q_identifier,False)
    
    if (len(type_first) == 0 and len(type_second) == 0):
        if aq_direction:
            query = expand_template(direct_relation_identifier,a_identifier,q_identifier)
        else:
            query = expand_template(direct_relation_identifier,q_identifier,a_identifier)
    else:
        remove_first_type = True
        if ("human" in type_second):
            remove_first_type = False
        if aq_direction:
            query = expand_failure_first(a_identifier,q_identifier,direct_relation_identifier,remove_first_type)
        else:
            query = expand_failure_first(q_identifier,a_identifier,direct_relation_identifier,remove_first_type)
    try:
        raw_result = return_sparql_query_results(query)
        filled_in = []
        type_first = ""
        type_second = ""
        if (len(raw_result["results"]["bindings"])==0):
            filled_in = "Search space issue"
            type_first = "No type"
            type_second = "No type"
        for row in raw_result["results"]["bindings"]:
            new_first = row["newFirstLabel"]["value"]
            new_second = row["newSecondLabel"]["value"]
            type_first = row["typeFirstLabel"]["value"]
            type_second = row["typeSecondLabel"]["value"]
            if aq_direction:
                intermediate_template = template.replace("_Q_",new_second)
                filled_in.append(intermediate_template.replace("_A_",new_first))
            else:
                intermediate_template = template.replace("_Q_",new_first)
                filled_in.append(intermediate_template.replace("_A_",new_second))
    except requests.exceptions.Timeout as e:
        if aq_direction:
            query = expand_failure(a_identifier,q_identifier)
        else:
            query = expand_failure(q_identifier,a_identifier)
        time.sleep(60)
        raw_result = return_sparql_query_results(query)
        filled_in = "Search space issue"
        type_first = []
        type_second = []                        
        if (len(raw_result["results"]["bindings"])==0):
            type_first = "No type"
            type_second = "No type"
        for row in raw_result["results"]["bindings"]:
            if (not(row["typeFirstLabel"]["value"] in type_first)):
                type_first.append(row["typeFirstLabel"]["value"])
            if (not(row["typeFirstLabel"]["value"] in type_second)):
                type_second.append(row["typeSecondLabel"]["value"])

    print("Template: ",template)
    print("Type(s) first placeholder: ", type_first)
    print("Type(s) second placeholder:", type_second)
    print(filled_in)
    return

def expand_three_slot_template(q_identifier:str,a_identifier:str,direct_relation_identifier:str,constraint_relation_info:tuple,template:str,aq_direction:bool):
    
    if constraint_relation_info != ('blank','blank'):
        tup_supp_direction,tup_supp_constraint = constraint_relation_info
        tup_supp_direction = tup_supp_direction[0]
        tup_supp_constraint = tup_supp_constraint[0][0]
    
    constraint_position_first = False
    c_identifier = tup_supp_direction[0]
    if (tup_supp_direction[0] == "answer") or (tup_supp_direction[0] == "question"):
        constraint_position_first = True
        c_identifier = tup_supp_direction[1]

    
    first_constraint = False
    if (aq_direction and (tup_supp_direction[0] == "answer" or tup_supp_direction[1] == "answer")):
        first_constraint = True
    elif (not(aq_direction) and (tup_supp_direction[1] == "question" or tup_supp_direction[0] == "question")):
        first_constraint = True
    
    if aq_direction:
        query = three_placeholders_extract(a_identifier,q_identifier,c_identifier,direct_relation_identifier,tup_supp_constraint,first_constraint,constraint_position_first)
    else:
        query = three_placeholders_extract(q_identifier,a_identifier,c_identifier,direct_relation_identifier,tup_supp_constraint,first_constraint,constraint_position_first)
    
    print(query)
    raw_result = return_sparql_query_results(query)
    filled_in = []
    for row in raw_result["results"]["bindings"]:
        new_first = row["newFirstLabel"]["value"]
        new_second = row["newSecondLabel"]["value"]
        new_third = row["newThirdLabel"]["value"]
        intermediate_template = intermediate_template.replace("_C_",new_third)
        if aq_direction:
            intermediate_template = template.replace("_Q_",new_second)
            filled_in.append(intermediate_template.replace("_A_",new_first))
        else:
            intermediate_template = template.replace("_Q_",new_first)
            filled_in.append(intermediate_template.replace("_A_",new_second))
        
    print("Template: ",template)
    print(filled_in)
    return

def human_type_check(a_tag,q_tag,isaq):
    if isaq:
        human_check_query = expand_failure(a_tag,q_tag)
    else:
        human_check_query = expand_failure(q_tag,a_tag)

    raw_result = return_sparql_query_results(human_check_query)
    type_first = []
    type_second = []
    for row in raw_result["results"]["bindings"]:
        if (not(row["typeFirstLabel"]["value"] in type_first)):
            type_first.append(row["typeFirstLabel"]["value"])
        if (not(row["typeFirstLabel"]["value"] in type_second)):
            type_second.append(row["typeSecondLabel"]["value"])
    
    if (("human" in type_first) or ("human" in type_second)):
        return type_first,type_second
    else:
        return [],[]