from sqlalchemy import create_engine

engine = create_engine('mysql://bnews_user:ur5Eesiedie3ja6ahkiX@localhost/breakingnews', encoding='utf-8')
engine_mquezada = create_engine('mysql://root@localhost/ams?charset=utf8mb4', encoding='utf-8')
engine_lmartine = create_engine('mysql://root:oracle_753@localhost/ams')
engine_m3 = create_engine('mysql://mquezada:phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi@127.0.0.1/mquezada_db')

engine_of215 = create_engine('mysql://root@localhost/twitter_news?charset=utf8mb4', encoding='utf-8')


def connect_from_rafike(username, password):
    from sshtunnel import SSHTunnelForwarder
    HOST = '172.17.69.88'

    server = SSHTunnelForwarder(
        (HOST, 22),
        ssh_password=password,
        ssh_username=username,
        remote_bind_address=('127.0.0.1', 3306))
    server.start()

    engine_rafike = create_engine(f'mysql://root@127.0.0.1:{server.local_bind_port}/twitter_news?charset=utf8mb4',
                                  encoding='utf-8')

    return server, engine_rafike