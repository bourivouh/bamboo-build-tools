# coding: utf-8

# $Id: $
import contextlib
import re
import sys
import os.path

import six


def cout(*lines):
    if not lines:
        sys.stdout.write('\n')
    for line in lines:
        sys.stdout.write(line + '\n')


def cerr(*lines):
    if not lines:
        sys.stderr.write('\n')
    for line in lines:
        sys.stderr.write(line + '\n')


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def parse_config(obj, configfile):
    filename = os.path.abspath(configfile)
    if os.path.exists(filename) and os.path.isfile(filename):
        config_locals = {}
        execfile(filename, globals(), config_locals)
        obj.__dict__.update(config_locals)


def get_stable(release, all=False):
    stable = release
    stable = re.sub(r'([\d]+)\.([\d]+)\.0', '\\1.x', stable)
    stable = re.sub(r'([\d]+)\.([\d]+)\.([\d]+)', '\\1.\\2.x', stable)
    if all:
        result = {stable}
        result.add(re.sub(r'([\d]+)\.([\d]+)\.x', '\\1.x', stable))
        return list(result)
    return stable


@contextlib.contextmanager
def chdir(dirname=None):
    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


def tuple_version(version):
    if isinstance(version, six.string_types):
        return tuple(int(v) for v in version.split("."))
    return version
