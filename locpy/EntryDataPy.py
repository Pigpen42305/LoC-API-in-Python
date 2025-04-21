"""
This module defines the EntryData class, and is required to unpickle the data in DATA.pkl
To implement new features, define ne
"""
from io import TextIOWrapper
from os import PathLike, path, getcwd
from types import NoneType
from typing import Any
import json
import re
from charset_normalizer.api import from_bytes
from time import sleep
import requests
from .path_manager import *

class ReprOverride(type):
    """A very simple metaclass to allow us to print the class itself"""
    def __repr__(cls):
        return json.dumps(cls._printable,indent = 4,default=(lambda x: repr(x)))

class EntryData(object,metaclass = ReprOverride):
    """
    This class does a few things:
    1) Limits the number of calls to the constructor to 1_000_000_000 calls in one session.
        - This is to stop infinite loops if something was broken in the implementation.
    2) Keeps track of the instances created (via class attributes):
        - Titles mapped to instances
        - Indices mapped to instances
        - Indices mapped to titles
        - If you subscript the class (EntryData[index or title]), then 
    3) Filters out unneeded keys from the source json (via class attributes):
        - LIST contains a list of keys to use for filtering
        - MODE is a boolean:
            - True to whitelist the keys in LIST
            - False to blacklist the keys in LIST
    4) If you try to print the EntryData class itself, a json-formatted string is returned for printing:
        - This prints the instance tracking
    5) Has pickling support:
        - Call the pickler on EntryData(None), which makes an uninitialized instance of EntryData
        - When unpickling, an empty instance is returned. The data is accessed from the instance tracking, which was unpickled too
    6) Multiple ways to initialize:
        1) From a file/filename/filepath:
            - Expects a json file
                - Expects that the json has already been cleaned up by running `LOCGetter.py`
            - Can be an open TextIOWrapper that is readable (to read from the start)
            - Can be a string with the filename, or it's path, relative or absolute
            - Can be a PathLike object, similar to the string
    """
    # True whitelist, False blacklist
    MODE:bool = False

    # Keys to use for whitelist/blacklist
    LIST:list[str] = [
        'SOME_PLACEHOLDER_KEY_TO_EXCLUDE',
    ]

    title_instances:dict[str,"EntryData"] = {} # maps titles to EntryData instances
    index_instances:dict[int,"EntryData"] = {} # maps indices to EntryData instances
    index_title    :dict[int,str]         = {} # maps indices to titles
    i = 0
    
    # list of source json for pickling
    _json_data:list[dict] = []

    _printable:dict[str,dict] = {
        "title_instances":title_instances,
        "index_instances":index_instances,
        "index_title":index_title
    }

    def __new__(cls,jsonfile = None,*args):
        cls.i += 1
        if cls.i > 1_000_000_000:
            raise RecursionError("1,000,000,000 calls to EntryData.__new__()!!!\nThere may be unintended recursion occurring in the implementation!")

        if isinstance(jsonfile,(PathLike,str,TextIOWrapper)):
            cls._get_entries(jsonfile)
            return EntryData

        elif jsonfile is None and len(args) == 3:
            cls._json_data = args[0]
            cls.MODE = args[1]
            cls.LIST = args[2]
            return super().__new__(cls)
        
        elif isinstance(jsonfile,(dict,NoneType)): return super().__new__(cls)

    def __init__(self,jsondata:dict[str,Any]|list[dict]|None,*args):
        cls = EntryData

        if jsondata is None: return
        if self is cls: return

        self.json = jsondata # type:dict[str,Any]
        if len(args) == 0: cls._json_data.append(jsondata)

        def listfilter(x):
            if cls.MODE: return x in cls.LIST
            else       : return x not in cls.LIST

        for key,value in self.items():
            if listfilter(key): setattr(self,key,value)
        
        self.name     = getattr(self,'title',None) # type:str|NoneType
        self.metadata = getattr(self,'item', None) # type:dict[str,list[str]|str]|NoneType
    
    def __iter__(self): return self.json.keys()
            
    def __getitem__(self,key): return self.json[key]
    
    def keys(self): return self.json.keys()
    
    def values(self): return self.json.values()
    
    def items(self): return self.json.items()

    def make_json(self,filename): json.dump(self.json,open(filename,'w'),indent=4)
    
    def __str__(self):
        try                  : return f"EntryData[{self.index}] is: {self.name}"
        except AttributeError: return repr(self)
    
    def __repr__(self):
        try                  : return f'EntryData.entry({self.index})'
        except AttributeError: return f'<EntryData object at {id(self)}>'

    @classmethod
    def entry(cls,key:int|str) -> "EntryData":

        if   isinstance(key,int): return cls.index_instances[key]
        if   isinstance(key,str): 
            try: return cls.title_instances[key]
            except KeyError as Error:
                for _key,inst in cls.title_instances.items():
                    if key.lower() in _key.lower():
                        return inst
                else:
                    raise

    @staticmethod
    def _get_entries(jsonfile:TextIOWrapper|PathLike|str):

        if isinstance(jsonfile,TextIOWrapper) and jsonfile.readable():
            jsonfile.seek(0)
            jsondata:dict = json.load(jsonfile)
        elif isinstance(jsonfile,(PathLike,str)) and path.exists(jsonfile):
            with open(jsonfile,'r') as file:
                jsondata:dict = json.load(file)
            del file
        else:
            log_error(FileNotFoundError(f"Could not find a file for {jsonfile = }"))

        for instance in map(EntryData,jsondata['results']):
            EntryData.title_instances[instance.name ] = instance
            EntryData.index_instances[instance.index] = instance
            EntryData.index_title[instance.index]     = instance.name
    
    def __setstate__(self,state):
        cls = EntryData
        if state['holder'] is not None: 
            raise Exception(f"got an unexpected state!")

        for self in map(lambda x: cls(x,None),cls._json_data):
            cls.title_instances[self.name ] = self
            cls.index_instances[self.index] = self
            cls.index_title[self.index]     = self.name

    def __reduce__(self):
        return (
        self.__class__,
        (None,EntryData._json_data,EntryData.MODE,EntryData.LIST),
        {'holder':None}
        )
    
    class _transcript_helpers:

        @staticmethod
        def process_xml(data:bytes) -> tuple[bytes,str]:
            
            patterns = {
                'tags':br'<[^>]+>',          # Removes xml tags
                'page':br'(0{2}\d{2})',      # Removes page indicators
                'time':br'\n\d\d:\d\d:\d\d', # Removes timestamps
                'file':br'\[[^\]]+\]',       # Finds anything in square brackets
            }

            # Remove matches to the removal patterns
            for pattern,target in patterns.items():
                if pattern == 'file':
                    bracketed = set(re.findall(target,data))                      # Make a set of items that are in bracketed
                    file_changes = filter(lambda x:b'_' in x,bracketed)           # Filter out transcript context marks, leaving file change markers
                    for element in file_changes: data = data.replace(element,b'') # Remove file change markers
                else:
                    data = re.sub(target,b'',data)

            # Remove the HTML comment at the top
            data = data.replace(b'-->',b'',1)
            data = data[data.find(b'-->') + 3:]

            # Remove leading and trailing whitespace
            data = data.strip()

            # Gather up the names, and mark with \x00 at the start, and sort
            names = set()
            for line in data.split(b'\n'):
                if b':' in line:
                    name = line.strip().partition(b':')[0] + b': '
                    if name.isupper():
                        names.add(b'\x00' + name)
            names = sorted(list(names),key=len)
            for name in names:
                for char in {b'. ',b'? ',b', ',b'! ',b'\n'}:
                    data = data.replace(char + name[1:],char.strip() + name)

            # Remove all remaining newlines
            data = data.replace(b'\n',b'')

            # Replace the \x00 marks to separate by conversation turns
            data = data.replace(b'\x00',b'\n\n')

            # Remove all repeated spaces
            while b'  ' in data:
                data = data.replace(b'  ',b' ')

            # Clean up before trimming
            data = data.strip()

            # Trim metadata
            datalist = data.split(b'\n')
            del datalist[0:2]
            
            # Separate the final line by 'sentences'.
            # Remove any improper sentences to trim metadata 
            def filtering(data:tuple[int,bytes]):
                i,x = data
                conditions = [
                    not x.endswith(b'Inc'),
                    (x.startswith(b' ') or i == 0),
                    not (x.isupper() and x.islower()),
                    b'www' not in x,
                ]
                return all(conditions)
            finalline = datalist[-1].split(b'.')
            final = dict(filter(filtering,enumerate(finalline)))

            # Reconnect the data
            datalist[-1] = b'.'.join(final.values()) + b'.'
            data = b'\n'.join(datalist)

            return (data,from_bytes(data)[0].encoding)

        @staticmethod
        def decoder(content:bytes,encoding:str) -> str: 
            return content.decode(
                encoding=encoding,
                errors='backslashreplace'
            )

        @classmethod
        def _save_transcript(cls,xml:bytes,filename:str) -> None:
            text,encoding = cls.process_xml(xml)
            with open(filename,'w',encoding='utf_8',errors='backslashreplace') as file:
                print(encoding,end='',file=file) # Write the encoding in utf_8 first
                if encoding == 'utf_8': # If the encoding is utf_8, write the rest now
                    print(
                        '\n\n\n',
                        cls.decoder(text,encoding),
                        sep='',
                        file=file,
                    )
            if encoding != 'utf_8': # If the encoding is not utf_8, reopen and write the rest
                with open(filename,'a',encoding=encoding,errors='backslashreplace') as file:
                    print(
                        '\n\n\n',
                        cls.decoder(text,encoding),
                        sep='',
                        file=file,
                    )

    def get_transcript(self,file:PathLike|str):
        cls = EntryData
        helpers = cls._transcript_helpers
        for resource in self.json['resources']:
            if 'transcript' in resource['caption']:
                resp = requests.get(resource["fulltext"])
                sleep(2)
                return helpers._save_transcript(resp.content,file)
        else:
            Error = KeyError(f"No transcript found for {self}")
            Error.add_note(json.dumps(self.json,indent=4))
            log_error(Error)

    @staticmethod
    def read_transcript(filename:PathLike|str) -> TextIOWrapper:
        try: 
            file = open(filename,'r',encoding = 'utf_8')
        except FileNotFoundError as Error:
            Error.add_note(f"Current working directory = {getcwd()}")
            Error.add_note(f"{filename = }")
            log_error(Error)
        encoding = file.readline().strip()
        if encoding != 'utf_8':
            file.reconfigure(encoding=encoding,errors='backslashreplace')
        file.seek(0)
        return file
    
    def open(
        self_or_cls,
        filename:PathLike|str,
        get_new:bool = False,
        ):
        if not isinstance(get_new,bool):
            log_error(TypeError(f"get_new should be of type bool, not {type(get_new)}"))
        if get_new:
            if not isinstance(self_or_cls,EntryData):
                log_error(AttributeError("You cannot call EntryData.open on the class if get_new is set to True"))
            self_or_cls.get_transcript(filename)
            return self_or_cls.open(filename)
        else:
            return self_or_cls.read_transcript(filename)
        
if __name__ == '__main__':
   # Test code
   pass
