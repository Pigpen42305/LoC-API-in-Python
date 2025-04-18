"""
This module contains the functions that will set up the files needed for the other modules
"""
import json
import time
import requests
from .path_manager import *
from os import mkdir


def get_loc_json():
    truestart = time.perf_counter()

    collection:str = 'https://www.loc.gov/collections/civil-rights-history-project/'

    pages = []
    for num in range(1,8):
        start = time.perf_counter()
        response = requests.get(f'{collection}?fo=json&sp={num}').json()
        pages.append(response)
        time.sleep(3)
        end = time.perf_counter()
        minutes,seconds = divmod(int(end - start),60)
        print(f"Page {num} completed in {minutes:01}:{seconds:02}")


    for index,data in enumerate(pages):
        with open(PAGE_FILES[index],'w') as file:
            json.dump(data,file,indent=4)
    
    trueend = time.perf_counter()
    minutes,seconds = divmod(int(trueend - truestart),60)
    print(f"7 json files saved in {minutes:01}:{seconds:02}")


def short_page(jsonfile,*save_keys):
        
    for index,jsonfile in enumerate(PAGE_FILES):
        with open(jsonfile,'r') as file:
            data:dict = json.load(file)
        
        delete_keys = set(data.keys()) - set(save_keys)
        for key in delete_keys: del data[key]
        
        with open(SHORT_PAGE_FILES[index],'w') as file:
            json.dump(data,file,indent=4)

        print(f'_{index + 1}_page.json was saved!')

def MAIN(*significant_keys):
    if len(significant_keys) == 0: significant_keys = ('results',)

    try:
        to_pages()
    except FileNotFoundError:
        mkdir("PAGES")
        get_loc_json()
        to_pages()
    except Exception as Error:
        log_error(Error)
        raise

    short_page(PAGE_FILES,*significant_keys)
    to_start()

if __name__ == '__main__': MAIN()
  