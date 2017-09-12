"""
Queries related to clusters
"""
from db.models_new import DocumentCluster, Document, Cluster, Tweet, DocumentTweet


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


def get_clusters_event(event_id_id, session):
    # get all the clusters methods for a specific event.
    q_tweet = session.query(Tweet.tweet_id).filter(Tweet.event_id_id == event_id_id).first()
    q_doc = session.query(DocumentTweet.document_id).filter(DocumentTweet.tweet_id == q_tweet[0]).first()
    q_clusters = session.query(DocumentCluster.cluster_id).filter(DocumentCluster.document_id == q_doc[0]).all()
    clusters_ids = [x[0] for x in q_clusters]
    clusters = session.query(Cluster).filter(Cluster.id.in_(clusters_ids)).all()
    return clusters
