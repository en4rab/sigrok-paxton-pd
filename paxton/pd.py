##
## Copyright (C) 2023 en4rab - Robin Bradshaw <en4rab@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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

# Added selectable polarity and valid edge to make it more generic but it has 
# not been thoroughly tested. The defaults are suitable for Paxton readers

import sigrokdecode as srd


class Decoder(srd.Decoder):
    api_version = 3
    id = 'paxton'
    name = 'Paxton reader'
    longname = 'Paxton Clock and Data'
    desc = 'Clock and Data interface for paxton entry systems.'
    license = 'gplv3+'
    inputs = ['logic']
    outputs = []
    tags = ['Embedded/industrial', 'RFID']
    channels = (
        {'id': 'clk', 'name': 'Clock', 'desc': 'Clock line'},
        {'id': 'dat', 'name': 'Data', 'desc': 'Data line'},
    )

    annotations = (                    # Implicitly assigned annotation type ID
        ('bit', 'Bit'),                # 0
        ('leadin', 'Lead In/Out'),     # 1
        ('digit', 'Digit'),            # 2
        ('card', 'Number'),            # 3
        ('parity', 'Parity'),          # 4
        ('lrc', 'LRC'),                # 5
        ('begin', 'Begin'),            # 6
        ('separator', 'Separator'),    # 7
        ('end', 'End'),                # 8
        ('unknown', 'Unknown'),        # 9
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('digits', 'Digits', (1, 2, 5, 6, 7, 8, 9,)),
        ('cards', 'Card', (3,)),
        ('parity', 'Parity', (4,)),
    )

    options = (
        {'id': 'leadin', 'desc': 'Number bits leadin', 'default': 10},
        {'id': 'leadout', 'desc': 'Number bits leadout', 'default': 10},
        {'id': 'edge', 'desc': 'Data valid on edge', 'default': 'falling', 'values': ('rising', 'falling') },
        {'id': 'polarity', 'desc': 'Data polarity', 'default': 'inverted', 'values': ('normal', 'inverted') },
    )

    def __init__(self):
        self.STATE_LEADIN = 0
        self.STATE_LEADOUT = 1
        self.STATE_DIGITS = 2
        self.STATE_LRC = 3

        self.reset()

    def reset(self):
        '''Set global variables to default values called after each packet'''
        self.card_ss = None               # start sequence for card annotations
        self.card_es = None               # end sequence for card annotations
        self.card_start = 0               # flag for start of card data
        self.card_decoded = ""            # card numbers to be printed

        self.digit_ss = None             # start sequence for digit annotations
        self.digit_type = self.STATE_LEADIN   # digit type being decoded

        self.bit_ss = None               # start sequence for digit annotations
        self.bit = None                  # current bit
        self.bits = []                   # bit list to decode
        
        self.bcd_list = []               # BCD digit list to calc LRC
        self.calc_LRC = []               # calculated LRC to compare

    def start(self):
        '''Register output types and verify user supplied decoder values.'''
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def _check_parity(self):
        '''Count the number of 1s in the 5-bit sequence return True if odd'''
        ones_count = sum(self.bits)
        # Check if the parity is odd
        if ones_count % 2 == 1:
            return True  # Parity is odd
        else:
            return False  # Parity is even

    def _calculate_lrc(self):
        '''Calculate LRC over received digits and return it as bit list'''
        # Initialise a list to store the even parity bits
        even_parity_bits = [0, 0, 0, 0]
        # Calculate even parity bits for each position
        for i in range(4):
            even_parity_bits[i] = sum(bcd[i] for bcd in self.bcd_list) % 2
    
        # Calculate the odd parity bit over the even parity bits
        ones_count = sum(even_parity_bits)
        if ones_count % 2 == 1:
            odd_parity_bit = 0
        else:
            odd_parity_bit = 1

        self.calc_LRC = even_parity_bits + [odd_parity_bit]

    def _get_num(self):
        '''Get the current digit from bits[] and return it as hex'''
        if len(self.bits) < 5:
            return None
        # save the BCD number to a list so we can check the LRC
        self.bcd_list.append(self.bits[:4])
        # check the parity and warn if error
        if not self._check_parity():
            ann = [4, ["Even"]]
        else:
            ann = [4, ["Odd "]]
        self.put(self.digit_ss, self.samplenum, self.out_ann, ann)

        dec_val = 8 * self.bits[3] + 4 * self.bits[2] + \
                  2 * self.bits[1] + 1 * self.bits[0]
        hex_val = hex(dec_val)[2:]  # Remove the '0x' prefix

        return hex_val

    def _digit_ann(self, ann_type, digit):
        '''Write a digit annotation of type ann_type to the trace'''
        ann = [ann_type, [digit]]
        self.put(self.digit_ss, self.samplenum, self.out_ann, ann)
        # setup to catch next 5 bits
        self.digit_ss = None             # clear start pos ready for new digit
        self.bits.clear()

    def _card_ann(self, ann_type):
        '''Write a card annotation of type ann_type to the trace'''
        if not self.card_decoded:
            digit = "No Data"
        else:
            digit = self.card_decoded
        ann = [ann_type, [digit]]
        self.put(self.card_ss, self.card_es, self.out_ann, ann)
        # setup for next number
        self.card_ss = None
        self.card_decoded = ""

    def _update_state(self):
        '''Update the annotations and bit values after each bit received'''
        if self.bit is not None:
            self.bits.append(self.bit)
            self.put(self.bit_ss, self.samplenum, self.out_ann,
                     [0, [str(self.bit)]])

        if self.digit_ss is None:              # if we arent decoding a digit
            self.digit_ss = self.bit_ss        # set start of digit
        if self.card_ss is None:               # if we arent decoding a card No
            self.card_ss = self.bit_ss         # set start of card data

        if self.digit_type == self.STATE_LEADIN:
            leadin = self.options['leadin']
            if len(self.bits) == leadin:
                ann = [1, [str("Lead in")]]
                self.put(self.digit_ss, self.samplenum, self.out_ann, ann)
                # setup to catch digits
                self.digit_ss = None
                self.digit_type = self.STATE_DIGITS
                self.bits.clear()

        if self.digit_type == self.STATE_LEADOUT:
            # if the packet is done reset for another one
            leadout = self.options['leadout']
            if len(self.bits) == leadout:
                ann = [1, [str("Lead out")]]
                self.put(self.digit_ss, self.samplenum, self.out_ann, ann)
                self.digit_ss = None
                self.reset()

        if self.digit_type == self.STATE_DIGITS:       # handle decoding digits
            if len(self.bits) == 5:
                digit = self._get_num()

                if digit == "b":
                    self._digit_ann(6, digit)        # digit type: begin
                    self.card_start = 1              # start decoding card data
                    self.card_ss = None              # set start of card data
                elif digit == "d":
                    self._digit_ann(7, digit)        # digit type: separator
                    self._card_ann(3)                # write last card number
                elif digit == "f":
                    self._digit_ann(8, digit)          # digit type: end
                    self._card_ann(3)                  # write last card number
                    self._calculate_lrc()              # calc LRC to compare
                    self.digit_type = self.STATE_LRC   # Next byte is LRC data
                elif self.card_start == 1:
                    self._digit_ann(2, digit)          # digit type: digit
                    self.card_decoded += str(digit)    # add digit to card num
                    self.card_es = self.samplenum      # increment es
                else:
                    self._digit_ann(9, digit)          # digit type: unknown

        if self.digit_type == self.STATE_LRC:
            if len(self.bits) == 5:
                if self.calc_LRC != self.bits:       # LRC matches calculated?
                    ann = [4, ["LRC Error"]]
                    self.put(self.digit_ss, self.samplenum, self.out_ann, ann)
                digit = self._get_num()
                self._digit_ann(5, digit)
                # setup to catch last 10 bits
                self.digit_type = self.STATE_LEADOUT

    def decode(self):
        '''Capture a bit on the clk capture edge and update on update edge'''
        edge = self.options['edge']

        capture_edge = 'r' if edge == 'rising' else 'f'
        update_edge  = 'f' if edge == 'rising' else 'r'

        polarity = self.options['polarity']
        bit_map = {0: 1, 1: 0} if polarity == 'inverted' else {0: 0, 1: 1}

        while True:
            # wait for clk capture edge
            (clk, dat) = self.wait({0: capture_edge})

            # start new bit
            self.bit_ss = self.samplenum
            self.bit = bit_map[dat]

            self.wait({0: update_edge})
            # end bit annotation
            self._update_state()
