#!/usr/bin/env python

import os
import sys
import re
import argparse
from multiprocessing import Process
from time import sleep


description = """
This script finds all JPG files under the given path,
resizes them and saves under the new location,
preserving the directory structure. Already existing files
are ignored.

Author: Roman Kiselev
 June 2015
"""



parser = argparse.ArgumentParser(description=description)
group = parser.add_mutually_exclusive_group()

parser.add_argument('src', metavar='source-dir', type=str, nargs=1,
                    help='Source directory tree containing JPG images')
parser.add_argument('dst', metavar='destination-dir', type=str, nargs=1,
                    help='Destination directory where the resized JPG images would be saved')
parser.add_argument('-w', '--overwrite', action='store_true',
                    help="Overwrites all output images")
parser.add_argument('-n', '--dry-run', action='store_true',
                    help="Perform a trial run with no changes made")
group.add_argument('-r', '--resize', nargs='?', type=int, default=False, const=4,
                    help="Resize all images to specified size in Mpx")
group.add_argument('-s', '--scale', nargs='?', type=int, default=False, const=30,
                    help="Scale all images to down to specified number of percents")
parser.add_argument('-q', '--quality', type=int, default=False,
                    help="Quality of JPEG compression")

args = parser.parse_args()

if args.src == args.dst:
	print "You cannot give the same folder for source and destination"
	sys.exit()

def process_photo(root, path):
	"""Process and copy JPG file. """
	scale_arg = ""
	resize_arg = ""
	quality_arg = ""
	if args.scale:
		scale_arg = "-resize %i%%" % args.scale
	if args.resize:
		resize_arg = "-geometry @%i000000" % args.resize
	if args.quality:
		quality_arg = "-quality %i" % args.quality

	convert_cmd = "convert %s %s %s %s %s" % (scale_arg, resize_arg, quality_arg,
                os.path.normpath(os.path.join(root, fname)),
                os.path.normpath(os.path.join(args.dst[0], root, fname)))
		
	new_dir = os.path.normpath(os.path.join(args.dst[0], root))
	# Check if directory exists 
	if not os.path.isdir(new_dir):
		if args.dry_run:
			print "Would create %s" % new_dir
		else:
			os.makedirs(new_dir)
	# Check if file already exists
	if os.path.exists(os.path.join(new_dir, fname)):
		if not args.overwrite:
			print "File exists, skipping %s" % os.path.join(new_dir, fname)
			return
		else:
			if args.dry_run:
				print "Would overwrite %s" % os.path.join(new_dir, fname)
			else:
				print "Overwriting %s" % os.path.join(new_dir, fname)
	if args.dry_run:
		print "Would call %s" % convert_cmd
	else:
		print convert_cmd
		os.system(convert_cmd)



# Do we need to do anything with images?
if args.scale or args.resize or args.quality:
	#############################################
	# Thread control
	#############################################
	thr_max = 8  # Max number of threads
	procs = []
	for root, subFolders, files in os.walk(args.src[0]):
		for fname in files:
			if re.match(".+\.jpg$", fname, re.I):
				while len(procs) >= thr_max:
					sleep(0.005)
					for p in procs:
						if not p.is_alive():
							procs.remove(p)
				p = Process(target=process_photo, args=(root, fname,))
				p.start()
				procs.append(p)

# If not, just copy them (hard-link if possible)
else:
	# try hard link
	try:
		for root, subFolders, files in os.walk(args.src[0]):
			for fname in files:
				if re.match(".+\.jpg$", fname, re.I):
					full_src = os.path.join(root, fname)
					new_dir = os.path.join(args.dst[0], root)
					full_dst = os.path.join(new_dir, fname)
					if not os.path.isdir(new_dir):
						if args.dry_run:
							print "Would create %s" % new_dir
						else:
							os.makedirs(new_dir)			
					if args.dry_run:
						print "Would copy %s to %s" % (full_src, full_dst)
					else:
						# Check if file already exists
						if os.path.exists(full_dst):
							if not args.overwrite:
								print "File exists, skipping %s" % os.path.join(new_dir, fname)
								break
							os.unlink(full_dst)
						print "Hard-linking %s to %s" % (full_src, full_dst)
						os.link(full_src, full_dst)

	except OSError:
		print "Another file system, cannot hard-link"
		sleep(0.2)

		dry = ""
		if args.dry_run:
			dry = "n"
		os.system('rsync -a%sv --include "*/" --include "*.jpg" --include "*.JPG" --exclude "*" --prune-empty-dirs %s %s' % \
		          (dry, args.src[0], args.dst[0]))














