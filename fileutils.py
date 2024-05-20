# -*- coding: utf-8 -*-
""" Generic, bare functions, not a part of any object or service. """

# Added for Python 3.5+
import typing
from typing import *

import base64
import calendar
import fnmatch
import getpass
import glob
import os
import random
import resource
import re
import stat
import subprocess
import sys
import tempfile
    
# Credits
__longname__ = "University of Richmond"
__acronym__ = " UR "
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2015, University of Richmond'
__credits__ = None
__version__ = '0.1'
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'Prototype'

__license__ = 'MIT'

LIGHT_BLUE="\033[1;34m"
BLUE = '\033[94m'
RED = '\033[91m'
YELLOW = '\033[1;33m'
REVERSE = "\033[7m"
REVERT = "\033[0m"
GREEN="\033[0;32m"

LOCK_NONE = 0

####
# A
####
def all_dirs_in(s:str, depth:int=0) -> str:
    """
    A generator to get the names of directories under the
    one given as the first parameter.
    """
    s = expandall(s)
    if depth==1: 
        return next(os.walk(s))[1]
    else:
        return [t[0] for t in os.walk(s)]


def all_files_in(s:str, include_hidden:bool=False) -> str:
    """
    A generator to cough up the full file names for every
    file in a directory.
    """
    s = expandall(s)
    for c, d, files in os.walk(s):
        for f in files:
            s = os.path.join(c, f)
            if not include_hidden and is_hidden(s): continue
            yield s


def all_files_like(d:str, partial_name:str) -> str:
    """
    A list of all files that match the argument
    """
    yield from ( f for f in all_files_in(d) if partial_name in f )


def all_files_not_like(d:str, partial_name:str) -> str:
    """
    A list of all files that do not match the argument
    """
    yield from ( f for f in all_files_in(d) if partial_name not in f )

def all_module_files() -> str:
    """
    This generator locates all module files that are located in
    the directories that are members of MODULEPATH.
    """
    for location in os.getenv('MODULEPATH', "").split(':'):
        yield from all_files_in(location)


