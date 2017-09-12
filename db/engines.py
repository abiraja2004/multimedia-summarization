from sqlalchemy import create_engine

engine = create_engine('mysql://bnews_user:ur5Eesiedie3ja6ahkiX@localhost/breakingnews', encoding='utf-8')
engine_mquezada = create_engine('mysql://root@localhost/ams?charset=utf8mb4', encoding='utf-8')
engine_lmartine = create_engine('mysql://root:oracle_753@localhost/ams')
engine_m3 = create_engine('mysql://mquezada:phoophoh7ahdaiJahphoh3aicooz7uka3ahJe9oi@127.0.0.1/mquezada_db')

engine_of215 = create_engine('mysql://root@localhost/twitter_news?charset=utf8mb4', encoding='utf-8')