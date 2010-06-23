
# Paver project
# http://www.blueskyonmars.com/projects/paver/index.html

# Paver works a bit like Make or Rake. 
# To use Paver, you run paver <taskname> and the paver command 
# will look for a pavement.py file in the current directory

import ConfigParser, os, os.path, sys

from paver.easy import *
from paver.setuputils import setup

#
# configure
#
# (for Paver to work probably, this needs to be global)
conf = ConfigParser.SafeConfigParser()
with open('pavement.ini') as f:
    conf.readfp(f)
options.conf = conf
opts = dict(options.conf.items('setup'))
for opt in opts:
    val = opts[opt]
    opts[opt] = eval(val)
setup(**opts)

@task
@needs('paver.misctasks.minilib', 
       'paver.misctasks.generate_setup',)
def sdist():
    call_task('setuptools.command.sdist')
