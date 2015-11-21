#!/usr/bin/env python

import os
import sys
import re
import argparse
from collections import OrderedDict

DB_SUBSTITUTE_MAX = 10

def load_file(file, prefix, db):
    with open(file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if prefix:
                if not line.startswith(prefix + "."):
                    continue
                line = line.replace(prefix + ".", "", 1)
            line = line.split("=", 1)
            db[line[0]] = line[1]

def add_first_var_ends_with(src_db, dst_db, ends_with):
    assert(type(src_db) is OrderedDict)

    for key, val in src_db.iteritems():
        if key.endswith(ends_with):
            print "'" + key + " ends with '" + ends_with + "'"
            dst_db[ends_with] = val
            break

def db_substitute(db, dict_db):
    regex = "(\{%s\})" % "\}|\{".join(map(re.escape, dict_db.keys()))
    regex = re.compile(regex)

    for i in range(DB_SUBSTITUTE_MAX):
        #print "db_substitute: i = %d" % i
        anything_replaced = False
        for key, val in db.iteritems():
            orig_val = val
            try:
                val = regex.sub(lambda mo: dict_db[mo.string[mo.start()+1:mo.end()-1]], val)
            except KeyErrorDirectory:
                pass
            db[key] = val
            anything_replaced = True if val != orig_val else anything_replaced
        if not anything_replaced:
            break
        
def print_to_file(db, filename):
    with open(filename, 'w') as file:
        for key, val in db.iteritems():
            file.write("%s=%s\n" % (key, val))

def main(argv):
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--arduino-dir", help="Path to Arduino install directory", required=True, type=str)
    args_parser.add_argument("--arduino-ver", help="Arduino version", required=True, type=int)
    args_parser.add_argument("--vendor", help="Hardware vendor directory name (i.e. arduino, esp8266com)", required=True, type=str)
    args_parser.add_argument("--arch", help="Hardware architecture directory name (i.e. avr, esp8266)", required=True, type=str)
    args_parser.add_argument("--board-tag", help="Board tag (i.e. uno, yun, nano, d1)", required=True, type=str)
    args_parser.add_argument("--build-path", help="Directory of build artifacts (for build.path)", required=True, type=str)
    args_parser.add_argument("--project-name", help="Project name (for build.project_name)", required=True, type=str)
    args_parser.add_argument("--output-file", help="File to output the result", required=True, type=str)
    args = args_parser.parse_args()

    arduino_dir = os.path.abspath(args.arduino_dir)
    arduino_ver = str(args.arduino_ver)
    vendor_dir = os.path.join(arduino_dir, "hardware", args.vendor)
    plat_dir = os.path.join(vendor_dir, args.arch)

    print "Platform directory: " + plat_dir

    boards_file = os.path.join(plat_dir, 'boards.txt')
    plat_file =  os.path.join(plat_dir, 'platform.txt')

    if not os.path.isfile(boards_file):
        print "Boards file " + boards_file + " not exists!"
        exit(1)

    if not os.path.isfile(plat_file):
        print "Platform file " + plat_file + " not exists!"
        exit(1)

    # all variables & output variables DBs
    vars_db = {}
    output_db = OrderedDict()

    # Global variables that should be avaliable
    vars_db['runtime.platform.path'] = plat_dir
    vars_db['runtime.hardware.path'] = vendor_dir
    vars_db['runtime.ide.path'] = arduino_dir
    vars_db['runtime.ide.version'] = arduino_ver

    if sys.platform.startswith('linux'):
        vars_db['runtime.os'] = 'linux'
    elif sys.platform.startswith('darwin'):
        vars_db['runtime.os'] = 'macosx'
    elif sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
        vars_db['runtime.os'] = 'windows'


    vars_db['ide_version'] = arduino_ver
    vars_db['build.path'] = args.build_path
    vars_db['build.project_name'] = args.project_name
    vars_db['build.arch'] = args.arch.upper()

    # Load board.txt to vars only
    board_db = OrderedDict()
    load_file(boards_file, args.board_tag, board_db)
    vars_db.update(board_db)
    
    #TMP
    add_first_var_ends_with(board_db, vars_db, 'build.flash_ld')
    add_first_var_ends_with(board_db, vars_db, 'build.mcu')
    
    # TMP
    vars_db['runtime.tools.avr-gcc.path'] = os.path.join(arduino_dir, "hardware", "tools", "avr")
    vars_db['runtime.tools.avrdude.path'] = vars_db['runtime.tools.avr-gcc.path']

    # Load platform.txt
    plat_db = OrderedDict()
    load_file(plat_file, "", plat_db)
    vars_db.update(plat_db)
    output_db.update(plat_db)

    # Substitute variables
    db_substitute(output_db, vars_db)

    #for key, val in vars_db.iteritems():
    #    print key + " = " + val

    print_to_file(output_db, args.output_file)

if __name__ == "__main__":
    main(sys.argv)
