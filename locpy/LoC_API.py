"""
LoC_API_Requests does the following when imported:
1) Checks for DATA.pkl:
    - Checks for PAGES:
        - If found, uses the json to populate the EntryData class attributes
        - If not found, calls the LOCGetter module to get new data from the Library of Congress site and organize it
    - Pickles EntryData's class attributes after all instances have be created
2) Unpickles DATA.pkl
3) Returns EntryData with the pickled data in the class attributes
"""

from .path_manager import *
from functools import partial
import builtins

print = partial(builtins.print,end='',flush=True)

print("\rPreparing LoC_API...\n")

from os.path import exists
from pickle import (
    Pickler,
    Unpickler,
)

def _setup() -> None:
    "See below for the docstring"
    from .EntryDataPy import EntryData
    try:
        to_pages()
    except FileNotFoundError as Error:
        log_error(Error)
        raise

    for filename in SHORT_PAGE_FILES:
        with open(filename,'r') as file:
            EntryData(file)
    
    print("\rPickling data...")
    Pickler(open(DATA_PKL,'wb'),5).dump(EntryData(None))
    print("\rPickling complete!\n")

# Here, the docstring for _setup is set. 
# This f-string cannot be evaluated during function declaration, so I set it afterwards.
setattr(_setup,'__doc__',
        f"""If the "PAGES" folder exists in this your directory ({STARTING_DIRECTORY}):
1) Iterates through the cleaned files
2) Calls the EntryData constructor on each cleaned json file
3) Pickles and saves the EntryData information in "{DATA_PKL}"
4) returns None

If "PAGES" is not found, raises FileNotFoundError"""
)

def _main() -> None:
    """
    Sets up LoC_API_Requests.

    - If DATA.pkl is not found, tries to make it from the PAGES
    - If the PAGES folder is not found, calls LOCGetter.MAIN()

    The result is the creation of the files needed for
    """
    print("\rRUNNING LoC_API._main()...\n")
    if not exists(DATA_PKL):          # if the DATA.pkl does not exist, try to create it
        print(f'\rNO DATA.pkl FOUND IN "{STARTING_DIRECTORY}", CREATING DATA.pkl...')
        if not exists(PAGES_DIRECTORY):         # if the PAGES are not found, try to get the data again
            print(f'\rNO "PAGES" FILE FOUND IN "{STARTING_DIRECTORY}", CREATING PAGES...\n')
            from .LOCGetter import MAIN
            print("GETTING DATA...\n")
            MAIN()                        # Sends 7 HTTP requests to the LoC json API, and processes the results
            print("RETRIEVED!\n")
        else: print()
        print("\rPICKLING DATA...")
        _setup()                          # Puts the data together in the EntryData class, and makes DATA.pkl
        print("\rPICKLING SUCCESSFUL!\n")

def _final():
    """
    Runs after _main(), unpickles the pickled data, and returns the EntryData class after unpickling
    """
    from .EntryDataPy import EntryData     # import the class again (empty definition)

    # If the DATA.pkl exists, unpickle the data

    # Unpickle the data
    print("\rUnpickling data...")
    try:
        Unpickler(open(DATA_PKL,'rb')).load()
    except Exception as Error: # If an exception occurs at this point, we are cooked. Create an error.txt and raise the exception
        log_error(Error)
    else:
        print("\rUnpickling complete!\n")
    
    print("LoC_API._main() HAS FINISHED SETTING UP!\n")
    return EntryData # Return the class

def main():
    _main()
    EntryData = _final()
    print("\rEntryData prepared!\n")
    return EntryData

if __name__ == '__main__': main()