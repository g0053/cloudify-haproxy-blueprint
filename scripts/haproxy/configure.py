###############################################################################
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
###############################################################################

# Builtin Imports
import os
import subprocess

# Third Party Imports
# Jinja2 is already installed on agents
from jinja2 import Environment, FileSystemLoader

# Cloudify Imports
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

# Constants
CONFIG_PATH = '/etc/haproxy/haproxy.cfg'
TEMPLATE_FOLDER = '/tmp'
TEMPLATE_FILE_NAME = 'haproxy.cfg.template'

ctx.logger.info('Configuring HAProxy.')
ctx.logger.debug('Pulling the config template into the temp directory.')
ctx.download_resource('haproxy.cfg.template',
                      **{'target_path': '/tmp/haproxy.cfg.template'})

env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))
template = env.get_template(TEMPLATE_FILE_NAME)

ctx.logger.debug('Building a dict object that will contain variables '
                 'to write to the Jinja2 template.')

config = dict()
config['global_maxconn'] = ctx.node.properties['global_maxconn']
config['mode'] = ctx.node.properties['mode']
config['timeout_connect'] = ctx.node.properties['timeout_connect']
config['timeout_client'] = ctx.node.properties['timeout_client']
config['timeout_server'] = ctx.node.properties['timeout_server']
config['frontend_id'] = ctx.node.name
config['frontend_port'] = ctx.node.properties['port']
config['default_backend'] = ctx.node.properties['default_backend']

config['backends'] = {}

for backend in ctx.instance.runtime_properties['backend_names']:
    config['backends'][backend] = ctx.instance.runtime_properties[backend]

ctx.logger.debug('Rendering the Jinja2 template to {0}.'.format(CONFIG_PATH))
ctx.logger.debug('The config dict: {0}.'.format(config))

TEMP_PATH = os.path.join(TEMPLATE_FOLDER, TEMPLATE_FILE_NAME)

with open(TEMP_PATH, 'w') as file:
    file.write(template.render(config))
    file.close()

move_to_etc = subprocess.Popen(
    ['sudo', 'mv', TEMP_PATH, CONFIG_PATH],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
output = move_to_etc.communicate()

if move_to_etc.returncode != 0:
    raise NonRecoverableError('Failed to write to {0}.'.format(CONFIG_PATH))

ctx.logger.debug('Write validation: {0}.'.format(output))

test_config = subprocess.Popen(
    ['sudo', '/usr/sbin/haproxy', '-f', CONFIG_PATH, '-c'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
output = test_config.communicate()

ctx.logger.debug('Config Validation: {0}'.format(output))

if test_config.returncode != 0:
    raise NonRecoverableError('Failed to Configure')
else:
    ctx.logger.info('Configure was successful.')
