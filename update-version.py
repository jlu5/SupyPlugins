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

subtrees = []
gitlog = subprocess.check_output(("git", "log"))

try:
    version = sys.argv[1].lower()
except IndexError:
    version = time.strftime("%Y.%m.%d")

for line in gitlog.decode("utf-8").split('\n'):
    splitline = line.split("git-subtree-dir: ", 1)
    if len(splitline) == 2:
        subtrees.append(splitline[1])

for dir in filter(os.path.isdir, os.listdir()):
    name = os.path.join(dir, "__init__.py")
    # Don't overwrite subtrees! Otherwise, we'll get sync problems really easily...
    if dir in subtrees or not os.path.exists(name):
        continue
    print('Rewriting %s __version__: %s' % (name, version))
    # Read, replace, go back to the file's beginning, and write out the updated contents.
    with open(name, 'r+') as f:
        contents = f.read()
        contents = re.sub(r'__version__ = ".*?"', '__version__ = "%s"' % version, contents)
        f.seek(0)
        f.write(contents)

subprocess.call(('git', 'commit', '-am', 'Bump version to ' + version))
subprocess.call(('git', 'tag', version))
