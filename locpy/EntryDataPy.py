"""
This module defines the EntryData class, and is required to unpickle the data in DATA.pkl
To implement new features, define ne
"""
from io import TextIOWrapper
from os import PathLike, path, getcwd
from types import NoneType
from typing import Any
import json
import xml.etree.ElementTree as ET
from time import sleep
import requests

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
        
    def __setitem__(self,key,value): self.json[key] = value
    
    def __getitem__(self,key): return self.json[key]

    def __delitem__(self,key): del self.json[key]
    
    def keys(self): return self.json.keys()
    
    def values(self): return self.json.values()
    
    def items(self): return self.json.items()

    def make_json(self): json.dump(self.json,open('check.json','w'),indent=4)
    
    def __str__(self):
        try                  : return f"EntryData[{self.index}] is: {self.name}"
        except AttributeError: return repr(self)
    
    def __repr__(self):
        try                  : return f'EntryData({self.index})'
        except AttributeError: return f'<EntryData object at {id(self)}>'

    def __class_getitem__(cls,key:int|str) -> list["EntryData"]:

        if   isinstance(key,int): return cls.index_instances[key]
        if   isinstance(key,str): 
            try: return cls.title_instances[key]
            except KeyError:
                for _key,inst in cls.title_instances.items():
                    if _key in key:
                        return inst
                else:
                    raise
        raise TypeError(f"Indexes must be type str or type int, not {type(key)}")

    @classmethod
    def _file_from_int(cls,index:int,*deeper_path,check_existence:bool = False,use_cwd:bool = True) -> str:
        "Returns the name of the file at that index. Note that the files are indexed 1 to n.\n" + \
        "This method make no checks for file existence by default, but index must be > 0, with type of int.\n" + \
        "If check_existance is True, then return a 2-tuple of the filename and the file's existence\n- " + \
        "use_cwd      : use the cwd as the start of the path\n- " + \
        "*deeper_path : add more steps to the path"

        if not isinstance(index,int): raise TypeError("index must be of type int")
        if index <= 0: raise IndexError("File list indexes must be greater than 0")

        result:bool|None = None

        if check_existence: 

            pathlist = []
            if use_cwd: pathlist.append(getcwd())
            pathlist.extend(deeper_path)
            pathlist.append(f"_{index}_page.json")
            filename = path.join(pathlist)

            del pathlist

            result = path.exists(filename)

        if result is None: return f"_{index}_page.json"

        return filename,result
    
    @classmethod
    def _int_from_file(cls,filename:str|PathLike,check_existence:bool = False) -> int|tuple[int,bool]:
        "Returns the index of the file given. filenames must be in the following format:\n" + \
        "f'_{index}_page.json' and the index must be > 0\n" + \
        "If check_existence is True, return a 2-tuple of the index and the existence of the file"

        if not isinstance(filename,(PathLike,str)): raise TypeError("filename must be of type str or PathLike")

        if check_existence: result = path.exists(filename)
        else: result = None

        try:

            index = int(path.basename(filename).removeprefix('_').removesuffix('_page.json'))
            if index <= 0: raise ValueError("file indexes must be greater than 0")

        except ValueError as Error:

            Error.add_note(f"{filename = } is an invalid filename")
            raise

        if result is None: return index
        return index,result

    @staticmethod
    def _get_entries(jsonfile:TextIOWrapper|PathLike|str):

        if isinstance(jsonfile,TextIOWrapper) and jsonfile.readable():
            jsonfile.seek(0)
            jsondata:dict = json.load(jsonfile)
        elif isinstance(jsonfile,(PathLike,str)) and path.exists(jsonfile):
            with open(jsonfile,'r',encoding='utf-8') as file:
                jsondata:dict = json.load(file)
            del file
        else:
            raise FileNotFoundError(f"Could not find a file for {jsonfile = }")

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
        def extract_text(element:ET.Element):
            text = element.text if element.text else ""
            for child in element:
                text += EntryData._transcript_helpers.extract_text(child)
                if child.tail:
                    text += child.tail
            return text.strip()
        
        @staticmethod
        def post_process(text:str):
            text = text.replace('[interposing]','\x00').replace('[phonetic]','\x01')

            text = text.replace('[','\x03').replace(']','\x03')

            text = text.replace('\x00','[interposing]').replace('\x01','[phonetic]')

            textlist = text.split('\x03')
            for index,item in enumerate(textlist):
                if 'START ' in item or 'END ' in item:
                    textlist[index] = ''
            del textlist[0],textlist[-1]
            text = ''.join(textlist)

            textlist = text.replace('\n      00','\x00\x01').split('\x00')
            for index,item in enumerate(textlist):
                if '\x01' in item:
                    textlist[index] = item[3:]
            text = '\n'.join(textlist)
            return text
        
        @staticmethod
        def remove_times(text:str):
            textlist = text.split('\n')
            for index,item in enumerate(textlist):
                if len(item) < 9: continue
                if (timestamp := item[:9]).strip().replace(':','').isdigit():
                    textlist[index] = item.replace(timestamp,'')
            return '\n'.join(textlist)
        
        @staticmethod
        def add_breaks(text:str):
            textlist = text.split('\n')
            for index,item in enumerate(textlist):
                if len(item) < 4: continue
                if ':  ' in item and item[:item.find(':  ')].isupper():
                    textlist[index] = '\n' + item
            return '\n'.join(textlist)

        @staticmethod
        def save_backup(text:str,error:Exception):
            with open('transcript_backup.txt','w',encoding='utf-8') as file:
                print('SCRIPT ERROR START',repr(error),'SCRIPT ERROR END',sep='\n',end='\n\n\n\n\n',file=file)
                print(text,file=file)

    def get_transcript(self,*,
                       remove_times:bool = True,
                       add_lines_for_turns:bool = True,
                       file:TextIOWrapper|PathLike|str|None = None,
                       ):
        cls = EntryData
        helpers = cls._transcript_helpers
        for resource in self.json['resources']:
            if 'transcript' in resource['caption']:
                resp = requests.get(resource["fulltext"])
                sleep(2)
                resp.encoding = 'utf-8'
                try: 
                    root = ET.fromstring(resp.text)
                except ET.ParseError:
                    if '<title>Service-Unavailable -- 503 -- Library of Congress</title>' in resp.text:
                        raise ConnectionError("The LoC site returned an error!")
                    with open('error.txt','w') as error:
                        print(resource,file=error)
                        print(resp.text,file=error)
                    raise
                plain_text = helpers.extract_text(root)
                plain_text = helpers.post_process(plain_text)
                if remove_times: plain_text = helpers.remove_times(plain_text)
                if add_lines_for_turns: plain_text = helpers.add_breaks(plain_text)
                plain_text = plain_text.replace('\n\n\n','\n\n')
                if file is None:
                    return plain_text
                elif isinstance(file,TextIOWrapper):
                    try: 
                        print(plain_text,file = file)
                    except Exception as Error: 
                        helpers.save_backup(plain_text,Error)
                        raise
                elif isinstance(file,(str,PathLike)):
                    try:
                        with open(file,'w',encoding='windows-1252') as file:
                            print(plain_text,file=file)
                    except Exception as Error:
                        helpers.save_backup(plain_text,Error)
                        raise
                break
        else:
            raise KeyError("No key found")

if __name__ == '__main__':
   # Test code
   pass



