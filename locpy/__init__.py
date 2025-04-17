import os

FIRST_DIR = os.getcwd()

try: 
    from LoC_API import EntryData
except Exception as Error:
    print(repr(Error,file = open(os.path.dirname(__file__),'w')))

if os.getcwd() != FIRST_DIR:
    os.chdir(FIRST_DIR)
del os,FIRST_DIR


