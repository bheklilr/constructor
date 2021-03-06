# (c) 2016 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# constructor is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.

import re
import sys
from os.path import abspath

import yaml


PREABLE = '''\n
Keys in `construct.yaml` file:
==============================

This document describes each of they keys in the `construct.yaml` file,
which is the main configuration file of a constructor configuration
directory.

All keys are optional, except otherwise noted.  Also, the keys `specs`
and `packages` take either a list of items, or a path to a file,
which contains one item per line (excluding lines starting with `#`).

Also note, that any line in `construct.yaml` may contain a selector at the
end, in order to allow customization for selected platforms.

'''

# list of tuples (key name, required, type, description)
KEYS = [
    ('name',                   True,  str, '''
Name of the installer.  May also contain uppercase letter.  The installer
name is independent of the names of any of the conda packages the installer
is composed of.
'''),

    ('version',                True,  str, '''
Version of the installer.  Just like the installer name, this version
is independent of any conda package versions contained in the installer.
'''),

    ('channels',               False, list, '''
The conda channels from which packages are retrieved, when using the `specs`
key below, but also when using the `packages` key ,unless the full URL is
given in the `packages` list (see below).
'''),

    ('specs',                  False, (list, str), '''
List of package specifications, e.g. `python 2.7*`, `pyzmq` or `numpy >=1.8`.
This list of specifications if given to the conda resolver (as if you were
to create a new environment with those specs.
'''),

    ('exclude',                False, list, '''
List of package names to be excluded, after the '`specs` have been resolved.
For example, you can say that `readline` should be excluded, even though it
is contained as a result of resolving the specs for `python 2.7`.
'''),

    ('packages',               False, (list, str), '''
A list of explicit conda packages to be included, e.g. `yaml-0.1.6-0.tar.bz2`.
The packages may also be specified by their entire URL,
e.g.`https://repo.continuum.io/pkgs/free/osx-64/openssl-1.0.1k-1.tar.bz2`.
Optionally, the MD5 hash sum of the package, may be added after an immediate
`#` character, e.g. `readline-6.2-2.tar.bz2#0801e644bd0c1cd7f0923b56c52eb7f7`.
'''),

    ('install_in_dependency_order', False, bool, '''
By default the conda packages included in the created installer are installed
in alphabetical order, Python is always installed first for technical
reasons.  Using this option, the packages are installed in their dependency
order (unless the explicit list in `packages` is used).
'''),

    ('conda_default_channels', False, list, 'XXX'),

    ('installer_filename',     False, str, '''
The filename of the installer being created.  A reasonable default filename
will determined by the `name`, `version`, platform and installer type.
'''),

    ('license_file',           False, str, '''
Path to the license file being displayed by the installer during the install
process.
'''),

    ('default_prefix',         False, str, 'XXX'),

    ('welcome_image',          False, str, '''
Path to an image (in any common image format `.png`, `.jpg`, `.tif`, etc.)
which is used as the welcome image for the Windows installer.
The image is re-sized to 164 x 314 pixels.
By default, an image is automatically generated.
'''),

    ('header_image',           False, str, '''
Like `welcome_image` for Windows, re-sized to 150 x 57 pixels.
'''),

    ('icon_image',             False, str, '''
Like `welcome_image` for Windows, re-sized to 256 x 256 pixels.
'''),

    ('default_image_color',    False, str, '''
The color of the default images (when not providing explicit image files)
used on Windows.  Possible values are `red`, `green`, `blue`, `yellow`.
The default is `blue`.
'''),
]


def ns_platform(platform):
    return dict(
        linux = platform.startswith('linux-'),
        linux32 = bool(platform == 'linux-32'),
        linux64 = bool(platform == 'linux-64'),
        armv7l = bool(platform == 'linux-armv7l'),
        ppc64le = bool(platform == 'linux-ppc64le'),
        osx = platform.startswith('osx-'),
        unix = platform.startswith(('linux-', 'osx-')),
        win = platform.startswith('win-'),
        win32 = bool(platform == 'win-32'),
        win64 = bool(platform == 'win-64'),
    )


sel_pat = re.compile(r'(.+?)\s*\[(.+)\]$')
def select_lines(data, namespace):
    lines = []
    for line in data.splitlines():
        line = line.rstrip()
        m = sel_pat.match(line)
        if m:
            cond = m.group(2)
            if eval(cond, namespace, {}):
                lines.append(m.group(1))
            continue
        lines.append(line)
    return '\n'.join(lines) + '\n'


def parse(path, platform):
    try:
        with open(path) as fi:
            data = fi.read()
    except IOError:
        sys.exit("Error: could not open '%s' for reading" % path)
    res = yaml.load(select_lines(data, ns_platform(platform)))
    try:
        res['version'] = str(res['version'])
    except KeyError:
        pass
    return res


def verify(info):
    types_key = {} # maps key to types
    required_keys = set()
    for key, required, types, unused_descr in KEYS:
        types_key[key] = types
        if required:
            required_keys.add(key)

    for key in info:
        if key not in types_key:
            sys.exit("Error: unknown key '%s' in construct.yaml" % key)
        elt = info[key]
        types = types_key[key]
        if not isinstance(elt, types):
            sys.exit("Error: key '%s' points to %s,\n"
                     "       expected %s" % (key, type(elt), types))

    for key in required_keys:
        if key not in info:
            sys.exit("Error: Required key '%s' not found in construct.yaml" %
                     key)


def generate_doc():
    path = abspath('%s/../../CONSTRUCT.md' % __file__)
    print('generating: %s' % path)
    with open(path, 'w') as fo:
        fo.write(PREABLE)
        for key, required, unused_types, descr in KEYS:
            descr = descr.strip()
            if descr == 'XXX':
                continue
            fo.write("""
`%s`:%s
----------------
%s

""" % (key,
       ' required' if required else '',
       descr))


if __name__ == '__main__':
    generate_doc()
