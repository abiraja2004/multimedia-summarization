import re
from pathlib import Path

from sqlalchemy.orm import sessionmaker

import settings
from db.engines import engine_lmartine as engine
from db.events import get_documents_from_event

"""
Exports all the documents of a event to a csv file.
Considers only the text of the documents
"""

event = "oscar_pistorius"

Session = sessionmaker(engine, autocommit=True)
session = Session()
documents = get_documents_from_event(event, session)
print('Number of Docs: {}'.format(len(documents)))
path_csv = Path(settings.LOCAL_DATA_DIR_2, 'data', event, f'documents_{event}.csv')
with path_csv.open('w') as csv_file:
    docs_text = [doc[0].text.replace('\t', '').replace('\n', '') + '\n' for doc in
                 documents]
    #docs_unique = list(set(docs_text))
    #print(len(docs_unique))
    csv_file.writelines(docs_text)
