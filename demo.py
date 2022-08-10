from template_extractor import Template
from SPARQLWrapper import SPARQLWrapper, JSON
import spacy
from expander import expand_two_slot_template,expand_three_slot_template


#expand_two_slot_template("Q148","Q956","P36","What is the capital of _Q_? _A_",False)
#template_extraction("who does Joakim Noah play for? Chicago Bulls")
#expand_two_slot_template('Q311735','Q128109','P54','Who does_Q_ play for? _A_',False)
#template_extraction("Marilyn Monroe starred in The Seven Year Itch. Who directed it? Billy Wilder")
#expand_three_slot_template("Q290679","Q51547","P57",([('question', 'Q4616')], [['P161']]),"_C_ starred in _Q_. Who directed it? _A_",False)

def template_extraction(QA:str):

    '''
    Tries to extract a template given a QA.
    '''

    spotlight_pipe = spacy.blank('en')
    spotlight_pipe.add_pipe('dbpedia_spotlight')
    # For a more detailed pre-processing, feel free to use the lg spaCy pipe.
    preprocess_pipe = spacy.load('en_core_web_md')
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)
    
    template = Template(QA)
    template.preprocessing(preprocess_pipe)
    template.extraction(spotlight_pipe,sparql,preprocess_pipe)
    
    if template.processed:
        print("Template(s) found")
        print("Given QA: ", QA)
        print("Found templates: ", template.get_question_templates())
        print("Extracted question entities: ",template.get_question_slots())
        print("Extracted answer entities: ",template.get_answer_slot())
        print("Connecting direct relation identifier(s): ",template.get_relations_qa())
        print("Connecting direct relation string(s): ",template.get_relations_qa_str())
        print("Constraint relation identifiers for three slot templates: ",template.get_supporting_relations())
        print("aq_direction :",template.get_aq_directions())

    else:
        print("No template found")
    
    return template

