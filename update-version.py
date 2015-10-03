#!/usr/bin/env python3

###
# Copyright (c) 2015, James Lu
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import subprocess
import os
import sys
import re
import time
import argparse

subtrees = []
gitlog = subprocess.check_output(("git", "log"))

default_version = time.strftime("%Y.%m.%d")

parser = argparse.ArgumentParser(description="Script to batch update plugins' versions in their __init__.py's")
parser.add_argument('-v', "--version", help='the version to upgrade to - if not defined, defaults to the current date (YYYY.MM.DD)"', default=default_version, nargs="?")
parser.add_argument("-n", "--no-commit", help="Don't commit and tag after incrementing version", action='store_true')
parser.add_argument("-f", "--folders", help="Sets the plugin folders to look through", nargs='*', default=os.listdir())
args = parser.parse_args()

version = args.version

for line in gitlog.decode("utf-8").split('\n'):
    splitline = line.split("git-subtree-dir: ", 1)
    if len(splitline) == 2:
        subtrees.append(splitline[1])

to_commit = []

version_re = re.compile(r'__version__ = "(.*?)"')
for dir in filter(os.path.isdir, args.folders):
    name = os.path.join(dir, "__init__.py")
    # Don't overwrite subtrees! Otherwise, we'll get sync problems really easily...
    if dir in subtrees or not os.path.exists(name):
        continue
    try:
        # Read, replace, go back to the file's beginning, and write out the updated contents.
        with open(name, 'r+') as f:
            contents = f.read()
            old_version = version_re.search(contents).group(1)
            new_version = version
            # If the existing version doesn't follow our format (YYYY.mm.dd), append it with a +.
            # But only do this once...
            if old_version.count('.') != 2 and version == default_version:
                old_version = old_version.split('+', 1)[0]
                new_version = "%s+%s" % (old_version, version)
            print('Rewriting %s __version__: %s' % (name, new_version))
            contents = version_re.sub('__version__ = "%s"' % new_version, contents)
            f.seek(0)
            f.truncate()
            f.write(contents)

            f.close()
    except:
        pass
    else:
        to_commit.append(name)

if not args.no_commit:
    print("Automatically committing and tagging as %s." % version)
    subprocess.call(['git', 'commit', '-m', 'Bump version to %s' % version] + to_commit)
    subprocess.call(('git', 'tag', version))
