# This Python file uses the following encoding: utf-8

"""Copyright 2014 Bogdan Vasilescu
Eindhoven University of Technology

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

import os
from unicodeManager import UnicodeReader

this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, 'data')

class BlackList:
    def __init__(self):
        self.dict = {}
        
        # Load data
        f = open(os.path.join(DATA_PATH, 'blackList.csv'), 'rb')
        reader = UnicodeReader(f)
        for row in reader:
            name = row[0].lower().strip()
            self.dict[name] = 1
        f.close()


if __name__=="__main__":
    bl = BlackList()
    print len(bl.dict.keys()), 'entries in the black list'

