"""
This module does the following:
- Tries to import requests before exporting it
- If requests is not found, prompts the user to confirm that they want to install requests
    - If successful, exports requests
    - If failed or denied, exports a class that fakes requests.get, raising AttributeError instead
- Exports REQUESTS_ENABLED, which is a bool telling whether the import was successful or not
"""
import os,sys
from types import ModuleType
from time import sleep

START = os.getcwd()
ENVIRONMENT = os.path.dirname(sys.executable)
os.chdir(ENVIRONMENT)
del ENVIRONMENT


def _user_choice() -> bool:
    """Prompts the user to confirm before installing requests"""
    print("Please install the requests module to get data from the library of congress")
    print("Any requests to the LoC Api require requests to be installed, and data aquisition is disabled without it.")
    while (user := input("Do you want to install the requests module in your environment? (Y/N)\n>> ")):
        match user:
            case 'Y':
                return True
            case 'N':
                return False
            case _:
                print("Try again")

def install_requests() -> bool:
    """Ensures that requests is present, or indicates that it is absent and allows disabling the features that depend on it."""
    try: # We first verify that requests does not need to be installed
        import requests
        return True
    except ModuleNotFoundError: # If it is indeed missing, proceed.
        pass
    
    if _user_choice(): # if the user confirms:
        print("Attempting to install requests...")
        process = os.spawnv(os.P_WAIT,"pip.exe",["pip","install","requests"])
        success = not bool(process)
        print('\n\n')

        if success:
            print("pip successfully installed requests! Continuing...")
        else:
            print("Warning: requests was not installed! Continuing...")
        return success
    else:
        return False

# This fakes requests.get
class FAKE_REQUESTS:
    """Spoofs the requests module. If the requests module is not found, then this class is exported in it's place"""
    @staticmethod
    def get(*args,**kwargs):
        "This is FAKE_REQUESTS.get, which raises AttributeError"
        raise AttributeError("requests was never installed!")

REQUESTS_ENABLED = install_requests()
os.chdir(START)

if REQUESTS_ENABLED:
    import requests as EXPORTED_REQUESTS
    tries = 0
    while tries < 10:
        try: 
            EXPORTED_REQUESTS.get('http://www.google.com',timeout=5)
            sleep(1)
        except EXPORTED_REQUESTS.ConnectTimeout as Error:
            tries += 1
            print(repr(Error))
        except EXPORTED_REQUESTS.HTTPError as Error:
            tries += 1
            print(repr(Error))
        except EXPORTED_REQUESTS.ConnectionError as Error:
            tries += 2
            print(repr(Error))
        except EXPORTED_REQUESTS.RequestException as Error:
            tries += 5
            print(repr(Error))
        else:
            del tries
            break
    else:
        input("WARNING: INTERNET CONNECTION COULD NOT BE ESTABLISHED! (Press Enter to continue)>> ")
        REQUESTS_ENABLED = False
else:
    EXPORTED_REQUESTS = FAKE_REQUESTS

requests:ModuleType|type[FAKE_REQUESTS] = EXPORTED_REQUESTS
os.chdir(START)
del START


# We want to export just the REQUESTS_ENABLED and requests
__all__ = [
    'REQUESTS_ENABLED',
    'requests',
]