#!/usr/bin/env python3

import os
import subprocess
import configparser
import argparse
import gzip
import bz2
import zipfile
import shutil

# Get script path
script_root = os.path.dirname(os.path.realpath(__file__))


def main():
    config = get_config()
    tmp_file = os.path.join(
        script_root,
        config['APP']['tmp_path'],
        config['MYSQL']['database'] + '_tmp.sql',
    )
    out_file = tmp_file
    gdrive_cmd = get_gdrive_cmd(config)
    sql_cmd = [
        'mysqldump',
        '-h' + config['MYSQL']['host'],
        '-P' + config['MYSQL']['port'],
        '-u' + config['MYSQL']['username'],
        '-p' + config['MYSQL']['password'],
        config['MYSQL']['database'],
    ]
    
    # Write SQL file
    with open(tmp_file, 'w') as f:
        subprocess.call(sql_cmd, stdout = f)

    # Handle compression
    if config['APP']['compress'].lower() != 'none':
        out_file = compress_file(tmp_file, config['APP']['compress'])

    print(out_file)


# Get config from config file
def get_config():
    args = get_args()

    config_path = os.path.join(script_root, args.config)

    config = configparser.ConfigParser(allow_no_value=True)

    # Define defaults
    config['APP'] = {
        'compress': args.compress,
    }
    config['MYSQL'] = {
        'host': 'localhost',
        'port': '3306',
        'username': 'username',
        'password': 'password',
        'database': args.database,
    }
    config['GDRIVE'] =  {
        'binary_path': 'bin',
        'config_path': '.gdrive',
        'parent_directory': None,
    }

    # Read defained config file
    config.read(config_path)

    return config


# Parse CLI arguments
def get_args():
    parser = argparse.ArgumentParser('Dump arbitrary MySQL database to Google Drive')
    parser.add_argument('database', help='Name of database to dump')
    parser.add_argument('--config', help='Path to config file; defaults to config.ini', default='config.ini')
    parser.add_argument('--compress', help='Compress resulting output; defaults to gzip', choices=['none', 'gz', 'bz2', 'zip'], default='gz')

    args = parser.parse_args()
    return args


# Determine CLI command to run to use gdrive util
def get_gdrive_cmd(config):
    # Apply path logic to supplied paths
    gdrive_bin = os.path.join(
        script_root, config['GDRIVE']['binary_path'], 'gdrive')
    gdrive_config = os.path.join(script_root, config['GDRIVE']['config_path'])
    gdrive_cmd = [gdrive_bin, '-c', gdrive_config]

    # Check binary exists
    if not os.path.isfile(gdrive_bin):
        print('Error' + gdrive_bin +
              ' is not found, please download from https://github.com/gdrive-org/gdrive#downloads')
        exit(1)

    # Check config exists
    if not os.path.isdir(gdrive_config):
        print(
            'Error: ' + gdrive_config + ' does not exist.  To create it and login, please run: \n\n'
            + '\t\t' + gdrive_bin + ' -c ' + gdrive_config + ' about'
        )
        exit(1)

    return gdrive_cmd


# Handle file compression
def compress_file(in_name, format):
    format = format.lower()

    # Do nothing
    if(format == 'none'):
        return in_name

    # Handle compression
    out_name = in_name + '.' + format
    if(format == 'gz'):
        with open(in_name, 'rb') as in_file:
            with gzip.open(out_name, 'wb') as out_file:
                shutil.copyfileobj(in_file, out_file)
    
    elif(format == 'bz2'):
        with open(in_name, 'rb') as in_file:
            with bz2.open(out_name, 'wb') as out_file:
                shutil.copyfileobj(in_file, out_file)
    elif(format == 'zip'):
        with zipfile.ZipFile(out_name, 'w') as out_file:
            out_file.write(in_name, arcname=in_name.split(os.path.sep)[-1])

    # Error if compression not possible
    else:
        print('Error: Unsupported compression format')
        exit(1)

    return out_name


# Run!
main()