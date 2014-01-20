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

import regex


def compile_rex(str_rex):
    return regex.compile(str_rex, flags=regex.IGNORECASE)


class PostCodes:
    
    def __init__(self):
        # From http://stackoverflow.com/a/10529103/1285620
        self.regex = {
            'us':compile_rex(r'\d{5}([\-]?\d{4})?'),
            'uk':compile_rex(r'(GIR|[A-Z]\d[A-Z\d]??|[A-Z]{2}\d[A-Z\d]??)[ ]??(\d[A-Z]{2})'),
            'de':compile_rex(r'\b((?:0[1-46-9]\d{3})|(?:[1-357-9]\d{4})|(?:[4][0-24-9]\d{3})|(?:[6][013-9]\d{3}))\b'),
            'ca':compile_rex(r'([ABCEGHJKLMNPRSTVXY]\d[ABCEGHJKLMNPRSTVWXYZ])\ {0,1}(\d[ABCEGHJKLMNPRSTVWXYZ]\d)'),
            'fr':compile_rex(r'(F-)?((2[A|B])|[0-9]{2})[0-9]{3}'),
            'it':compile_rex(r'(V-|I-)?[0-9]{5}'),
            'au':compile_rex(r'(0[289][0-9]{2})|([1345689][0-9]{3})|(2[0-8][0-9]{2})|(290[0-9])|(291[0-4])|(7[0-4][0-9]{2})|(7[8-9][0-9]{2})'),
            'nl':compile_rex(r'\b[1-9][0-9]{3}\s?([a-zA-Z]{2})\b'),
            'es':compile_rex(r'([1-9]{2}|[0-9][1-9]|[1-9][0-9])[0-9]{3}'),
            'dk':compile_rex(r'([D-d][K-k])?( |-)?[1-9]{1}[0-9]{3}'),
            'se':compile_rex(r'(s-|S-){0,1}[0-9]{3}\s?[0-9]{2}'),
            'be':compile_rex(r'[1-9]{1}[0-9]{3}')
        }


if __name__=="__main__":
    pc = PostCodes()
    # Sanity check: make sure the keys match country TLDs
    from worldCountries import WorldCountries
    tlds = WorldCountries().tldsSet
    unknowns = set(pc.regex.keys()).difference(tlds)
    if len(unknowns):
        print 'Unknown TLDs:', sorted(unknowns)
    else:
        print 'OK'
    