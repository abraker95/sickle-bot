import os
import pathlib


# Discord bot token
discord_token = ''

# Discord id of admin (int)
admin_user_id = 00000000000000000  

# Channel ID to post debug messages such as errors and general failures
debug_channel = 00000000000000000

# Runtime Settings and paths
runtime_mode = [ 'db' ]     # Add 'db' in list for warn, info, and debug printouts
#runtime_mode = [ ]     # Add 'db' in list for warn, info, and debug printouts
runtime_quit = False        # Don't change

root     = os.path.abspath(os.path.dirname(__file__))
log_path = pathlib.Path(root + '/logs')

# API Keys
#MongoAddress = getenv('MongoAddress') or '127.0.0.1'
#MongoPort = getenv('MongoPort') or 27017
#MongoAuth = getenv('MongoAuth') or False
#MongoUser = getenv('MongoUser') or ''
#MongoPass = getenv('MongoPass') or ''

# Bot Control Settings
server_url = 'http://localhost/'
cmd_prefix = '<<'

