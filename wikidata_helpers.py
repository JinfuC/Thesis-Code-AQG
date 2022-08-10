	
def return_cols(result,first_col,second_col,return_ids:bool):

	"""
	Returns a dictionary containing pair of a JSON result of qwikidata. Return_ids should be true
	in case if the Wikidata id-tags are desired as keys.
	"""
	
	kv_pairs={}
	for row in result["results"]["bindings"]:
		if (return_ids):
			key = row[first_col]["value"].replace("http://www.wikidata.org/entity/","")
			kv_pairs[key]= row[second_col]["value"]
		else:
			kv_pairs[row[first_col]["value"]]= row[second_col]["value"]
	return kv_pairs


def get_relations(id1,id2):

	'''
	Returns the query checking if there is a relation between the two Wikidata identifiers.
	'''

	query = """
	SELECT ?propLabel ?relationLabel
    WHERE {{
       wd:{id_1} ?relation wd:{id_2}.
	   ?prop wikibase:directClaim ?relation.
	   ?prop rdfs:label ?propLabel.
	   filter(lang(?propLabel) = "en").
       SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}} 
    }}
	"""
	return query.format_map({"id_1":id1,"id_2":id2})

def is_instance_of(topic_id):
	
	"""
	Returns query with as result to which type is belongs to, ordered by the amount of properties each type has.
	"""

	query = """
	SELECT ?item (count(?values) as ?amount)
	WHERE 
	{{
	wd:{topic_id} wdt:P31 ?item.
	?item ?properties ?values
	SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }} 
	}} group by ?item having (count(?values))
	order by DESC(?amount)
	"""
	return query.format_map({"topic_id":topic_id})

def freebase_to_name(freebase_id):

	"""
	Returns the query that searches for the Wikidata string of a freebase id.
	"""

	query = """
	SELECT ?item ?itemLabel
	WHERE 
	{{
	?item wdt:P646 "{freebase_id}".
	SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }} 
	}}
	LIMIT 1
	"""
	return query.format_map({"freebase_id":freebase_id})


def expand_template(relation:str,first:str,second:str):
	## normal expansion with type inferring
	query = """
	SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel
	WHERE 
	{{
	wd:{first} wdt:P31 ?typeFirst.
	wd:{second} wdt:P31 ?typeSecond.
	?newFirst wdt:P31 ?typeFirst.
	?newSecond wdt:P31 ?typeSecond.
	?newFirst wdt:{relation} ?newSecond.
	SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
	}}
	LIMIT 2
	"""
	return query.format_map({"relation":relation,"first":first,"second":second})

def jaccard_similarity(question_placeholder:str,answer_placeholder:str):
	
	'''
	Not the actual Jaccard similarity, this is without dividing by the total amount of item with incoming links to both
	'''

	query = """
	SELECT  (COUNT(?item) as ?count)
	WHERE 
	{{
  	?item ?l1 wd:{pl1}.
  	?item ?l2 wd:{pl2}.
  	SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }} 
	}}
	"""
	return query.format_map({"pl1":question_placeholder,"pl2":answer_placeholder})

def amount_distinct_prop(placeholder:str):
	query = """
	SELECT (COUNT(DISTINCT(?prop)) as ?count)
	WHERE {{
  	?item ?prop wd:{placeholder}
  	SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
	}}
	"""
	return query.format_map({"placeholder":placeholder})



def three_placeholders_extract(first,second:str,third,relation:str,constraint:str,first_constraint:bool,constraint_positioning_first:bool):
	if first_constraint:
		if constraint_positioning_first:
			query = """
			SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel ?newThirdLabel
			WHERE {{
			wd:{first} wdt:P31 ?typeFirst.
			wd:{second} wdt:P31 ?typeSecond.
			wd:{third} wdt:P31 ?typeThird.
			?newFirst wdt:P31 ?typeFirst.
			?newSecond wdt:P31 ?typeSecond.
			?newThird wdt:P31 ?typeThird.
			?newFirst wdt:{relation} ?newSecond.
			?newFirst wdt:{constraint} ?newThird
			SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
			}}
			LIMIT 2
			"""
		else:
			query = """
			SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel ?newThirdLabel
			WHERE {{
			wd:{first} wdt:P31 ?typeFirst.
			wd:{second} wdt:P31 ?typeSecond.
			wd:{third} wdt:P31 ?typeThird.
			?newFirst wdt:P31 ?typeFirst.
			?newSecond wdt:P31 ?typeSecond.
			?newThird wdt:P31 ?typeThird.
			?newFirst wdt:{relation} ?newSecond.
			?newThird wdt:{constraint} ?newFirst.
			SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
			}}
			LIMIT 2
			"""
	else:
		if constraint_positioning_first:
			query = """
			SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel ?newThirdLabel
			WHERE {{
			wd:{first} wdt:P31 ?typeFirst.
			wd:{second} wdt:P31 ?typeSecond.
			wd:{third} wdt:P31 ?typeThird.
			?newFirst wdt:P31 ?typeFirst.
			?newSecond wdt:P31 ?typeSecond.
			?newThird wdt:P31 ?typeThird.
			?newFirst wdt:{relation} ?newSecond.
			?newSecond wdt:{constraint} ?newThird
			SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
			}}
			LIMIT 2
			"""
		else:
			query = """
			SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel ?newThirdLabel
			WHERE {{
			wd:{first} wdt:P31 ?typeFirst.
			wd:{second} wdt:P31 ?typeSecond.
			wd:{third} wdt:P31 ?typeThird.
			?newFirst wdt:P31 ?typeFirst.
			?newSecond wdt:P31 ?typeSecond.
			?newThird wdt:P31 ?typeThird.
			?newFirst wdt:{relation} ?newSecond.
			?newThird wdt:{constraint} ?newSecond.
			SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
			}}
			LIMIT 2
			"""

	return query.format_map({"first":first,"second":second,"third":third,"relation":relation,"constraint":constraint})

def expand_failure(first,second):
	
	query = """
		SELECT DISTINCT ?typeFirstLabel ?typeSecondLabel
		WHERE 
		{{
		wd:{first} wdt:P31 ?typeFirst.
		wd:{second} wdt:P31 ?typeSecond.
		SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
		}}
		"""
	return query.format_map({"first":first,"second":second})


def expand_failure_first(first,second,relation,removefirst:bool):
	## failure
	if (removefirst):
		query = """
		SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel
		WHERE 
		{{
		wd:{second} wdt:P31 ?typeSecond.
		?newFirst wdt:P31 ?typeFirst.
		?newSecond wdt:P31 ?typeSecond.
		?newFirst wdt:{relation} ?newSecond.
		SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
		}}
		LIMIT 2
		"""
	else:
		query = """
		SELECT DISTINCT ?newFirstLabel ?newSecondLabel ?typeFirstLabel ?typeSecondLabel
		WHERE 
		{{
		wd:{first} wdt:P31 ?typeFirst.
		?newFirst wdt:P31 ?typeFirst.
		?newSecond wdt:P31 ?typeSecond.
		?newFirst wdt:{relation} ?newSecond.
		SERVICE wikibase:label {{bd:serviceParam wikibase:language "en"}}
		}}
		LIMIT 2
		"""
	return query.format_map({"relation":relation,"first":first,"second":second})
