"""
Insert a new cluster in the DB.
Needs a file with the documents and a file with the labels for the clusters
"""
from pathlib import Path

from sqlalchemy.orm import sessionmaker

import settings
from db.models_new import Cluster, DocumentCluster


def insert_clustering_db(clustering, n_clusters):
    cluster = Cluster(method=clustering, n_clusters=n_clusters)
    session.add(cluster)
    session.commit()
    print('Cluster insertado: {}'.format(cluster.id))
    # Inserta un nuevo tipo de clustering en la BD.
    return cluster.id


def insert_labels_db(document_cluster):
    session.bulk_save_objects(document_cluster)
    session.commit()


if __name__ == '__main__':
    Session = sessionmaker(bind=settings.engine, expire_on_commit=False)
    session = Session()
    event_name = 'nepal_earthquake'
    clustering = 'Hierchical'
    path_file_cluster = Path(settings.LOCAL_DATA_DIR_2, 'data', event_name, 'clusters', clustering)
    files = [x.name for x in path_file_cluster.iterdir() if x.is_file() and x.suffix != '.pickle']
    docs = files.pop(files.index(event_name + '_docs.txt'))
    for file in files:
        tokens = file.split('.')
        id_cluster = insert_clustering_db(tokens[2], tokens[3])
        path_labels = Path(path_file_cluster, file)
        path_docs = Path(path_file_cluster, docs)
        docs_labels = []
        with path_labels.open() as file_1, path_docs.open() as file_2:
            for (doc, label) in zip(file_2, file_1):
                doc_id = doc.split('\t')[0]
                label = label.strip()
                doc_cluster = DocumentCluster(document_id=doc_id, cluster_id=id_cluster, label=label)
                docs_labels.append(doc_cluster)
        insert_labels_db(docs_labels)
