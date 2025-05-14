"""
Will get all of the transcripts that actually work.
The transcripts will be saved in a folder called 'TRANSCRIPTS'
The items must provide resources, and a transcript in those resources with a fulltext url.
"""
from os import chdir,mkdir

import requests

try:
    chdir('TRANSCRIPTS')
except FileNotFoundError:
    mkdir('TRANSCRIPTS')
    chdir('TRANSCRIPTS')

from locpy import EntryData


""" # If something doesn't work, put a # in front of this line!

# Put the index that failed or a enough of the title to find the item
SPECIFIC_ENTRY: int | str = 41

item = EntryData.entry(SPECIFIC_ENTRY)
item.get_transcript(item.title + '.txt',timeout=10)
exit()
# """

skipped = []
for title,item in EntryData.title_instances.items():
    try:
        item.get_transcript(title + '.txt',timeout=5)
    except NotImplementedError:
        pass
    except KeyError:
        print(f'\r<--{item.index} RAISES AN ERROR!!!-->')
    except requests.exceptions.ReadTimeout:
        skipped.append((title,item))
        print(f'\r<--{item.index} SKIPPED FOR NOW-->')

I = 0
while len(skipped) > 0:
    current = skipped.copy()
    skipped = []
    for title,item in current:
        try:
            item.get_transcript(title + '.txt',timeout=10)
        except NotImplementedError:
            pass
        except requests.exceptions.ReadTimeout:
            skipped.append((title,item))
            print(f'\r<--{item.index} SKIPPED FOR NOW-->')
    if current == skipped:
        I += 1
    else:
        I = 0
    if I >= 10:
        raise TimeoutError(f"Retries to get these items have made no progress!: {[i.index for _,i in skipped]}")