from pathlib import Path

from jinja2 import Environment, FileSystemLoader

number_summaries = 20
event_name = 'libya_hotel'
path_summaries = Path('data', event_name, 'summaries', 'system')
summaries_files = [file for file in path_summaries.iterdir() if file.is_file()]


def parse_mgraph(path_file):
    with path_file.open('r') as file:
        ids = []
        if path_file.suffix == '.tsv':
            lines = file.readlines()[:number_summaries]
            for line in lines:
                id = line.split('\t')[0]
                if id.find('-') > -1:
                    ids.append(id.split('-')[0])
                else:
                    ids.append(id)
    return ids


def parse_txt_summary(path_file):
    with path_file.open('r') as file:
        return file.readlines()


results_dir = Path('results', event_name)
for file in summaries_files:
    env = Environment(loader=FileSystemLoader('results'), trim_blocks=True)
    if file.name == 'mgraph.tsv':
        file_name = Path(f'mgraph_{number_summaries}.html')
        ids = parse_mgraph(file)
        with (results_dir / file_name).open('w') as f:
            t = env.get_template('baseline_template.html').render(ids=ids, number_summaries=number_summaries,
                                                                  name='mgraph')
            f.write(t)
    else:

        name = file.name[:-4]
        ids = parse_txt_summary(file)
        file_name = Path(name + '.html')
        with (results_dir / file_name).open('w') as f:
            t = env.get_template('baseline_template.html').render(ids=ids, number_summaries=len(ids),
                                                                  name=name)
            f.write(t)
