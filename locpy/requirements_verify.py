import subprocess,sys
from os.path import join,dirname

__all__ = ['main']

PACKAGE_DIRECTORY = dirname(__file__)
requirements = join(PACKAGE_DIRECTORY,'requirements.txt')

def user_choice() -> bool:
    """Prompts the user to confirm before installing requests"""
    print("Please install the requirements to use this package")
    while (user := input("Do you want to install the requirements from the requirements.txt in the package? (Y/N)\n>> ")):
        match user:
            case 'Y':
                return True
            case 'N':
                return False
            case _:
                print("Try again")

def install_requirements() -> None:
    """Installs the requirements, as found in the requirements.txt file"""
    result = subprocess.run([sys.executable,"-m","pip","install","-r",requirements])
    result.check_returncode()
    print("Requirements installed successfully!")

def verify_requirements_met() -> bool:
    """
    Scans through the environment's installed packages and the requirements.
    If a requirement is not found in the installed packages, returns False
    Otherwise, returns True
    """

    result = subprocess.run([sys.executable,"-m","pip","list"],capture_output=True)

    installed = [item.split()[0] for item in result.stdout.decode().split('\r\n')[2:-1]]

    with open(requirements,'r') as reqs:
        for requirement in reqs:
            req = requirement.partition('==')[0]
            if req[0:2] == 'ÿþ':
                req = req[2:]
            if req not in installed:
                print(req,'is missing!')
                return False
        return True

def main():
    if not verify_requirements_met():
        if user_choice():
            install_requirements()

if __name__ == '__main__': main()