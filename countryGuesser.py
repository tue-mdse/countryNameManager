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

import timing
from time import clock
from unidecode import unidecode
import re
import SuffixTree.SubstringDict


from usaStates import USAStates
from canadaProvinces import CanadaProvinces
from worldCountries import WorldCountries
from worldCities import WorldCities



def removeSubstrings(listOfStrings):
    # Insert all strings into a suffix tree
    std = SuffixTree.SubstringDict()
    for s in listOfStrings:
        std[s] = 1
    withoutSubstrings = set()
    for s in listOfStrings:
        # Only return those elements for which there is no suffix
        if len(std[s]) == 1:
            withoutSubstrings.add(s)
    return sorted(withoutSubstrings)



class CountryGuesser:
    
    def __init__(self):
        self.MIN_POPULATION = 100000
        self.MIN_CITY_LENGTH = 4
        self.MIN_COUNTRY_LENGTH = 5
        self.MIN_SUBSTRING_LENGTH = 5
        
        # Loading data
        print 'Loading data'
        timing.log(clock())
        
        self.USAStates = USAStates()
        self.CanadaProvinces = CanadaProvinces()
        self.WorldCountries = WorldCountries()
        self.WorldCities = WorldCities(self.MIN_CITY_LENGTH, self.MIN_POPULATION)
        
        # Store the city names also as a suffix tree
        print 'Creating suffix trees for city names'
        timing.log(clock())
        
        # 1) Large cities
        self.stdWorldCitiesLarge = SuffixTree.SubstringDict()
        for city in self.WorldCities.largeCity2countryPopulation.iterkeys():
            self.stdWorldCitiesLarge[city] = city
        # 2) All cities
        self.stdWorldCitiesAll = SuffixTree.SubstringDict()
        for city in self.WorldCities.city2countryPopulation.iterkeys():
            self.stdWorldCitiesAll[city] = city

        print 'Done initialising'
        timing.log(clock())
        
    
    def __get_trailing_number(self, s):
        m = re.search(r'\d+$', s)
        return m.group() if m else None

    
    def __commaParts(self, location_norm):
        return [p for p in [p.strip() for p in location_norm.split(',')] if len(p)]
    
    
    def __parts(self, location_norm):
        return [p for p in re.split(r'[^A-Za-z]', location_norm) if len(p)]
    
    
    def __partsWithoutSplitting(self, location_norm, exceptions):
        cpy_location_norm = location_norm[:]
        parts = []
        for word in exceptions:
            if word in location_norm:
                parts.append(word)
                cpy_location_norm=cpy_location_norm.replace(word, ' ')
        parts.extend( re.split(r'[^A-Za-z]', cpy_location_norm) )
        return [p for p in parts if len(p)]
    
        
    # Look for country names inside the string
    def __searchCountry(self, location_norm):
        # Exclude names of US states or Canadian provinces
        clear_countries = self.WorldCountries.namesSet.difference(self.USAStates.namesSet.union(self.CanadaProvinces.namesSet))
        # Do not split multi-word country names if they appear as substrings
        multiwords = [c for c in clear_countries if len(c.split())>1]
        
        # Compute parts
        parts = self.__partsWithoutSplitting(location_norm, multiwords)
                
        # Look for occurrences of country names in the list of parts
