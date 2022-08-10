from SPARQLWrapper import SPARQLWrapper
from wikidata_helpers import *
from qwikidata.sparql import return_sparql_query_results
from string import punctuation
import copy

class Template:
    
    def __init__(self,sentence:str):
        self.original = sentence
        # list of templates
        self.question_templates = []
        self.aq_direction_templates= []
        # (extracted words,corresponding tags)
        self.question_slots = ([],[])
        self.question_slot_types = []
        self.answer_slot = ("answer","Q0")
        self.answer_type = "Q1"
        # relations between primary question word and answer (2D)
        self.relations_qa = []
        self.relations_qa_str = []
        self.direction_is_aq = []
        # [([],[])]  1st dimension -> corresponding to the question template index
        # 2nd dimension -> tuple with first element list of found constraints corresponding to which slot
        # 2nd element of tuple is the constraint relations
        self.supporting_relations = []
        # question words that were already used dont need to be checked again for possible templates
        self.not_checked_entities = ([],[])
        # possbile supporting question slot because same as answer
        self.candidate_supporting_question_slot = ([],[])
        self.all_question_entities = ([],[])
        self.support_extracted_str = []
        # has templates
        self.processed = False
        self.answer_tag_set = False
    
    def get_question_templates(self):
        return self.question_templates
    
    def get_question_slots(self):
        return self.question_slots
    
    def add_question_slot(self,extracted_entity,entity_tag):
        fst,snd = self.question_slots
        fst.append(extracted_entity)
        snd.append(entity_tag)
        self.question_slots = (fst,snd)
        return
    
    def get_question_slot_types(self):
        return self.question_slot_types
    
    def add_question_slot_type(self,entity_type):
        self.question_slot_types.append(entity_type)
        return
    
    
    def get_answer_slot(self):
        return self.answer_slot
    
    def get_answer_type(self):
        return self.answer_type
    
    def get_relations_qa(self):
        return self.relations_qa
    
    def get_relations_qa_str(self):
        return self.relations_qa_str

    def get_aq_directions(self):
        return self.aq_direction_templates
        
    def add_relation_qa(self,relations:list,relations_str:list):
        self.relations_qa.append(relations)
        self.relations_qa_str.append(relations_str)
        return
    
    def get_supporting_extraction(self):
        return self.supporting_extraction
    
    def add_supporting_extraction(self,extracted_entites,entity_tags):
        fst,snd = self.supporting_extraction
        fst.append(extracted_entites)
        snd.append(entity_tags)
        self.supporting_extraction = (fst,snd)
        return
    
    
    def get_supporting_relations(self):
        return self.supporting_relations
    
    def add_supporting_relations(self,relations,supported_tag):
        self.supporting_relations.append((relations,supported_tag))
        return
    
    def pop_not_checked_entities(self,entity:str,tag,pop_cause_answer_similar = False):

        '''
        Remove the entities that are checked
        '''

        fst,snd = self.not_checked_entities

        if (pop_cause_answer_similar is True):
            for i in range(0,fst.count(entity)):
                fst.remove(entity)
                snd.remove(tag)
            
            can_sup_strs = self.candidate_supporting_question_slot[0]
            can_sup_labels = self.candidate_supporting_question_slot[1]
            can_sup_strs.append(entity)
            can_sup_labels.append(tag)
            self.candidate_supporting_question_slot = (can_sup_strs,can_sup_labels)
        else:
            fst.remove(entity)
            snd.remove(tag)
        self.not_checked_entities = (fst,snd)
        return
    
    def preprocessing(self,spacy_pipeline):
        '''
        Pre-processing, entities that belongs to certain classes are capitalized.
        '''
        original = self.original
        original = original.replace("  "," ")
        doc = spacy_pipeline(original)
        for ent in doc.ents:
            if ent.label_ in ["GPE","PERSON","NORP","ORG","LANGUAGE","LOC","EVENT","PRODUCT","WORK OF ART"]:
                original = original.replace(ent.text,ent.text.title())
        self.original = original
        return
    
    def extraction(self,spacy_pipeline,sparqlwrapper,spacy_pipeline_md):

        '''
        Function that attempts to extract a template from a given QA.
        '''
        # using entity linker, check for DBpedia resources
        doc = spacy_pipeline(self.original)
        entities_tuples = []
        for entity in doc.ents:
            entities_tuples.append((entity.text,entity.kb_id_))
        
        # if nothing found, no template available
        if len(entities_tuples)==0:
            return
        
        # parse the tags
        entities_tuples = [(entity[0],entity[1].replace("http://dbpedia.org/resource/","")) for entity in entities_tuples]
        # if the answer entity is recognized as blank DBpedia tag, or there is only one entity found in whole QA
        # then there is no template available
        if (entities_tuples[-1][1] == "" or len(entities_tuples) == 1):
            return
        else :
            self.answer_slot = entities_tuples[-1]
            splitted = self.original.split("?")
            # case when there is no entity in question, no template available
            if not(self.answer_slot[0] in splitted[-1]):
                return
            # convert the DBpedia resource identifier to the Wikidata variants
            dbquery_a = self.dbpedia_query(self.answer_slot[1])
           
            self.answer_slot = (self.answer_slot[0],self.translate_to_wikidata(dbquery_a,sparqlwrapper))
            if len(self.answer_slot[1]) == 0:
                return
            # no disambiguation required
            if len(self.answer_slot[1]) == 1:
                self.answer_tag_set = True
                self.answer_slot = (self.answer_slot[0],self.answer_slot[1][0]) 
            # entities in question
            can_names_temp = []
            can_dbtags_temp = []
            for (x,y) in entities_tuples[0:-1]:
                if (y != "") and not(x in splitted[-1]):
                    can_names_temp.append(x)
                    can_dbtags_temp.append(y)
            if (len(can_names_temp)==0):
                return
            else:
                can_tags = []
                # translate the DBpedia variants to wikidata tags
                for tag in can_dbtags_temp:
                    dbquery_q = self.dbpedia_query(tag)
                    can_tags.append(self.translate_to_wikidata(dbquery_q,sparqlwrapper))
                self.not_checked_entities = (can_names_temp,can_tags)
        
        # check whether the question contains an entity that is the same as the answer, if so, skip this potential template
        for i in range(0,len(self.not_checked_entities[1])):
            if (self.not_checked_entities[1][i] == self.answer_slot[1]):
                self.pop_not_checked_entities(self.not_checked_entities[0][i],self.not_checked_entities[1][i],True)
                break
        self.all_question_entities = copy.deepcopy(self.not_checked_entities)
        
        # extraction loop for all question entities
        while (len(self.not_checked_entities[0]) != 0):
            # one loop checks for template
            if (self.extraction_loop()):
                self.check_supporting()
        
        if len(self.relations_qa)==0:
            return
        # construction of worthy templates:
        self.construct_templates()
        self.relation_disambiguation(spacy_pipeline_md)
        self.processed= True
        return 
    
    def extraction_loop(self):

        '''
        Check for direct relations between entities found in the question and the answer entity.
        '''

        if (len(self.not_checked_entities[0]) == 0):
            return False
        #(nce = not checked entity)
        ncestrs,ncetags = self.not_checked_entities
        answer_tags = self.answer_slot[1]
        
        # loop over amount of found entities
        for i in range(0,len(ncetags)):
            # for all tags in the first entity of not checked
            for candidate_tag in ncetags[0]:
              
                # if the answer_tag is not determined
                if not(self.answer_tag_set):
                   
                    # loop over the possible answer tags and check if there is a relation
                    for answer_tag in answer_tags:
                        
                        relation_query = get_relations(candidate_tag,answer_tag)
                        raw_result = return_sparql_query_results(relation_query)
                        # relations in Wikidata are not commutative, so check if there exists one in opposite direction
                        if (len(raw_result["results"]["bindings"])==0):
                            relation_query = get_relations(answer_tag,candidate_tag)
                            raw_result = return_sparql_query_results(relation_query)
                            if (len(raw_result["results"]["bindings"]) != 0):
                                self.extract_entities(ncestrs,ncetags,candidate_tag,answer_tag,raw_result,True)
                                return True

                        else:
                            self.extract_entities(ncestrs,ncetags,candidate_tag,answer_tag,raw_result,False)
                            return True
                # case when the answer tag is already determined
                else:
                    
                    relation_query = get_relations(candidate_tag,answer_tags)
                    raw_result = return_sparql_query_results(relation_query)
                    
                    if (len(raw_result["results"]["bindings"])==0):
                        relation_query = get_relations(answer_tags,candidate_tag)
                        raw_result = return_sparql_query_results(relation_query)

                        if (len(raw_result["results"]["bindings"]) != 0):                               
                            self.extract_entities(ncestrs,ncetags,candidate_tag,"already set",raw_result,True)
                            return True
                    else:
                        self.extract_entities(ncestrs,ncetags,candidate_tag,"already set",raw_result,False)
                        return True
            
            self.pop_not_checked_entities(ncestrs[0],ncetags[0])
        return False


    def extract_entities(self, ncestrs, ncetags, candidate_tag, answer_tag, raw_result,direction:bool):
        
        '''
        Extract the entities and set the relation in place.
        '''
        
        self.add_question_slot(ncestrs[0],candidate_tag)

        if answer_tag != "already set":
            self.answer_slot = (self.answer_slot[0],answer_tag)
            self.answer_tag_set = True

        query_response = return_cols(raw_result,"propLabel","relationLabel",True)
        placeholder = []
        placeholder_str = []
        for rel_str,rel in query_response.items():
            placeholder.append(rel.replace("http://www.wikidata.org/prop/direct/",""))
            placeholder_str.append(rel_str)
                                    
        # add the relation for the found pair
        self.add_relation_qa(placeholder,placeholder_str)
        self.direction_is_aq.append(direction)
        # check for supporting relations by removing themselves from all entities
        x,y = copy.deepcopy(self.all_question_entities)
        x.remove(ncestrs[0])
        y.remove(ncetags[0])
        self.candidate_supporting_question_slot = (x,y) 
        # remove from not checked
        self.pop_not_checked_entities(ncestrs[0],ncetags[0])
        return
    
    def check_supporting(self):

        '''
        Check if the template can be turned into a three slot template
        '''

        # found_tag indicates how it should be positioned for expansion
        found_tag = []
        found_raw_rel = []
        
        # check if there exist relations between the just extracted question blank and candidates:
        for i in range(0,len(self.candidate_supporting_question_slot[0])):
            candidate_labels = self.candidate_supporting_question_slot[1][i]
            for candidate_label in candidate_labels:
                # check for relations
                empty,raw_result = self.has_relation(self.question_slots[1][-1],candidate_label)
                if (not empty):
                    # make sure they are in the right order for easy check later
                    found_tag.append(("question",candidate_label))
                    self.support_extracted_str.append(self.candidate_supporting_question_slot[0][i])
                    found_raw_rel.append(raw_result)
                else:
                    empty,raw_result = self.has_relation(candidate_label,self.question_slots[1][-1])
                    if (not empty):
                        found_tag.append((candidate_label,"question"))
                        self.support_extracted_str.append(self.candidate_supporting_question_slot[0][i])
                        found_raw_rel.append(raw_result)
            
                    else:
                        empty,raw_result = self.has_relation(candidate_label,self.answer_slot[1])
                        if (not empty):
                            found_tag.append((candidate_label,"answer"))
                            self.support_extracted_str.append(self.candidate_supporting_question_slot[0][i])
                            found_raw_rel.append(raw_result)
                        else:
                            empty,raw_result = self.has_relation(self.answer_slot[1],candidate_label)
                            if (not empty):
                                found_tag.append(("answer",candidate_label))
                                self.support_extracted_str.append(self.candidate_supporting_question_slot[0][i])
                                found_raw_rel.append(raw_result)
                    
        #reset
        self.candidate_supporting_question_slot = ([],[])
        
        if (len(found_tag)==0):
            self.supporting_relations.append(("blank",'blank'))
            return
        
        found_rel = []
        # convert raw result
        for found_raw in found_raw_rel:
            query_response = return_cols(found_raw,"propLabel","relationLabel",True)
            relations = []
            for relation_str,rel in query_response.items():
                relations.append(rel.replace("http://www.wikidata.org/prop/direct/",""))
            found_rel.append(relations)
        # add supports that were found
        tup = (found_tag,found_rel)
        self.supporting_relations.append(tup)

        return
        
    
    
    def dbpedia_query(self,dbr):

        """
        Returns the SPARQL query string that queries the equivalent entities.
        """

        if "." in dbr:
            dbr = dbr.replace(".","\.")
        if "," in dbr:
            dbr = dbr.replace(",","\,")
        if "(" in dbr:
            dbr = dbr.replace("(","\(")
        if ")" in dbr:
            dbr = dbr.replace(")","\)")
        if "'" in dbr:
            dbr = dbr.replace("'",r"\'")
        if "&" in dbr:
            dbr = dbr.replace("&","\&")
        query_string = """
        SELECT distinct ?same
        WHERE {{dbr:{dbr} owl:sameAs ?same}}
        LIMIT 100
        """
        return query_string.format_map({"dbr":dbr})
    
    def translate_to_wikidata(self,query,sparqlwrapper:SPARQLWrapper):

        '''
        Function that returns the Wikidata identifiers of the DBpedia resource in the query argument. 
        '''

        sparqlwrapper.setQuery(query)
        response = sparqlwrapper.query().convert()
        wikidata_preceder = "http://www.wikidata.org/entity/"
        candidates = []
        for result in response["results"]["bindings"]:
            if (wikidata_preceder in result["same"]["value"]):
                candidates.append(result["same"]["value"].replace(wikidata_preceder,""))
        
        return candidates
    
    def has_relation(self,first_label,second_label):

        '''
        Checks if there is a relation between the two entities
        '''

        relation_query = get_relations(first_label,second_label)
       
        raw_result = return_sparql_query_results(relation_query)
        return (len(raw_result["results"]["bindings"]) == 0, raw_result)
    
    def construct_templates(self):

        '''
        Construct the template, given the extracted entities
        '''

        for i in range(0,len(self.question_slots[0])):
            order,supp_rel = self.supporting_relations[i]
            # if it has supporting relations check whether the extracted q blank is fitting for a template
            if (order != "blank"):
                question_with_blanks = self.original.replace(self.question_slots[0][i],"_Q_")
                question_with_blanks = question_with_blanks.replace(self.answer_slot[0],"_A_")
                question_with_blanks = question_with_blanks.replace(self.support_extracted_str[i],"_C_")
                self.question_templates.append(question_with_blanks)
            else:
                question_with_blanks = self.original.replace(self.question_slots[0][i],"_Q_")
                question_with_blanks = question_with_blanks.replace(self.answer_slot[0],"_A_")
                self.question_templates.append(question_with_blanks)
                
    def relation_disambiguation(self,spacy_pipeline):

        '''
        Relation disambiguation by checking keywords that are noun or verbs
        '''
        
        formatted_questions = []
        # for every template, set it in the right format (question with the blank removed)
        for template in self.question_templates:
            temp = template.replace("_Q_","")
            temp = temp.replace("_A_","")
            temp = temp.replace("?","")
            formatted_questions.append(temp)
    
        # relation disambiguate, check for nounds and verbs
        keywords = []
        pos_tags = ['NOUN','VERB'] 
        for text in formatted_questions:
            doc = spacy_pipeline(text.lower()) 
            result = []
            for token in doc:
                if(token.text in spacy_pipeline.Defaults.stop_words or token.text in punctuation):
                    continue
                if(token.pos_ in pos_tags):
                    result.append(token.text)
            keywords.append(result)
        original = spacy_pipeline(self.original)
        final_relations = []
        final_relations_str = []
        final_aq_templates = []
        # first dimension each template relation
        for i in range(0,len(self.relations_qa)):
            # if the template has more than one relation
            if len(self.relations_qa[i])>1:
                found_keywords_this_template = keywords[i]
                appears_in_original_sentence = []
                for j in range(0,len(self.relations_qa[i])):
                    # if it appears literally in the string, save it
                    if self.relations_qa_str[i][j] in self.original:
                        appears_in_original_sentence.append((i,j))
                # in case more than one appears in the string, check for similarity
                if (len(appears_in_original_sentence) > 1):
                    similarity_scores = []
                   
                    for i,j in appears_in_original_sentence:
                        # case no keywords found, then compare the relation strings to sentence
                        if (len(found_keywords_this_template)==0):
                            for i,j in appears_in_original_sentence:
                                similarity_scores.append(spacy_pipeline(self.relations_qa_str[i][j]).similarity(original))
                        else:
                            sim_score_for_keywords = []
                            for keyword in found_keywords_this_template:
                                sim_score_for_keywords.append(spacy_pipeline(self.relations_qa_str[i][j]).similarity(spacy_pipeline(keyword)))
                            similarity_scores.append(max(sim_score_for_keywords))
                   
                    max_index = similarity_scores.index(max(similarity_scores))
                    first_dim, second_dim = appears_in_original_sentence[max_index]
                    final_relations.append(self.relations_qa[first_dim][second_dim])
                    final_relations_str.append(self.relations_qa_str[first_dim][second_dim])
                    final_aq_templates.append(self.direction_is_aq[i])
                elif (len(appears_in_original_sentence)==1):
                    first_dim, second_dim = appears_in_original_sentence[0]
                    final_relations.append(self.relations_qa[first_dim][second_dim])
                    final_relations_str.append(self.relations_qa_str[first_dim][second_dim])
                    final_aq_templates.append(self.direction_is_aq[i])
                else:
                    similarity_scores = []
            
                    for j in range(0,len(self.relations_qa[i])):
                        if (len(found_keywords_this_template)==0):
                            similarity_scores.append(spacy_pipeline(self.relations_qa_str[i][j]).similarity(original))
                        else:
                            sim_score_for_keywords = []
                            for keyword in found_keywords_this_template:
                                sim_score_for_keywords.append(spacy_pipeline(self.relations_qa_str[i][j]).similarity(spacy_pipeline(keyword)))
                            similarity_scores.append(max(sim_score_for_keywords))
                    
                    max_index = similarity_scores.index(max(similarity_scores))
                    final_relations.append(self.relations_qa[i][max_index])
                    final_relations_str.append(self.relations_qa_str[i][max_index])
                    final_aq_templates.append(self.direction_is_aq[i])
            else:
                final_relations.append(self.relations_qa[i][0])
                final_relations_str.append(self.relations_qa_str[i][0])
                final_aq_templates.append(self.direction_is_aq[i])
        
        self.relations_qa = final_relations
        self.relations_qa_str = final_relations_str
        self.aq_direction_templates = final_aq_templates
        
