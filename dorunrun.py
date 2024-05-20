# -*- coding: utf-8 -*-
"""
This file contains conveniences for our slurm development efforts.
"""

import typing
from   typing import *

min_py = (3, 8)

###
# Standard imports.
###

import enum
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

import math
import shlex
import subprocess

from   urdecorators import trap

# Credits
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2021'
__credits__ = None
__version__ = str(math.pi**2)[:5]
__maintainer__ = 'George Flanagin'
__email__ = ['me+ur@georgeflanagin.com', 'gflanagin@richmond.edu']
__status__ = 'Teaching example'
__license__ = 'MIT'

@trap
def dorunrun(command:Union[str, list],
    timeout:int=None,
    verbose:bool=False,
    quiet:bool=False,
    return_datatype:type=bool,
    ) -> Union[str, bool, int, dict]:
    """
    A wrapper around (almost) all the complexities of running child 
        processes.
    command -- a string, or a list of strings, that constitute the
        commonsense definition of the command to be attemped. 
    timeout -- generally, we don't
    verbose -- do we want some narrative to stderr?
    quiet -- overrides verbose, shell, etc. 
    return_datatype -- this argument corresponds to the item 
        the caller wants returned. It can be one of these values.

            bool : True if the subprocess exited with code 0.
            int  : the exit code itself.
            str  : the stdout of the child process.
            dict : everything as a dict of key-value pairs.

    returns -- a value corresponding to the requested info.
    """

    # If return_datatype is not in the list, use dict. Note 
    # that the next statement covers None, as well.
    return_datatype = dict if return_datatype not in (int, str, bool) else return_datatype

    # Let's convert all the arguments to str and relieve the caller
    # of that responsibility.
    if isinstance(command, (list, tuple)):
        command = [str(_) for _ in command]
        shell = False
    elif isinstance(command, str):
        command = shlex.split(command)
        shell = False
    else:
        raise Exception(f"Bad argument type to dorunrun: {command=}")

    if verbose: sys.stderr.write(f"{command=}\n")

    try:
        result = subprocess.run(command, 
            timeout=timeout, 
            input="",
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            shell=False)

        code = result.returncode
        b_code = code == 0
        i_code = code
        s = result.stdout[:-1] if result.stdout.endswith('\n') else result.stdout
        e = result.stderr[:-1] if result.stderr.endswith('\n') else result.stderr

        if return_datatype is int:
            return i_code
        elif return_datatype is str:
            return s
        elif return_datatype is bool:
            return b_code
        else:
            return {"OK":b_code, 
                    "code":i_code, 
                    "name":ExitCode(i_code).name, 
                    "stdout":s, 
                    "stderr":e}
        
    except subprocess.TimeoutExpired as e:
        print(f"Process exceeded time limit at {timeout} seconds.")
        print(f"Command was {command}")
        return {"OK":False, 
                "code":255, 
                "name":ExitCode(255).name, 
                "stdout":"", 
                "stderr":""}

    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


class FakingIt(enum.EnumMeta):

    def __contains__(self, something:object) -> bool:
        """
        Normally ... the "in" operator checks if something is in
        an instance of the container. We want to check if a value
        is one of the IntEnum class's members.
        """
        try:
            self(something)
        except ValueError:
            return False

        return True


class ExitCode(enum.IntEnum, metaclass=FakingIt):
    """
    This is a comprehensive list of exit codes in Linux, and it 
    includes four utility functions. Suppose x is an integer:

        x in ExitCode     # is x a valid value?
        x.OK              # Workaround: enums all evaluate to True, even if they are zero.
        x.is_signal       # True if the value is a "killed by Linux signal"
        x.signal          # Which signal, or zero.
    """

    @property
    def OK(self) -> bool:
        return self is ExitCode.SUCCESS

    @property
    def is_signal(self) -> bool:
        return ExitCode.KILLEDBYMAX > self > ExitCode.KILLEDBYSIGNAL

    @property 
    def signal(self) -> int:
        return self % ExitCode.KILLEDBYSIGNAL if self.is_signal else 0


    # All was well.
    SUCCESS = os.EX_OK

    # It just did not work. No info provided.
    GENERAL = 1

    # BASH builtin error (e.g. basename)
    BUILTIN = 2
    
    # No device or address by that name was found.
    NODEVICE = 6

    # Trying to create a user or group that already exists.
    USERORGROUPEXISTS = 9

    # The execution requires sudo
    NOSUDO = 10

    ######
    # Code 64 is also the usage error, and the least number
    # that has reserved meanings, and nothing above here 
    # should be used by a user program.
    ######
    BASEVALUE = 64
    # command line usage error
    USAGE = os.EX_USAGE
    # data format error
    DATAERR = os.EX_DATAERR
    # cannot open input
    NOINPUT = os.EX_NOINPUT
    # user name unknown
    NOUSER = os.EX_NOUSER
    # host name unknown
    NOHOST = os.EX_NOHOST
    # unavailable service or device
    UNAVAILABLE = os.EX_UNAVAILABLE
    # internal software error
    SOFTWARE = os.EX_SOFTWARE
    # system error
    OSERR = os.EX_OSERR
    # Cannot create an ordinary user file
    OSFILE = os.EX_OSFILE
    # Cannot create a critical file, or it is missing.
    CANTCREAT = os.EX_CANTCREAT
    # input/output error
    IOERR = os.EX_IOERR
    # retry-able error
    TEMPFAIL = os.EX_TEMPFAIL
    # remotely reported error in protocol
    PROTOCOL = os.EX_PROTOCOL
    # permission denied
    NOPERM = os.EX_NOPERM
    # configuration file error
    CONFIG = os.EX_CONFIG

    # The operation was run with a timeout, and it timed out.
    TIMEOUT = 124

    # The request to run with a timeout failed.
    TIMEOUTFAILED = 125

    # Tried to execute a non-executable file.
    NOTEXECUTABLE = 126

    # Command not found (in $PATH)
    NOSUCHCOMMAND = 127

    ###########
    # If $? > 128, then the process was killed by a signal.
    ###########
    KILLEDBYSIGNAL = 128

    # These are common enough to include in the list.
    KILLEDBYCTRLC = 130
    KILLEDBYKILL = 137
    KILLEDBYPIPE = 141
    KILLEDBYTERM = 143

    KILLEDBYMAX = 161

    # Nonsense argument to exit()
    OUTOFRANGE = 255


if __name__ == '__main__':
    import getpass
    mynetid = getpass.getuser()

    # we know this source file exists, so let's use it.
    filename = __file__
    print(dorunrun(f'rm -f {filename}.new', return_datatype=dict))
    print(dorunrun(f'cp {filename} {filename}.new', return_datatype=int))

    # most computers are setup so that you can ssh as yourself to localhost. 
    short_filename = os.path.basename(filename)
    print(dorunrun(f"""
        scp {mynetid}@localhost:{filename} /tmp/{short_filename}
        """, 
        return_datatype=dict))
    print(dorunrun(f"""
        ssh -o ConnectTimeout=3 -i ~/.ssh/id_rsa root@alexis "ls -lrt"
        """,
        return_datatype=dict))
    
