"""
This module contains the functions that will set up the files needed for the other modules
"""
import json
import os
import time
from requests_verify import *

def get_loc_json():
    truestart = time.perf_counter()
    DIR = os.getcwd()

    if os.getcwd() != os.path.dirname(__file__): 
        os.chdir(os.path.dirname(__file__))

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

    if not os.path.exists("PAGES"): os.mkdir("PAGES")
    
    os.chdir("PAGES")

    files = []
    for index,data in enumerate(pages,1):
        with open(f'{index}_page.json','w',encoding='utf-8') as file:
            json.dump(data,file,indent=4)
            files.append(f'{index}_page.json')
    
    trueend = time.perf_counter()
    minutes,seconds = divmod(int(trueend - truestart),60)
    print(f"{len(files)} json files saved in {minutes:01}:{seconds:02}")
    os.chdir(DIR)
    return files

def short_page(jsonfile,*save_keys):

    if isinstance(jsonfile,list):
        outputs = []
        for JSONFILE in jsonfile:
            outputs.append(short_page(JSONFILE,*save_keys))
        return outputs
        

    DIR = os.getcwd()
    if os.getcwd() != os.path.dirname(__file__): 
        os.chdir(os.path.dirname(__file__))
    
    if not os.path.exists("PAGES"): raise FileNotFoundError("NO PAGES FOLDER FOUND IN SCRIPT DIRECTORY")
    os.chdir("PAGES")

    with open(jsonfile,'r',encoding='utf-8') as file:
        data:dict = json.load(file)
    
    delete_keys = set(data.keys()) - set(save_keys)

    for key in delete_keys:
        del data[key]
    
    with open(f'_{jsonfile}','w',encoding='utf-8') as file:
        json.dump(data,file,indent=4)

    os.chdir(DIR)
    print(f'_{jsonfile} was saved!')
    return f'_{jsonfile}'

def MAIN():
    significant_keys = (
        'results',
    )

    DIR = os.getcwd()
    if os.getcwd() != os.path.dirname(__file__): 
        os.chdir(os.path.dirname(__file__))

    if not os.path.exists("PAGES") and REQUESTS_ENABLED: 
        filelist = get_loc_json()
        os.chdir("PAGES")
    elif os.path.exists("PAGES"):
        os.chdir("PAGES")
        filelist = os.listdir()
    else:
        raise ModuleNotFoundError("First run requires the requests module!")

    for jsonpath in filter(lambda x: not x.startswith('_'),filelist):
        short_page(jsonpath,*significant_keys)
    
    os.chdir(DIR)

if __name__ == '__main__': MAIN()
  