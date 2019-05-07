# MySQL Dump to Google Drive
Dump MySQL database and upload to Google Drive.

Written in Python and is just a wrapper for *mysqldump* and *[gdrive](https://github.com/gdrive-org/gdrive)*.

Tested in Linux and MacOS.  Semi-tested in Windows but may not work.

## Installation
```
# Get mysql2gdrive script
git clone https://github.com/samburney/mysql2gdrive.git

# Download gdrive - Get the correct URL for your platform from here: https://github.com/gdrive-org/gdrive/blob/master/README.md#downloads
mkdir mysql2gdrive/bin
wget -O mysql2gdrive/bin/gdrive <URL>
chmod +x mysql2gdrive/bin/gdrive

# Copy example config.ini and configure for your environment
cp mysql2gdrive/config.ini.example mysql2gdrive/config.ini
```

## Usage
```
$ ./mysql2gdrive/mysql2gdrive.py --help
usage: mysql2gdrive.py [-h] [--config CONFIG] [--compress {none,gz,bz2,zip}]
                       databases [databases ...]

Dump MySQL database to Google Drive

positional arguments:
  databases             Name of database(s) to dump

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Path to config file; defaults to config.ini
  --compress {none,gz,bz2,zip}
                        Compress resulting output; defaults to gz
```

