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
PRINTING = True
if PRINTING: print("Preparing LoC_API_Requests...")
from os import (
    getcwd as CWD, 
    chdir as CD,
)
from os.path import (
    dirname as DIR,
    exists as is_found,
    join as join_path,
)
from pickle import (
    Pickler,
    Unpickler,
)

START = CWD()
END = DIR(__file__)

def _change(script_start:bool) -> None:
    """
    When called with a boolean value:
    - If called with True: Changes current working directory to the directory of this script
    - If called with False: Changes current working directory to the directory that was the current working directory at the start of this script
    - Otherwise, raises TypeError

    If trying to change the directory to the current working directory, does nothing.

    Returns None"""
    if not isinstance(script_start,bool):
        raise TypeError(f"{script_start = } is not type bool")
    
    if script_start and CWD() != END:
        CD(END)
    elif CWD() != START:
        CD(START)

def _setup() -> None:
    "See below for the docstring"
    from EntryDataPy import EntryData
    _change(True)
    if is_found("PAGES"):
        CD("PAGES")
    else:
        raise FileNotFoundError(f'No PAGES folder was found in "{CWD()}!"')

    for i in range(1,8):
        with open(f"_{i}_page.json",'r',encoding='utf-8') as file:
            EntryData(file)
    
    _change(True)
    if PRINTING: print("Pickling data...")
    Pickler(open('DATA.pkl','wb'),5).dump(EntryData(None))
    if PRINTING: print("Pickling complete!")
    _change(False)

# Here, the docstring for _setup is set. 
# This f-string cannot be evaluated during function declaration, so I set it afterwards.
setattr(_setup,'__doc__',
        f"""If the "PAGES" folder exists in this script's directory ({END}):
1) Iterates through the cleaned files ({tuple(range(1,8))})
2) Calls the EntryData constructor on each cleaned json file
3) Pickles and saves the EntryData information in "{join_path(END,"DATA.pkl")}"
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
    if PRINTING: print("RUNNING LoC_API_Requests.main()...")
    _change(True)
    if not is_found("DATA.pkl"):          # if the DATA.pkl does not exist, try to create it
        if PRINTING: print(f'  NO DATA.pkl FOUND IN "{CWD()}", CREATING DATA.pkl...')
        if not is_found("PAGES"):         # if the PAGES are not found, try to get the data again
            if PRINTING: print(f'    NO "PAGES" FILE FOUND IN "{CWD()}", CREATING PAGES...')
            _change(False)
            from LOCGetter import MAIN
            if PRINTING: print("    GETTING DATA...")
            MAIN()                        # Sends 7 HTTP requests to the LoC json API, and processes the results
            if PRINTING: 
                print("    RETRIEVED!")
                print("    JSON DATA SAVED TO PAGES SUCCESSFULLY!")
        if PRINTING: print("  PICKLING DATA...")
        _setup()                          # Puts the data together in the EntryData class, and makes DATA.pkl
        if PRINTING: print("  PICKLING SUCCESSFUL!")
        if PRINTING: print("  DATA.pkl CREATED SUCCESSFULLY!")

def _final():
    """
    Runs after _main(), unpickles the pickled data, and returns the EntryData class after unpickling
    """
    from EntryDataPy import EntryData     # import the class again (empty definition)

    # If the DATA.pkl exists, unpickle the data

    _change(True)
    # Unpickle the data
    if PRINTING: print("Unpickling data...")
    try:
        Unpickler(open('DATA.pkl','rb')).load()
    except Exception as E: # If an exception occurs at this point, we are cooked. Create an error.txt and raise the exception
        with open('error.txt','w') as file:
            print(repr(E),file = file,flush = True)
    else:
        if PRINTING: print("Unpickling complete!")
    finally:
        _change(False)
    
    if PRINTING: print("LoC_API_Requests.main() HAS FINISHED SETTING UP!")
    return EntryData # Return the class

_main()
EntryData = _final()
if PRINTING: print("LoC_API_Requests prepared!")