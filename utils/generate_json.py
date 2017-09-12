"""
Export the documents/tweets of an event in JSON format. This will export only the name of the event
and the text without pre-processing of each document/tweet.
"""


# def generate_json(event_name):
#     print("Generating JSON for {}".format(event_name))
#     event_ids = get_event_ids(event_name)
#     docs = get_documents(event_ids)
#     data = {'topic': event_name.replace('_',' ')}
#     docs_texts = [doc.url for doc in docs]
#     data['tweets'] = docs_texts
#     with open(event_name+'.txt','w') as file:
#         json.dump(data, file)
#
#
# generate_json('libya_hotel')
# generate_json('oscar_pistorius')
