import re
from pathlib import Path

from sqlalchemy.orm import sessionmaker

import settings
from db.engines import connect_to_server
from db.events import get_documents_from_event

"""
Exports all the documents of a event to a csv file.
Considers only the text
"""

event = "oscar_pistorius"

connect = lambda: connect_to_server(username="lmartinez", host="172.17.69.88", ssh_pkey="/home/luis/.ssh/id_rsa")
with connect() as engine:
    Session = sessionmaker(engine, autocommit=True)
    session = Session()
    documents = get_documents_from_event(event, session)
    print('Number of Docs: {}'.format(len(documents)))
    path_csv = Path(settings.LOCAL_DATA_DIR_2, 'data', event, 'documents.tsv')
    with path_csv.open('w') as csv_file:
        docs_text = [re.sub(r"http\S+", '', doc[0].text.replace('\t', '').replace('\n', '')) + '\n' for doc in documents
                     if len(doc[0].text) > 3]
        docs_unique = list(set(docs_text))
        docs_unique.sort()
        csv_file.writelines(docs_unique)