def append_blob(b:bytes, f:Union[str, object]) -> int:
    """
    Appends b to f, and allows f to be an alread open file
    or a filename. This function does a lock on the file allowing
    for safe operation in a multi-process/thread environment.

    returns -1 on error or number of bytes written.
    """
    try:    
        f = open(f, 'ab+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        return f.write(b)
    except Exception as e:
        return -1
    finally:
        f.close()


def append_pickle(o:object, f:Union[str, object]) -> Union[bool, int]:
    """
    Pickles o and appends it to f.

    returns True on success, False on a failure to pickle, and
        -1 on any IO Error.
    """
    try:    
        f = open(f, 'ab+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        pickle.dump(o, f)
        return True
    except pickle.PicklingError as e:
        return False
    except Exception as e:
        return -1
    finally:
        f.close()


def append_text(s:str, f:Union[str, object]) -> int:
    """
    Appends s to f, and allows f to be an alread open file
    or a filename. This function does a lock on the file allowing
    for safe operation in a multi-process/thread environment.

    returns -1 on error or number of bytes written.
    """
    try:    
        f = open(f, 'a+') if isinstance(f, str) else f
        fcntl.lockf(f, fcntl.LOCK_EX)
        return f.write(s)
    except Exception as e:
        return -1
    finally:
        f.close()


####
# B
####

def build_file_list(f:str) -> List[str]:
    """
    Resolve all the symbolic names that might be embedded in the filespec,
    and return a list of all the files that match it **at the time the
    function is called.**

    f -- a file name "spec."

    returns -- a possibly empty list of file names.
    """
    return glob.glob(file_name_filter(f))
    

####
# C
####

####
# D
####

def date_filter(filename:str, *, 
    year:str="YYYY", 
    year_contracted:str="Y?",
    month:str="MM", 
    month_contracted:str="M?",
    month_name:str="bbb",
    week_number:str="WW",
    day:str="DD",
    day_contracted:str="D?",
    hour:str="hh",
    minute:str="mm",
    second:str="ss",
    date_offset:int=0) -> str:
    """
    Remove placeholders from a filename and use today's date (with
    an optional offset).

    NOTE: all the placeholders are non-numeric, and all the replacements 
        are digits. Thus the function works because the two are disjoint
        sets. Break that .. and the function doesn't work.
    """
    if not isinstance(filename, str): return filename

    #Return unmodified file name if there isn't at least one set of format delimiters "{" and "}"
    if not re.match(".*?\{.*?\}.*?", filename):
        return filename

    today = crontuple_now() + datetime.timedelta(days=date_offset)

    # And now ... for Petrarch's Sonnet 47
    this_year = str(today.year)
    this_year_contracted = this_year[2:]
    this_month_name = calendar.month_abbr[today.month].upper()
    this_month = str('%02d' % today.month)
    this_month_contracted = this_month if this_month[0] == '1' else this_month[1]
    this_week = str('%02d' % datetime.date.today().isocalendar()[1])
    this_day =  str('%02d' % today.day)
    this_day_contracted = this_day if this_day[0] != '0' else this_day[1]
    this_hour = str('%02d' % today.hour)
    this_minute = str('%02d' % today.minute)
    this_second = str('%02d' % today.second)

    #Initialize new_filename so we can use it later
    new_filename = filename
    
    #Iterate through each pair of "{" and "}" in filename and replace placeholder values
    #with date literals
    for date_exp in [ m.group(0) for m in re.finditer("\{.*?\}",filename) ]:
        #Start with the sliced substring excluding the "{" and "}" charactes and
        #begin replacing pattern date strings with literals
        new_name = date_exp[1:-1].replace(year, this_year)
        new_name = new_name.replace(year_contracted, this_year_contracted)
        new_name = new_name.replace(month_name, this_month_name)
        new_name = new_name.replace(month, this_month)
        new_name = new_name.replace(month_contracted, this_month_contracted)
        new_name = new_name.replace(week_number, this_week)
        new_name = new_name.replace(day, this_day)
        new_name = new_name.replace(day_contracted, this_day_contracted)
        new_name = new_name.replace(hour, this_hour)
        new_name = new_name.replace(minute, this_minute)
        new_name = new_name.replace(second, this_second)
        #Now replace the original string including the "{" and "}" with the translated string
        new_filename = new_filename.replace(date_exp,new_name)

    #Return result and strip { and } format containers
    return new_filename


####
# E
####

def expandall(s:str) -> str:
    """
    Expand all the user vars into an absolute path name. If the 
    argument happens to be None, it is OK.
    """
    return s if s is None else os.path.abspath(os.path.expandvars(os.path.expanduser(s)))
    

def extract_pickle(f:Union[str,object]) -> object:
    """
    A generator to read a file of pickles.
    """
    try:
        f = open(f, 'rb') if isinstance(f, str) else f
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break
    finally:
        f.close()
####
# F
####

def fclose_all() -> None:
    for i in range (0, 1024):
        try:
            os.close(i)
        except:
            continue


def file_name_filter(filename:str, env:str='.') -> str:
    """
    Modify the filename in the following ways, and in this order:

    1. Apply the date filtering.
    2. Expand any environment variables or directory shorthand.
    3. Join the environment if the name does not start with an
        absolute path.
    """
    filename = expandall(date_filter(filename))

    if not filename.startswith(os.sep): 
        filename = os.path.join(env, filename)

    return filename


####
# G
####

def get_file_page(path:str,num_bytes:int=resource.getpagesize()) -> str: 
    """
    Returns the first num_bytes of a file as a tuple of hex strings

    path -- path to file
    num_bytes -- number of bytes from position 0 to return
    """
    with open(path,'rb') as z:
        return z.read(num_bytes)

filetypes = {
    b"%PDF-1." : "PDF",
    b"#%Module" : "MOD",
    b"BZh91A" : "BZ2",
    bytes.fromhex("FF454C46") : "ELF",
    bytes.fromhex("1F8B") : "GZIP",
    bytes.fromhex("FD377A585A00") : "XZ",
    bytes.fromhex("504B0304") : "ZIP",
    bytes.fromhex("504B0708") : "ZIP"
    }

def get_file_type(path:str) -> str:
    """
    By inspection, return the presumed type of the file located 
    at path. Returns a three of four char file type, or None if
    the type cannot be determined. This might be because the
    type cannot be determined when inspected, or because it cannot 
    be opened. 
    """
    global filetypes
    
    try:
        with open(expandall(path), 'rb') as f:
            shred = f.read(256)
    except PermissionError as e:
        return None

    for k, v in filetypes.items():
        if shred.startswith(k): return v

    return "TXT" if shred.isascii() else None
    

def get_lockfile(lockfile:str) -> bool:
    """
    Return whether we are the process that owns the lock.
    """
    if not os.path.exists(lockfile):
        with open(lockfile, 'w') as f:
            f.write(f"{os.getpid()}")
            f.close()
        return True

    else:
        with open(lockfile, 'r') as f:
            return f.read().strip() == str(os.getpid())


def release_lockfile(lockfile:str) -> bool:
    try:
        os.unlink(lockfile)
        return True
    except:
        return False
    
    
def got_data(filenames:str) -> bool:
    """
    Return True if the file or files all are non-empty, False otherwise.
    """
    if filenames is None or not len(filenames): return False

    filenames = listify(filenames)
    result = True
    for _ in filenames:
        result = result and bool(os.path.isfile(_)) and bool(os.stat(_).st_size)
    return result

####
# H
####
def home_and_away(filename:str) -> str:
    """
    Looks for the file in $PWD, $OLDPWD, $HOME, and then /scratch if it is
    not fully qualified. Note that this function only returns None if no
    files like filename are found in any of the locations.

    It has the benefit that unless nothing is found, it returns the
    filename fully qualified. 
    """

    if filename.startswith(os.sep): return filename

    s = os.path.join(os.environ.get('PWD',''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get('OLDPWD',''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get('HOME', ''), filename)
    if os.path.exists(s): return s
    s = os.path.join(os.environ.get(f'/scratch/{getpass.getuser()}', filename))
    if os.path.exists(s): return s

    return None


####
# I
####
def is_hidden(path:str) -> bool:
    """
    returns True if the path is hidden
    """
    return True if "/." in path else False


def is_PDF(o:Union[bytes,str]) -> bool:
    """
    Determine if a file is a PDF file or something else.

    o -- as a str, it is interpreted to be a filename; if bytes,
        we assume it is the first part of some file-like data
        object.

    returns True if the file or data start with %PDF-1.
    """

    shred = None
    if isinstance(o, str):
        with open(o) as f:
            shred = bytes(f.readline()[:7])
    else:
        shred = o[:7]
    return shred == b'%PDF-1.'


####
# J
####

####
# K
####

####
# L
####

def lines_in_file(filename:str) -> int:
    """
    Count the number of lines in a file by a consistent means.
    """
    if not os.path.isfile(filename): return 0

    try:
        count = int(subprocess.check_output([
            "/bin/grep", "-c", os.linesep, filename
            ], universal_newlines=True).strip())
    except subprocess.CalledProcessError as e:
        tombstone(str(e))
        return 0
    except ValueError as e:
        tombstone(str(e))
        return -2
    else:
        return count
    

####
# M
####

def make_dir_or_die(dirname:str, mode:int=0o700) -> None:
    """
    Do our best to make the given directory (and any required 
    directories upstream). If we cannot, then die trying.
    """

    dirname = expandall(dirname)

    try:
        os.makedirs(dirname, mode)

    except FileExistsError as e:
        # It's already there.
        if not os.path.isdir(dirname): 
            raise NotADirectoryError('{} is not a directory.'.format(dirname)) from None
            sys.exit(os.EX_IOERR)

    except PermissionError as e:
        # This is bad.
        tombstone()
        tombstone("Permissions error creating/using " + dirname)
        sys.exit(os.EX_NOPERM)

    if (os.stat(dirname).st_mode & 0o777) < mode:
        tombstone("Permissions on " + dirname + " less than requested.")


####
# N
####

####
# O
####

####
# P
####

def path_join(dir_part:str, file_part:str) -> str:
    """
    Like os.path.join(), but trapping the None-s and replacing
    them with appropriate structures.
    """
    if dir_part is None:
        tombstone("trapped a None in directory name")
        dir_part = ""

    if file_part is None:
        tombstone("trapped a None in filename")
        file_part = ""

    dir_part = os.path.expandvars(os.path.expanduser(dir_part))
    file_part = os.path.expandvars(os.path.expanduser(file_part))
    return os.path.join(dir_part, file_part)
 

###
# Q
###

###
# R
###

def random_file(name_prefix:str, *, length:int=None, break_on:str=None) -> tuple:
    """
    Generate a new file, with random contents, consisting of printable
    characters.

    name_prefix -- In case you want to isolate them later.
    length -- if None, then a random length <= 1MB
    break_on -- For some testing, perhaps you want a file of "lines."

    returns -- a tuple of file_name and size.
    """    
    f_name = None
    num_written = -1

    file_size = length if length is not None else random.choice(range(0, 1<<20))
    fcn_signature('random_string', file_size)
    s = random_string(file_size, True)

    if break_on is not None:
        if isinstance(break_on, str): break_on = break_on.encode('utf-8')
        s = s.replace(break_on, b'\n')    

    try:
        f_no, f_name = tempfile.mkstemp(suffix='.txt', prefix=name_prefix)
        num_written = os.write(f_no, s)
        os.close(f_no)
    except Exception as e:
        tombstone(str(e))
    
    return f_name, num_written
    


def random_string(length:int=10, want_bytes:bool=False, all_alpha:bool=True) -> str:
    """
    
    """
    
    s = base64.b64encode(os.urandom(length*2))
    if want_bytes: return s[:length]

    s = s.decode('utf-8')
    if not all_alpha: return s[:length]

    t = "".join([ _ for _ in s if _.isalpha() ])[:length]
    return t


def read_whitespace_file(filename:str) -> tuple:
    """
    This is a generator that returns the whitespace delimited tokens 
    in a text file, one token at a time.
    """
    if not filename: return tuple()

    if not os.path.isfile(filename):
        sys.stderr.write(f"{filename} cannot be found.")
        return os.EX_NOINPUT

    f = open(filename)
    yield from (" ".join(f.read().split('\n'))).split()
    

####
# S
####

####
# T U V W X Y Z
####
