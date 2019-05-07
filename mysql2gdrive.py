#!/usr/bin/env python3

import os
import sys
import subprocess
import configparser
import argparse
import gzip
import bz2
import zipfile
import shutil
from datetime import datetime


# Check Python version
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
    print('Error: Python 3.6.0 or newer is required', file=sys.stderr)
    exit(1) 


# Define main script
def main():
    config = get_config()
    check_gdrive_cmd(config)

    # Make SQL dump(s) to local file(s)
    sql_names = []
    for database in config['MYSQL']['databases'].split(','):    
        sql_name = get_mysql_dump(database)
        if sql_name != None:
            sql_names.append(sql_name)
        
    # Upload to Google Drive
    upload_result = gdrive_upload(sql_name, config['GDRIVE']['parent_folder'])

    # Delete temporary file(s) and return gdrive process result
    os.unlink(sql_name)
    sys.exit(upload_result.returncode)


# Get config from config file
def get_config():
    args = get_args()

    script_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(script_path, args.config)

    config = configparser.ConfigParser(allow_no_value=True)

    # Define defaults
    config['APP'] = {
        'script_path': script_path,
        'compress': args.compress,
        'tmp_path': 'tmp',
    }
    config['MYSQL'] = {
        'host': 'localhost',
        'port': '3306',
        'username': 'username',
        'password': 'password',
        'databases': ','.join(args.databases),
    }
    config['GDRIVE'] =  {
        'binary_path': 'bin',
        'config_path': '.gdrive',
        'parent_folder': None,
    }

    # Read defined config file
    config.read(config_path)

    return config


# Parse CLI arguments
def get_args():
    parser = argparse.ArgumentParser(description='Dump MySQL database to Google Drive')
    parser.add_argument('databases', help='Name of database(s) to dump', nargs='+')
    parser.add_argument('--config', help='Path to config file; defaults to config.ini', default='config.ini')
    parser.add_argument('--compress', help='Compress resulting output; defaults to gz', choices=['none', 'gz', 'bz2', 'zip'], default='gz')

    args = parser.parse_args()
    return args


def check_gdrive_cmd(config):
    gdrive_cmd = get_gdrive_cmd(config)

    # Check binary exists
    if not os.path.isfile(gdrive_cmd[0]):
        print('Error: ' + gdrive_cmd[0] +
              ' is not found, please download from https://github.com/gdrive-org/gdrive#downloads')
        sys.exit(1)

    # Check config exists
    if not os.path.isdir(gdrive_cmd[2]):
        print(
            'Error: ' + gdrive_cmd[2] + ' does not exist.  To create it and login, please run: \n\n'
            + '\t' + gdrive_cmd[0] + ' -c ' + gdrive_cmd[2] + ' about\n'
        )
        sys.exit(1)


# Determine CLI command to run to use gdrive util
def get_gdrive_cmd(config):
    # Apply path logic to supplied paths
    gdrive_bin = os.path.join(
        config['APP']['script_path'], config['GDRIVE']['binary_path'], 'gdrive')
    gdrive_config = os.path.join(config['APP']['script_path'], config['GDRIVE']['config_path'])
    gdrive_cmd = [gdrive_bin, '-c', gdrive_config]

    return gdrive_cmd


# Upload file to Google Drive
def gdrive_upload(file_path, gdrive_folder=None):
    config = get_config()
    gdrive_cmd = get_gdrive_cmd(config)
    upload_options = [
        'upload',
    ]

    if gdrive_folder:
        upload_options.append('--parent')
        upload_options.append(gdrive_folder)

    upload_cmd = [
        *gdrive_cmd,
        *upload_options,
        file_path
    ]

    return subprocess.run(upload_cmd)


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
        sys.exit(1)

    os.unlink(in_name)
    return out_name


# Make SQL dump
def get_mysql_dump(database):
    config = get_config()

    tmp_path = get_tmp_path(config)
    creds_name = os.path.join(tmp_path, '.creds.ini')

    tmp_name = os.path.join(tmp_path, f"{database}_{datetime.now():%Y%m%d-%H%M}.sql")

    # Make temporary SQL credentials file (Suppress CLI password warning)
    sql_config = configparser.ConfigParser()
    sql_config['client'] = {
        'user': config['MYSQL']['username'],
        'password': config['MYSQL']['password'],
    }
    with open(creds_name, 'w') as creds_file:
        sql_config.write(creds_file)

    # Define SQL command to be run
    sql_cmd = [
        'mysqldump',
        '--defaults-extra-file=' + creds_name,
        '-h' + config['MYSQL']['host'],
        '-P' + config['MYSQL']['port'],
        database,
    ]

    # Write SQL file
    with open(tmp_name, 'w') as tmp_file:
        print(f'Dumping {database}...')
        result = subprocess.run(sql_cmd, stdout=tmp_file)

        # Immediately delete creds file
        os.unlink(creds_name)

        # If mysqldump failed, clean up tmp_name
        if result.returncode != 0:
            os.unlink(tmp_name)
            return None

    # Handle compression
    out_name = compress_file(tmp_name, config['APP']['compress'])

    return out_name


# Sanity check, create and return path to tmp directory
def get_tmp_path(config):
    tmp_path = os.path.join(config['APP']['script_path'], config['APP']['tmp_path'])

    # Create tmp_path if it doesn't exist
    if os.path.exists(tmp_path) and not os.path.isdir(tmp_path):
        print('Error: ' + tmp_path + ' already exists but is not a directory')
        sys.exit(1)
    elif not os.path.exists(tmp_path):
        os.mkdir(tmp_path)

    return tmp_path


# Run!
main()
