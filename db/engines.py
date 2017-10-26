from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

engine = create_engine('mysql://bnews_user:ur5Eesiedie3ja6ahkiX@localhost/breakingnews', encoding='utf-8')
engine_mquezada = create_engine('mysql://root@localhost/ams?charset=utf8mb4', encoding='utf-8')
engine_lmartine = create_engine('mysql://root:oracle_753@localhost/twitter_news')
engine_m3 = create_engine('mysql://mquezada:phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi@127.0.0.1/mquezada_db')

engine_of215 = create_engine('mysql://root@localhost/twitter_news?charset=utf8mb4', encoding='utf-8')


def connect_to_server(username, host, db_user="root", db_name="twitter_news", db_password=""):
    server = SSHTunnelForwarder(
        (host, 22),
        ssh_pkey="/home/mquezada/.ssh/id_rsa",
        ssh_username=username,
        remote_bind_address=('127.0.0.1', 3306))
    server.start()

    engine = create_engine(f'mysql://{db_user}:{db_password}@127.0.0.1:{server.local_bind_port}'
                           f'/{db_name}?charset=utf8mb4',
                           encoding='utf-8')

    return server, engine
