#!/usr/bin/env python
""" Used to hold all common  general-purpose functions and classes

    See the file "LICENSE" for the full license governing this code. 
    Copyright 2011 Ken Farmer
"""
import sys
import argparse
import math
import errno
import csv
from os.path import isdir, isfile, exists
from os.path import join as pjoin

from datagristle._version import __version__


def isnumeric(number):
    """ Tests whether or not the input is numeric.
        Args:
           - number:  a string containing a number that may be either an integer
             or a float, a positive or a negative or zero.
        Returns:  True or False
    """
    try:
        float(number)
        return True
    except (TypeError, ValueError):
        return False


def get_common_key(count_dict):
    """  Provides the most common key in a dictionary as well as its frequency
         expressed as a percentage.  For example:
         cd = ['car':    7
               'boat':  30
               'truck':  8
               'plane':  5
         print most_common_key(cd)
         >>> boat, 60
    """
    sorted_keys  = (sorted(count_dict, key=count_dict.get))
    total_values = sum(count_dict.values())
    most_common_key       = sorted_keys[-1]
    most_common_key_value = count_dict[sorted_keys[-1]]
    most_common_pct       = most_common_key_value / total_values
    return most_common_key, most_common_pct



def coalesce(default, *args):
    """ Returns the first non-None value.
        If no non-None args exist, then return default.
    """
    for arg in args:
        if arg not in (None, "'None'", 'None'):
            return arg
    return default


def dict_coalesce(struct, key, default=None):
    try:
        return struct[key]
    except KeyError:
        return default


def ifprint(value, string, *args):
    if value is not None:
        print(string % args)


class ArgProcessor(object):
    """ Perform standard datagristle arg parsing as well as custom script parsing.

    Objective is to establish consistency between args of all scripts.  User must
    override add_custom_args(), adding to it any other arg groups desired (via 
    appropriate method calls).

    Args:
        short_desc: a single paragraph description of script.
        long_desc: a 1-2 page description of script.
    Raises:
        sys.exit:  on most errors
        NotImplementedError: if add_custom_args() is not overrridden
    """
    def __init__(self, short_desc, long_desc):
        self.parser     = argparse.ArgumentParser(short_desc,
                              formatter_class=argparse.RawTextHelpFormatter)
        self.add_custom_args()
        self.add_standard_args()
        self.args       = self.parser.parse_args()

        if self.args.long_help:
            print(long_desc)
            sys.exit(0)

        #if self.args.files[0] == '-':  # stdin
        #    if not self.args.delimiter:
        #        self.parser.error('Please provide delimiter when piping data into program via stdin')

        self.custom_validation()


    def add_standard_args(self):
        """
        """
        self.parser.add_argument('--long-help',
                default=False,
                action='store_true',
                help='Print more verbose help')

        self.parser.add_argument('-V', '--version',
                action='version',
                version='version: %s' % __version__)


    def add_option_csv_dialect(self):
        """
        """
        self.parser.add_argument('-d', '--delimiter',
                action=DelimiterAction,
                help=('Specify a quoted single-column field delimiter. This may be'
                      ' determined automatically by the program.'))
        self.parser.add_argument('--escapechar',
                default='"',
                help='Specify escaping character - generally only used for '
                     ' stdin data.  Default is "')
        self.parser.add_argument('--quoting',
                choices=('quote_all','quote_minimal','quite_nonnumeric','quote_none'),
                default='quote_none',
                help='Specify field quoting - generally only used for stdin data.'
                     '  The default: is quote_none.')
        self.parser.add_argument('--quotechar',
                default='"',
                help='Specify field quoting character - generally only used for '
                     'stdin data.  Default is double-quote')
        self.parser.add_argument('--recdelimiter',
                help='Specify a quoted end-of-record delimiter. ')
        self.parser.add_argument('--hasheader',
                dest='hasheader',
                default=None,
                action='store_true',
                help='Indicate that there is a header in the file.')
        self.parser.add_argument('--hasnoheader',
                dest='hasheader',
                default=None,
                action='store_false',
                help=('Indicate that there is no header in the file.'
                        'Occasionally helpful in overriding automatic '
                        'csv dialect guessing.'))

    def add_option_dry_run(self, help_msg=None):
        """
        """
        help_info = help_msg or 'Performs most processing except for final changes.'
        self.parser.add_argument('--dry-run',
                default=False,
                action='store_true',
                help=help_info)

    def add_option_stats(self, help_msg=None, default=True):
        """
        """
        help_info = help_msg or 'Writes detailed processing stats'
        self.parser.add_argument('--stats',
                dest='stats',
                action='store_true',
                help=help_info)

        help_info = help_msg or 'Turns off stats'
        self.parser.add_argument('--nostats',
                dest='stats',
                action='store_false',
                help=help_info)

    def add_option_config_name(self):
        """
        """
        help_info = 'Name of config within xdg dir (such as .confg/gristle_differ/* on linux)'
        self.parser.add_argument('--config-name',
                help=help_info)

    def add_option_config_fn(self):
        """
        """
        help_info = 'Name of config file.'
        self.parser.add_argument('--config-fn',
                help=help_info)

    def add_option_logging(self, help_msg=None):
        """
        """
        self.parser.add_argument('--log-level',
                            choices=['DEBUG','INFO','WARNING','ERROR', 'CRITICAL'],
                            help='Specify verbosity of logging')
        self.parser.add_argument('--console-log',
                            action='store_true',
                            default=True,
                            dest='log_to_console',
                            help='Turns on printing of logs to the console')
        self.parser.add_argument('--no-console-log',
                            action='store_false',
                            dest='log_to_console',
                            help='Turns off printing of logs to the console')


    def add_positional_file_args(self, stdin=True):
        """
        """
        if stdin is True:
            default=['-']
            help=('Specifies the input file(s).  The default is stdin.  Multiple '
                  'filenames can be provided.')
        else:
            default=None
            help='Specifies the input file(s). '
        #print 'default: %s' % default

        self.parser.add_argument('files',
                                 default=default,
                                 nargs='*',
                                 #type=argparse.FileType('r'),
                                 help=help)

    def add_custom_args(self):
        """ Must be overriden by subclass with its argument additions.
        """
        raise NotImplementedError('Must be overriden by sub-classing script')

    def custom_validation(self):
        """ Intended to be overridden by subclass.
        """
        pass


