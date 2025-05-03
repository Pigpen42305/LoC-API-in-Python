import os
from charset_normalizer.api import from_bytes
from typing import Never

__all__ = [
    'to_start',
    'to_package',
    'to_pages',
    'log_error',
    'final_log_error',
    'DATA_PKL',
    'SHORT_PAGE_FILES',
    'PAGE_FILES',
    'STARTING_DIRECTORY',
    'PACKAGE_DIRECTORY',
    'PAGES_DIRECTORY',
    'ERROR_FILE',
]

STARTING_DIRECTORY = os.getcwd()
PACKAGE_DIRECTORY = os.path.dirname(__file__)
PAGES_DIRECTORY = os.path.join(STARTING_DIRECTORY,"PAGES")
PAGE_FILES = [os.path.join(PAGES_DIRECTORY,f"{i}_page.json") for i in range(1,8)]
SHORT_PAGE_FILES = [os.path.join(PAGES_DIRECTORY,f"_{i}_page.json") for i in range(1,8)]

DATA_PKL = os.path.join(STARTING_DIRECTORY,'DATA.pkl')
ERROR_FILE = os.path.join(STARTING_DIRECTORY,"ERROR_LOG.txt")

def _change(directory):
    def __change():
        if os.getcwd() != directory:
            os.chdir(directory)
    return __change

def to_start(): _change(STARTING_DIRECTORY)
def to_package(): _change(PACKAGE_DIRECTORY)
def to_pages():
    if os.path.exists(PAGES_DIRECTORY):
        _change(PAGES_DIRECTORY)()
    else:
        Error = FileNotFoundError(f'The file "{PAGES_DIRECTORY}" does not exist!')
        log_error(Error)
        raise Error

def log_error(error:Exception|None,bytedata:bytes|None = None,encoding:str|None = None) -> Never|None:
    if isinstance(error,Exception):
        to_start()

        if (encoding is None) and (bytedata is not None):
            encoding_type = from_bytes(bytedata,threshold=0.5).best().encoding
        else:
            encoding_type = encoding
        
        with open(ERROR_FILE,'w',encoding=encoding_type) as ErrorFile:
            print("SCRIPT ERROR:\n",file=ErrorFile)
            print(repr(error),error,sep='\n',file=ErrorFile)
            if bytedata is not None:
                print("SAVED DATA:\n",file=ErrorFile)
                print(bytedata.decode(encoding_type),file=ErrorFile)
        
        raise error

def final_log_error(error:Exception|None,bytedata:bytes|None = None,encoding:str|None = None) -> Never|None:
    if isinstance(error,Exception):
        log_error(error,bytedata,encoding)
        exit(1)
