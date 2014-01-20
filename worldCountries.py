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
from unidecode import unidecode
from unicodeManager.reader import UnicodeReader


class WorldCountries():
    def __init__(self):
        self.namesSet = set()
        self.tldsSet = set()
        self.alternative2name = {}
        self.tld2name = {}

        # The list of country names, alternative spellings, and 2-letter codes (TLDs)
        f = open(os.path.join(os.path.abspath('.'), 'data', 'countries.csv'), 'rb')
        reader = UnicodeReader(f)
        reader.next()
        for row in reader:
#            cid = int(row[0])
            # The country name
            name = unidecode(row[1]).lower().strip()
            self.namesSet.add(name)
            self.alternative2name[name] = name
            
            # Different alternative names, separated by comma
            alternatives = [unidecode(a).lower().strip() for a in row[2].split(',') if len(row[2].strip())]
            for a in alternatives:
                self.alternative2name[a] = name
                self.namesSet.add(a)
                
            # The 2-letter codes (TLDs)
            codes = [t.lower().strip() for t in row[4].split(',')]
            for c in [c for c in codes if len(c)]:
                self.tld2name[c] = name
                self.tldsSet.add(c)
        f.close()
        

if __name__=="__main__":
    countries = WorldCountries()
    print len(countries.namesSet), 'country names and variations thereof'
    
    shortCountries = [c for c in sorted(countries.namesSet, key=lambda c:len(c)) if len(c)<5]
    print 'Short country names:', shortCountries