class DelimiterAction(argparse.Action):
    """ An argparse delimiter action to fix unprintable delimiter values.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        val = dialect_del_fixer(values)
        setattr(namespace, self.dest, val)


def dialect_del_fixer(values):
    """ Fix unprintable delimiter values provided as CLI args
    """
    if values == '\\t':
        val = '\t'
    elif values == 'tab':
        val = '\t'
    elif values == '\\n':
        val = '\n'
    else:
        val = values
    return val




def abort(summary, details=None, rc=1):
    """ Creates formatted error message within a box of = characters
        then exits.
    """

    #---prints top line:
    print('=' * 79)

    #---prints message within = characters, assumes it is kinda short:
    print('=== ', end='')
    print('%-69.69s' % summary, end='')
    print(' ===')
    if 'logger' in vars() and logger:
        logger.critical(summary)

    #---prints exception msg, breaks it into multiple lines:
    if details:
        for i in range(int(math.ceil(len(details)/68))):
            print('=== ', end='')
            print('%-69.69s' % details[i*68:(i*68)+68], end='')
            print(' ===')
    if 'logger' in vars() and logger:
        logger.critical(details)

    #---prints bottom line:
    print('=' * 79)

    sys.exit(rc)



def colnames_to_coloff0(col_names, lookup_list):
    """ Returns a list of collection column positions with offset of 0 for a list of
        collection column names (optional) and a lookup list of col names and/or col
        offsets.

        Inputs:
           - col_names   - list of collection column names, may be empty
           - lookup_list - list of column names or positions to lookup (off0)
        Returns:
           - result      - list of column positions (off0)
        Raises:
           - KeyError if column name from lookup_list not in colnames,
                      or if col position from lookup_list extends beyond
                      populated col_names list.
        Notes:
           - output will always be a list of integers
           - input column offsets can be integers (0) or strings ('0')
    """
    assert isinstance(col_names, list)
    assert isinstance(lookup_list, list)

    colname_lookup = dict((element, offset) for offset, element in enumerate(col_names))
    colname_lookup_len = len(colname_lookup)

    try:
        result         =  [int(x) if isnumeric(x) else colname_lookup[x] for x in lookup_list]
    except KeyError:
        raise KeyError('Column name not found in colname list')

    # extra edit to look for offsets not found within a colname listing:
    if colname_lookup:
        for x in result:
            if x >= colname_lookup_len:
                raise KeyError('column number %s not found in colname list' % x)

    #assert isinstance(result, list)
    return result