#        candidates = set([self.WorldCountries.alternative2name[c] for c in clear_countries if c in parts and len(c)>=self.MIN_COUNTRY_LENGTH])
        return set([self.WorldCountries.alternative2name[c] for c in clear_countries if c in parts])
        
        
    def __searchUSAState(self, location_norm):
        # Exclude names of countries or Canadian provinces
        clear_states = self.USAStates.namesSet.difference(self.WorldCountries.namesSet.union(self.CanadaProvinces.namesSet))
        # Do not split multi-word state names if they appear as substrings
        multiwords = [c for c in clear_states if len(c.split())>1]
        
        # Compute parts
        parts = self.__partsWithoutSplitting(location_norm, multiwords)
        
        # Look for occurrences of country names in the list of parts
        return set(parts).intersection(clear_states)
        
        
    def __searchCanadaProvince(self, location_norm):
        # Exclude names of countries or US states
        clear_states = self.CanadaProvinces.namesSet.difference(self.WorldCountries.namesSet.union(self.USAStates.namesSet))
        # Do not split multi-word state names if they appear as substrings
        multiwords = [c for c in clear_states if len(c.split())>1]
        
        # Compute parts
        parts = self.__partsWithoutSplitting(location_norm, multiwords)
        
        # Look for occurrences of country names in the list of parts
        return set(parts).intersection(clear_states)
    
    
    def __searchUSAAbbrev(self, location_norm):
        # Exclude TLDs or Canadian abbrevs
        clear_abbrevs = self.USAStates.abbrevsSet.difference(self.WorldCountries.tldsSet.union(self.CanadaProvinces.abbrevsSet))
        
        # Compute comma parts
        comma_parts = self.__commaParts(location_norm)
        if len(comma_parts):
            intersect = set(comma_parts).intersection(clear_abbrevs)
            if len(intersect):
                return intersect
            
            # Last comma part might be of the form:
            # 773 white road, bowdoinham, me 04008
            last = comma_parts[-1]
            # Get trailing number, check if post-code-like
            number = self.__get_trailing_number(last)
            if number is not None and len(number)==5:
                # Look for USA state abbrev
                parts = self.__partsWithoutSplitting(last, [])
                return set(parts).intersection(self.USAStates.abbrevsSet)
        
        return set()
    
        
    def __searchUSAAbbrevApx(self, location_norm):
        # Exclude TLDs or Canadian abbrevs
        clear_abbrevs = self.USAStates.abbrevsSet.difference(self.WorldCountries.tldsSet.union(self.CanadaProvinces.abbrevsSet))
        
        # Compute parts
        parts = self.__partsWithoutSplitting(location_norm, [])
        if len(parts):
            return set(parts).intersection(clear_abbrevs)
        return set()
    
    
    def __searchCanadaAbbrev(self, location_norm):
        # Exclude TLDs or USA abbrevs
        clear_abbrevs = self.CanadaProvinces.abbrevsSet.difference(self.WorldCountries.tldsSet.union(self.USAStates.abbrevsSet))
        
        # Compute comma parts
        comma_parts = self.__commaParts(location_norm)
        if len(comma_parts):
            return set(comma_parts).intersection(clear_abbrevs)
        return set()
    

    def __searchCanadaAbbrevApx(self, location_norm):
        # Exclude TLDs or USA abbrevs
        clear_abbrevs = self.CanadaProvinces.abbrevsSet.difference(self.WorldCountries.tldsSet.union(self.USAStates.abbrevsSet))
        
        # Compute parts
        parts = self.__partsWithoutSplitting(location_norm, [])
        if len(parts):
            return set(parts).intersection(clear_abbrevs)
        return set()
    
    
    def __searchTLD(self, location_norm):
        candidates = set()
        if len(location_norm) == 3 and location_norm[0] == '.':
            code = location_norm[1:]
            if self.WorldCountries.tld2name.has_key(code):
                candidates.add(self.WorldCountries.tld2name[code])
        return candidates
        
        
    def __searchLargeCity(self, location_norm):
        candidate_countries = set()
        # Compute parts
        parts = [p for p in self.__parts(location_norm) if len(p)>=self.MIN_CITY_LENGTH]
        if len(parts):
            # Store the location string as a suffix tree 
            std = SuffixTree.SubstringDict()
            std[location_norm] = True
            
            # Look for candidate cities among the parts
            candidates = set()
            for p in parts:
                suffixes = self.stdWorldCitiesLarge[p]
                for suf in suffixes:
                    if len(std[suf]):
                        candidates.add(suf)
                        
            # Remove substrings from the list of candidates
            # ['paris', 'saint-marc', 'saint-marcel']
            # ['paris', 'saint-marcel']
            pruned = removeSubstrings(candidates)
            
            for city in pruned:
                for (c,_) in self.WorldCities.largeCity2countryPopulation[city]:
                    candidate_countries.add(self.WorldCountries.alternative2name[c])
        return candidate_countries
            
    
    def __searchAnyCity(self, location_norm):
        candidate_countries = set()
        # Compute parts
        parts = [p for p in self.__parts(location_norm) if len(p)>=self.MIN_CITY_LENGTH]
        if len(parts):
            # Store the location string as a suffix tree 
            std = SuffixTree.SubstringDict()
            std[location_norm] = True
            
            # Look for candidate cities among the parts
            candidates = set()
            for p in parts:
                suffixes = self.stdWorldCitiesAll[p]
                for suf in suffixes:
                    if len(std[suf]):
                        candidates.add(suf)
                        
            # Remove substrings from the list of candidates
            # ['paris', 'saint-marc', 'saint-marcel']
            # ['paris', 'saint-marcel']
            pruned = removeSubstrings(candidates)
            
            for city in pruned:
                for (c,_) in self.WorldCities.city2countryPopulation[city]:
                    candidate_countries.add(self.WorldCountries.alternative2name[c])
        return candidate_countries
        
        
        
    def guess(self, location):
        # Transliterate / remove diacritics / convert to lower case
        location_norm = unidecode(location).lower().strip()
        
        # Look for USA state abbrev as comma part
        if len(self.__searchUSAAbbrev(location_norm)):
            return [self.WorldCountries.alternative2name['usa']]
        
        # Look for Canada province abbrev as comma part
        if len(self.__searchCanadaAbbrev(location_norm)):
            return [self.WorldCountries.alternative2name['canada']]
        
        # Look for occurences of country names
        found_countries = self.__searchCountry(location_norm)
        if len(found_countries):
            return sorted(found_countries)

        # Look for US state names
        if len(self.__searchUSAState(location_norm)):
            return [self.WorldCountries.alternative2name['usa']]
        
        # Look for Canada province name
        if len(self.__searchCanadaProvince(location_norm)):
            return [self.WorldCountries.alternative2name['canada']]
        
        # Look for large cities
        found_countries = self.__searchLargeCity(location_norm)
        if len(found_countries):
            return sorted(found_countries)
        
        # Look for other cities
        found_countries = self.__searchAnyCity(location_norm)
        if len(found_countries):
            return sorted(found_countries)
        
        # Look for USA state abbrev anywhere
        if len(self.__searchUSAAbbrev(location_norm)):
            return [self.WorldCountries.alternative2name['usa']]
        
        # Look for Canada province abbrev anywhere
        if len(self.__searchCanadaAbbrev(location_norm)):
            return [self.WorldCountries.alternative2name['canada']]
        
        # Look for TLDs
        found_countries = self.__searchTLD(location_norm)
        if len(found_countries):
            return sorted(found_countries)
        
        return [None]
        
        
        
if __name__=="__main__":
    import os
    from unicodeManager.reader import UnicodeReader
    from unicodeManager.writer import UnicodeWriter
    
    g = open(os.path.join(os.path.abspath('.'), 'data', 'results.csv'), 'wb')
    writer = UnicodeWriter(g)
    
    cg = CountryGuesser()
    
    succ = 0
    fail = 0
    
    f = open(os.path.join(os.path.abspath('.'), 'data', 'sample.csv'), 'rb')
    reader = UnicodeReader(f)
    for row in reader:
        location = row[0]
        location_norm = unidecode(location).lower().strip()
        country = cg.guess(location)
        if country[0] is None:
            fail += 1
        else:
            succ += 1
        writer.writerow([location] + country)

    print succ, 'resolved'
    print fail, 'not resolved'
    
    f.close()
    g.close()

