#!/usr/bin/python

"""
    Android boot image pack unpacker - Extract kernel and ramdisk from boot.img
    Copyright (C) 2010  m_101

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from ctypes import *
import struct

# check number of arguments
if len(sys.argv) < 2:
    print 'Usage : ' + sys.argv[0] + ' <boot.img> [outfile]'
    exit(1)



# constants
BOOT_MAGIC = 'ANDROID!'
BOOT_MAGIC_SIZE = 8
BOOT_NAME_SIZE = 16
BOOT_ARGS_SIZE = 512

class boot_img_hdr(Structure):
    _fields_ = [
                ("magic", c_byte * BOOT_MAGIC_SIZE),                  # 

                ('kernel_size', c_uint),            # size in bytes
                ('kernel_addr', c_uint),            # physical load addr

                ('ramdisk_size', c_uint),           # size in bytes
                ('ramdisk_addr', c_uint),           # physical load addr

                ('second_size', c_uint),            # size in bytes
                ('second_addr', c_uint),            # physical load addr

                ('tags_addr', c_uint),              # physical addr for kernel tags
                ('page_size', c_uint),              # flash page size we assume
                ('unused', c_uint * 2),             # future expansion: should be 0

                ('name', c_byte * BOOT_NAME_SIZE), # asciiz product name

                ('cmdline', c_byte * BOOT_ARGS_SIZE),

                ('id', c_uint * 8)
               ]


def show_range (prefix, addr, size):
    print '%s0x%08x-0x%08x (0x%08x)' % (prefix, addr, addr + size, size)

bootimg_hdr = boot_img_hdr()

bootimg = { 'kernel':'', 'misc':'', 'ramdisk':'', 'boot':'', 'system':'',
            'cache':'', 'userdata':'', 'recovery':'' }
bootfile = ''

# we load file in memory
fileIn = open(sys.argv[1], 'r')
magic = fileIn.read(BOOT_MAGIC_SIZE)

if magic != BOOT_MAGIC:
    print "It isn't an android boot image"
    exit(1)

print 'It is an android boot image'

# decode boot img header
bootimg_hdr.kernel_size = struct.unpack('I', fileIn.read(4))[0]
bootimg_hdr.kernel_addr = struct.unpack('I', fileIn.read(4))[0]

bootimg_hdr.ramdisk_size = struct.unpack('I', fileIn.read(4))[0]
bootimg_hdr.ramdisk_addr = struct.unpack('I', fileIn.read(4))[0]

bootimg_hdr.second_size = struct.unpack('I', fileIn.read(4))[0]
bootimg_hdr.second_addr = struct.unpack('I', fileIn.read(4))[0]

bootimg_hdr.tags_addr = struct.unpack('I', fileIn.read(4))[0]
bootimg_hdr.page_size = struct.unpack('I', fileIn.read(4))[0]

#print 'shit : ', fileIn.read(BOOT_NAME_SIZE)
bootimg_hdr.unused = struct.unpack('2I', fileIn.read(8))
bootimg_hdr.name = struct.unpack('%u' % BOOT_NAME_SIZE + 'B', fileIn.read(BOOT_NAME_SIZE))

bootimg_hdr.cmdline = struct.unpack('%u' % BOOT_ARGS_SIZE + 'B', fileIn.read(BOOT_ARGS_SIZE))

bootimg_hdr.id = struct.unpack('%u' % 8 + 'I', fileIn.read(8 * sizeof(c_uint)))

# show decoded fields
name = ''.join([ chr(c) for c in bootimg_hdr.name ])
print 'Product : ' + name
show_range('Kernel  : ', bootimg_hdr.kernel_addr, bootimg_hdr.kernel_size)
show_range('Ramdisk : ', bootimg_hdr.ramdisk_addr, bootimg_hdr.ramdisk_size)
show_range('Second  : ', bootimg_hdr.second_addr, bootimg_hdr.second_size)
print 'pagesize: %u' % bootimg_hdr.page_size
cmdline = ''.join([ chr(c) for c in bootimg_hdr.cmdline ])
print 'Cmdline : ' + cmdline

# go to beginning of file
fileIn.seek(0)
# we skip the header
fileIn.read(bootimg_hdr.page_size)

# pagesize
page_size = bootimg_hdr.page_size
# get kernel
n = (bootimg_hdr.kernel_size + page_size - 1)/page_size
kernel = fileIn.read(n * page_size)
# get ramdisk
m = (bootimg_hdr.ramdisk_size + page_size - 1)/page_size
ramdisk = fileIn.read(m * page_size)
# get second
o = (bootimg_hdr.page_size + page_size - 1)/page_size
second = fileIn.read(o * page_size)


# write the files out

# defined prefix
if len(sys.argv) == 3:
    imgPrefix = sys.argv[2]
# default prefix
else:
    imgPrefix = 'dump'
# kernel file
fileKernel = open(imgPrefix + '-kernel', 'w')
fileKernel.write(kernel)
fileKernel.close()

# ramdisk file
fileRamdisk = open(imgPrefix + '-ramdisk-cpio.gz', 'w')
fileRamdisk.write(ramdisk)
fileRamdisk.write(ramdisk)

