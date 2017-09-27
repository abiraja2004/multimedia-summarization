"""
Queries related to clusters
"""
from db.models_new import DocumentCluster, Document, Cluster


def get_documents_cluster(cluster_id, n_clusters, session):
    """
    :param session:
    :param cluster_id:
    :param n_clusters:
    :return:
    """
    q_docs = session.query(DocumentCluster.label, Document). \
        join(Document, DocumentCluster.document_id == Document.id). \
        join(Cluster, Cluster.id == DocumentCluster.cluster_id). \
        filter(DocumentCluster.cluster_id == cluster_id). \
        filter(Cluster.n_clusters == n_clusters). \
        all()

    return q_docs
