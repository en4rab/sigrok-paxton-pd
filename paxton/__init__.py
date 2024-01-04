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

'''
The Clock/Data interface is a de facto wiring standard commonly used to connect
a card swipe mechanism to the rest of an electronic entry system.

Details:
https://web.archive.org/web/20211208093044/https://www.securitytechnologiesgroup.co.uk/downloads/Ref_Pyramid_Series_Magnetic_Stripe_Data_Format.pdf

'''

from .pd import Decoder
