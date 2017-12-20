import sys
from pathlib import Path

'''Cuantos tweets iguales del summary_1 hay en summary_2'''

LOCAL_DATA_DIR_2 = Path('/home', 'luism', 'PycharmProjects', 'multimedia-summarization')

if __name__ == '__main__':
    event_name = sys.argv[1]
    summary_1_name = sys.argv[2]
    summary_2_name = sys.argv[3]
    path_to_summaries = Path(LOCAL_DATA_DIR_2, 'data', event_name, 'summaries', 'system', 'text')
    with Path(path_to_summaries, summary_1_name).open('r') as summary_1, Path(path_to_summaries, summary_2_name).open('r') as summary_2:
        lines_1= summary_1.readlines()
        lines_2 = summary_2.readlines()
        count = 0
        for line_1 in lines_1:
            for line_2 in lines_2:
                if line_1 == line_2:
                    count = count + 1
    print(count)