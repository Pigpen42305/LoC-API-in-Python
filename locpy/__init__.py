from .requirements_verify import main as verify

verify() # Makes sure all requirements are met
del verify

from .path_manager import *

from .LoC_API import main as run_LoC_setup
EntryData = run_LoC_setup()
del run_LoC_setup
to_start()

__all__ = [
    'EntryData',
]
