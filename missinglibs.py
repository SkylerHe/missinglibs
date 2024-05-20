# -*- coding: utf-8 -*-
import typing
from   typing import *

###
# Standard imports, starting with os and sys
###
min_py = (3, 11)
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import contextlib
import getpass

###
# Installed libraries like numpy, pandas, paramiko
###

###
# From hpclib
###
import linuxutils
from   urdecorators import trap
from   fileutils import *
from   parsec4 import *
from   dorunrun import *
###
# imports and objects that were written for this project.
###
import os
import subprocess
import sqlite3
from datetime import datetime

"""
Steps:
1. Open the database (datetime, lib, program)
2. Find all executable files that have missing libraries
3. Check for missing libraries
"""
###
# Global objects
###
verbose = False
mynetid = getpass.getuser()

###
# Credits
###
__author__ = 'Skyler He'
__copyright__ = 'Copyright 2024, University of Richmond'
__credits__ = None
__version__ = 0.1
__maintainer__ = 'Skyler He'
__email__ = f'{mynetid}@richmond.edu'
__status__ = 'in progress'
__license__ = 'MIT'


def open_db(name:str) -> tuple:
    """
    This function returns two "handles", one to the database connetion   
    for commit and close, and one to the cursor to manipulate the data
    """
    if  os.path.isfile(name):
        
        db = sqlite3.connect(name,
                             timeout = 5,
                             isolation_level = 'EXCLUSIVE')
        return db, db.cursor()

def check_missinglibs(f:list, cursor):
    """
    This function checks for missing libraries 
    in the list of executable files
    """
    for f in f:
        try:
            result = subprocess.run(['ldd', f], 
                                    capture_output = True,
                                    text = True)
            missing_libs = [l for l in result.stdout.split('\n') if 'not found' in l]
            for lib in missing_libs:
                cursor.execute(''' INSERT INTO missinglibs 
                                (lib, program)
                                VALUES (?, ?) ''', 
                                (lib, f))
        except Exception as e:
            print(e)
            sys.exit(os.EX_DATAERR)



@trap
def missing_libs_main(myargs:argparse.Namespace) -> int:
    db, cursor = create_or_open_db('missinglibs.db')
    exec_files = all_files_not_like('/home/skyler/hpclib', '.so')
    check_missinglibs(exec_files, cursor)
    db.commit()
    db.close()
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="missing_libs", 
        description="What missing_libs does, missing_libs does best.")

    parser.add_argument('-o', '--output', type=str, default="",
        help="Output file name")
    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place")

    myargs = parser.parse_args()
    verbose = myargs.verbose

    try:
        outfile = sys.stdout if not myargs.output else open(myargs.output, 'w')
        with contextlib.redirect_stdout(outfile):
            sys.exit(globals()[f"{os.path.basename(__file__)[:-3]}_main"](myargs))

    except Exception as e:
        print(f"Escaped or re-raised exception: {e}")

