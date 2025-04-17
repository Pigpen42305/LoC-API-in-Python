import os

FIRST_DIR = os.getcwd()

try: 
    from LoC_API import EntryData
except Exception as Error:
    print(repr(Error,file = open(os.path.join(os.path.dirname(__file__),'loc_error.txt'),'w')))
    exit("AN ERROR OCCURRED")


if os.getcwd() != FIRST_DIR:
    os.chdir(FIRST_DIR)
del os,FIRST_DIR

__all__ = [
    'EntryData',
]
