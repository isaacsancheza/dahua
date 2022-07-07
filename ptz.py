#!/usr/bin/env python3
from os import environ
from dahua import PTZ
from pprint import pprint
from argparse import ArgumentParser


parser = ArgumentParser('ptz')
subparsers = parser.add_subparsers(dest='command')

get_parser = subparsers.add_parser('get')
set_parser = subparsers.add_parser('set')

get_subparsers = get_parser.add_subparsers(dest='get_command')
set_subparsers = set_parser.add_subparsers(dest='set_command')

get_position_parser = get_subparsers.add_parser('position')
set_position_parser = set_subparsers.add_parser('position')

set_position_parser.add_argument('x', type=float, help='X Position')
set_position_parser.add_argument('y', type=float, help='Y Position')
set_position_parser.add_argument('z', type=float, help='Zoom [0 - 128.0]')
set_position_parser.add_argument('s', type=int, help='Speed [1-8]')

required_environment_variables = (
    'DAHUA_PTZ_IP',
    'DAHUA_PTZ_CHANNEL',
    'DAHUA_PTZ_USERNAME',
    'DAHUA_PTZ_PASSWORD',
)

for required_envrionment_variable in required_environment_variables:
    if required_envrionment_variable not in environ:
        parser.error(f'environment variable {required_envrionment_variable} not set')

parser.set_defaults(command='', get_command='', set_command='')
args = parser.parse_args()

ip = environ['DAHUA_PTZ_IP']
channel = environ['DAHUA_PTZ_CHANNEL']
username = environ['DAHUA_PTZ_USERNAME']
password = environ['DAHUA_PTZ_PASSWORD']

ptz = PTZ(ip, channel, username, password)
command = args.command

get_command = args.get_command
set_command = args.set_command

if command == 'get':
    if get_command == ' status':
        pprint(ptz.status)
    elif get_command == 'position':
        pprint(ptz.position)
    else:
        get_parser.print_help()
elif command == 'set':
    if set_command == 'position':
        ptz.go_to(args.x, args.y, args.z, args.s)
    else:
        set_parser.print_help()
else:
    parser.print_help()
