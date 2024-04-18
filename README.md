# Code of Question Generation Thesis
This repository contains the core code of my master thesis **[Asking the Right Question: Generating Difficulty-Ranked Questions from Examples](https://scriptiebank.be/asking-right-question-generating-difficulty-ranked-questions-examples)** (text can be found at the button **Download scriptie**). This thesis was submitted for the degree of Msc in Engineering: Computer Science at the university of KU Leuven. 


The promotor of this thesis was prof. dr. Luc De Raedt and the daily supervisor of this thesis was ir. Thomas Winters.  

## Requirements
The requirements to run the code are listed in requirements.txt. Next to the requirements in requirements.txt, it might be still necessary to install the spaCy pipeline. It is also recommended to set an user-agent and a from request header (in qwikidata's _return_sparql_query_results()_) to avoid Wikidata throttling the query requests.

## Data
### Generated Templates
The **_*slot.csv_** files contain templates extracted for evaluation from part of the QA datasets: TriviaQA, SimpleQuestions and WebQuestions.
### Difficulty Rankings
**_difficulty_features.csv_** contains the gathered data from Sporcle quizzes with the addition of the gathered features. The last column contains the numerical label of how many participants got that question correct.
 
**_diff_evaluation_rankings.csv_** contains the generated rankings from a random forest (pointwise ranking) and the three heuristic rankers as mentioned in the thesis text. These rankings were used for evaluation. **_diff_evaluation_order.csv_** shows which ranker was used to generate each ranking. 

[^1]: www.sporcle.com

## Template Extraction
The template extractor can be used to extract templates from a given pair of question-answer. The algorithm requires the given QA pair to have a questionmark and an answer. The code for template extraction can be found in **_template_extractor.py_**

The main method of the _Template_ class is _extraction()_.
## Filling in the Templates
The extracted templates can be filled in using the functions in 
**_expander.py_**. Depending on how many slots the template has, a different function is used. 

It should be noted that the function _expand_two_slot_template()_ takes the processing limit of Wikidata into account. At the time of writing, Wikidata Query Service only allows 1 minute processing time for each query. The effect of this 1 minute processing time is that queries that constrain an entity to be the type human cannot be processed within this limit. Before the query is given to Wikidata, the function _expand_two_slot_template()_ checks whether a human constraint is present or not. If there is, the query is modified to omit this constraint in order to produce a filled-in template.
_expand_three_slot_template()_ does not take this processing time into account and will time out in case Wikidata cannot process the query in time.

## demo.py
**_demo.py_** contains some examples in comment on how to extract a template from a given QA and how to generate new QAs from a template.

## Difficulty Classification
**_difficulty_ranker.py_** consists of two core functions, _get_difficulty_features()_ for gathering the features used for the difficulty classifier, and _amount_inserts()_ as the metric to compare two rankings.

## SPARQL Queries
**_wikidata_helpers.py_** contains various Wikidata SPARQL queries used in the algorithms.
