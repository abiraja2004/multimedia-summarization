from pathlib import Path
from bs4 import BeautifulSoup
import settings

event_names = ['libya_hotel', 'oscar_pistorius', 'nepal_earthquake', 'hurricane_irma2']
for name in event_names:
    path_html_files = Path(settings.LOCAL_DATA_DIR_2, 'results', name)
    path_summary_ids = Path(settings.LOCAL_DATA_DIR_2, 'data', name, 'ids')
    list_files = [file for file in path_html_files.iterdir() if file.is_file()]
    for file in list_files:
        name = file.name[file.name.index('_')+1:-5]
        with file.open('r') as summary_html, Path(path_summary_ids, name+'.txt').open('w') as summary_ids:
            soup = BeautifulSoup(summary_html, 'html.parser')
            links = soup.find_all('a')
            for link in links:
                href = link['href'].split('/')[-1]
                summary_ids.write(href + '\n')