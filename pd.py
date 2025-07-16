##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Kevin Redon <kingkevin@cuvoodoo.info>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd
from collections import namedtuple

'''
OUTPUT_PYTHON format:

Packet:
[namedtuple('ss': bit start sample number,
  'es': bit end sample number,
  'si': SI bit,
  'so': SO bit,
 ), ...]

Since address and word size are variable, a list of all bits in each packet
need to be output. Since Microwire is a synchronous protocol with separate
input and output lines (SI and SO) they are provided together, but because
Microwire is half-duplex only the SI or SO bits will be considered at once.
To be able to annotate correctly the instructions formed by the bit, the start
and end sample number of each bit (pair of SI/SO bit) are provided.
'''

PyPacket = namedtuple('PyPacket', 'ss es si so')
Packet = namedtuple('Packet', 'samplenum matched cs sk si so')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'microwire'
    name = 'Microwire'
    longname = 'Microwire'
    desc = '3-wire, half-duplex, synchronous serial bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['microwire']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'cs', 'name': 'CS', 'desc': 'Chip select'},
        {'id': 'sk', 'name': 'SK', 'desc': 'Clock'},
        {'id': 'si', 'name': 'SI', 'desc': 'Slave in'},
        {'id': 'so', 'name': 'SO', 'desc': 'Slave out'},
    )
    annotations = (
        ('start-bit', 'Start bit'),
        ('si-bit', 'SI bit'),
        ('so-bit', 'SO bit'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('si-bits', 'SI bits', (0, 1)),
        ('so-bits', 'SO bits', (2,)),
        ('warnings', 'Warnings', (3,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self):
        while True:
            # 0 - cs
            # 1 - sk
            # 2 - si
            # 3 - so 

            # First step is to wait for chipselect
            self.wait({0: 'r'})

            # Now, wait for the first SI to be high when clock is rising, chipselect still on
            self.wait({2: 'h', 1: 'r', 0: 'h'})
            start_bit_start = self.samplenum

            # Wait for the clock to fall
            self.wait({1: 'f', 0: 'h'})

            self.put(start_bit_start, self.samplenum, self.out_ann, [0, ['Start bit', 'S']])
            
            packet = []
            pydata = []

            while True:
                # Collect all bits on the rising edge, or when the chipselect goes low
                cs, sk, si, so = self.wait([{1: 'r'}, {0: 'f'}])
                if not cs:
                    break

                start = self.samplenum

                # Wait for falling edge of the clock
                self.wait({1: 'f'})
                end = self.samplenum

                packet.append(Packet(start, self.matched, cs, sk, si, so))
            
                bit_si = si
                bit_so = so
            
                self.put(start, end, self.out_ann,
                            [1, ['SI bit: %d' % bit_si,
                                'SI: %d' % bit_si, '%d' % bit_si]])
                self.put(start, end, self.out_ann,
                            [2, ['SO bit: %d' % bit_so,
                                'SO: %d' % bit_so, '%d' % bit_so]])
                pydata.append(PyPacket(start, end,
                                bit_si, bit_so))

            self.put(packet[0].samplenum, packet[-1].samplenum, self.out_python, pydata)
