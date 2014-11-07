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
from collections import Counter


from usaStates import USAStates
from brazilStates import BrazilStates
from canadaProvinces import CanadaProvinces
from worldCountries import WorldCountries
from worldCities import WorldCities
from postCodes import PostCodes



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
        
        # Rule types
        self.R_COUNTRY = 0
        self.R_STATE = 1
        self.R_BIG_CITY = 2
        self.R_ANY_CITY = 3
        self.R_POST_CODE = 4
        self.R_TLD = 5
        self.R_STATE_ABBREV = 6
        
        # Rule labels
        self.rule_labels = {
            self.R_COUNTRY:'Country',
            self.R_STATE:'State',
            self.R_BIG_CITY:'Big city',
            self.R_ANY_CITY:'Any city',
            self.R_POST_CODE:'Post code',
            self.R_TLD:'TLD',
            self.R_STATE_ABBREV:'State abbrev'
        }
        
        # Loading data
        print "Loading data"
        ##timing.log(clock())
        
        self.USAStates = USAStates()
        self.BrazilStates = BrazilStates()
        self.CanadaProvinces = CanadaProvinces()
        self.WorldCountries = WorldCountries()
        self.WorldCities = WorldCities(self.MIN_CITY_LENGTH, self.MIN_POPULATION)
        self.PostCodes = PostCodes()
        
        # Store the city names also as a suffix tree
        print 'Creating suffix trees for city names'
        ##timing.log(clock())
        
        # 1) Large cities
        self.stdWorldCitiesLarge = SuffixTree.SubstringDict()
        for city in self.WorldCities.largeCity2countryPopulation.iterkeys():
            self.stdWorldCitiesLarge[city] = city
        # 2) All cities
        self.stdWorldCitiesAll = SuffixTree.SubstringDict()
        for city in self.WorldCities.city2countryPopulation.iterkeys():
            self.stdWorldCitiesAll[city] = city

        print 'Done initialising'
        #timing.log(clock())
        
    
    def __get_trailing_number(self, s):
        m = re.search(r'\d+$', s)
        return m.group() if m else None


    '''Split a string into comma parts.'''
    def __commaParts(self, location_norm):
        return [p for p in [p.strip() for p in location_norm.split(',')] if len(p)]
    
    
    '''Split a string into parts on any non-alphabetic character.'''
    def __parts(self, location_norm):
        return [p for p in re.split(r'[^A-Za-z]', location_norm) if len(p)]
    
    
    '''Split a string into parts on any non-alphabetic character.
    Substrings from the exceptions list do not get split.'''
    def __partsWithoutSplitting(self, location_norm, exceptions):
        cpy_location_norm = location_norm[:] #creates copy
        parts = []
        for word in exceptions:
            if word in location_norm:
                parts.append(word)
                cpy_location_norm=cpy_location_norm.replace(word, ' ')
        parts.extend( re.split(r'[^A-Za-z]', cpy_location_norm) )
        return [p for p in parts if len(p)]
        
        
    def __multiWords(self, strSet):
        return [c for c in strSet if len(c.split())>1 or len(c.split('.'))>1]
        
    '''Look for country names inside the string.'''
    def __searchCountry(self, location_norm):
        # Exclude names of US states (Georgia) or Canadian provinces
        clear_countries = self.WorldCountries.namesSet#.difference(self.USAStates.namesSet.union(self.CanadaProvinces.namesSet))
        
        # Do not split multi-word country names if they appear as substrings
        multiwords = self.__multiWords(clear_countries)
        parts = self.__partsWithoutSplitting(location_norm, multiwords)
                
        # Look for occurrences of country names in the list of parts
#        candidates = set([self.WorldCountries.alternative2name[c] for c in clear_countries if c in parts and len(c)>=self.MIN_COUNTRY_LENGTH])
        return set([self.WorldCountries.alternative2name[c] for c in clear_countries if c in parts])
        
        
    '''Search for names of states for a given country (USA, Canada, Brazil)'''
    def __searchState(self, location_norm, namesSet):
        multiwords = self.__multiWords(namesSet)
        parts = self.__partsWithoutSplitting(location_norm, multiwords)
        return set(parts).intersection(namesSet)
    
        
    '''Search for 2-letter state abbreviations for a given country (USA, Canada, Brazil)'''
    def __searchStateAbbrevEnd(self, location_norm, abbrevsSet):
        intersect = set()
        
        # Compute comma parts
        comma_parts = self.__commaParts(location_norm)
        if len(comma_parts) > 1:
            intersect.update( set(comma_parts).intersection(abbrevsSet) )
            
            # Last comma part might be of the form:
            # 773 white road, bowdoinham, me 04008
            last = comma_parts[-1]
            # Get trailing number, check if post-code-like
            number = self.__get_trailing_number(last)
            if number is not None and len(number)==5:
                # Look for USA state abbrev
                parts = self.__parts(last)
                intersect.update( set(parts).intersection(abbrevsSet) )
        
        # If there are no commas to split on, check last space part
        elif len(comma_parts) == 1:
            parts = self.__parts(location_norm)
            if len(parts):
                intersect.update( set([parts[-1]]).intersection(abbrevsSet))
        
        return intersect


    '''Search for names of big cities (>=MIN_POPULATION). If multiple, keep only the largest.'''
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
                most_likely_country = sorted(self.WorldCities.largeCity2countryPopulation[city], key=lambda e:-e[1])[0]
                candidate_countries.add(self.WorldCountries.alternative2name[most_likely_country[0]])
#                for (c,_) in self.WorldCities.largeCity2countryPopulation[city]:
#                    candidate_countries.add(self.WorldCountries.alternative2name[c])
                    
        return candidate_countries
            
    
    '''Search for names of any cities. Keep all results.'''
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
                where_is = set()
                for (c,_) in self.WorldCities.city2countryPopulation[city]:
                    where_is.add(self.WorldCountries.alternative2name[c])
            
                if self.WorldCountries.alternative2name['usa'] in where_is:
                    # Check if last part is an abbreviation of a US state
                    all_parts = self.__parts(location_norm)
                    if all_parts[-1] in self.USAStates.abbrevsSet:
                        where_is = [self.WorldCountries.alternative2name['usa']]
                candidate_countries.update(where_is)
                    
        return candidate_countries
        
        
    '''Search for post codes for different countries.'''
    def __searchPostCode(self, location_norm):
        candidates = set()
        for tld, rex in self.PostCodes.regex.iteritems():
            m = rex.search(location_norm)
            if m is not None:
                candidates.add(self.WorldCountries.tld2name[tld])
        return candidates
    
    
        
    def apply_rules(self, location_norm):
        candidates = set()
        
        # Look for occurences of country names
        found_countries = self.__searchCountry(location_norm)
        if len(found_countries):
            candidates.update([(c, self.R_COUNTRY) for c in sorted(found_countries)])

        # Look for state names (USA, Canada, Brazil)
        # USA
        states = self.USAStates.namesSet
        if len(self.__searchState(location_norm, states)):
            candidates.add((self.WorldCountries.alternative2name['usa'], self.R_STATE))
        # Canada
        states = self.CanadaProvinces.namesSet
        if len(self.__searchState(location_norm, states)):
            candidates.add((self.WorldCountries.alternative2name['canada'], self.R_STATE))
        # Brazil
        states = self.BrazilStates.namesSet
        if len(self.__searchState(location_norm, states)):
            candidates.add((self.WorldCountries.alternative2name['brazil'], self.R_STATE))

        # Look for 2-letter state/country codes at the end of the string
        # USA
        abbrevs = self.USAStates.abbrevsSet
        if len(self.__searchStateAbbrevEnd(location_norm, abbrevs)):
            candidates.add((self.WorldCountries.alternative2name['usa'], self.R_STATE_ABBREV))
        # Canada
        abbrevs = self.CanadaProvinces.abbrevsSet
        if len(self.__searchStateAbbrevEnd(location_norm, abbrevs)):
            candidates.add((self.WorldCountries.alternative2name['canada'], self.R_STATE_ABBREV))
        # Brazil
        abbrevs = self.BrazilStates.abbrevsSet
        if len(self.__searchStateAbbrevEnd(location_norm, abbrevs)):
            candidates.add((self.WorldCountries.alternative2name['brazil'], self.R_STATE_ABBREV))
        # Any country TLD
        abbrevs = self.WorldCountries.tldsSet
        matches = self.__searchStateAbbrevEnd(location_norm, abbrevs)
        candidates.update([(self.WorldCountries.tld2name[c], self.R_TLD) for c in matches])
        
        # Look for large cities
        found_countries = self.__searchLargeCity(location_norm)
        if len(found_countries):
            candidates.update([(c, self.R_BIG_CITY) for c in sorted(found_countries)])
        
        # Look for other cities
        found_countries = self.__searchAnyCity(location_norm)
        if len(found_countries):
            candidates.update([(c, self.R_ANY_CITY) for c in sorted(found_countries)])
        
        # Look for post codes
        found_countries = self.__searchPostCode(location_norm)
        if len(found_countries):
            candidates.update([(c, self.R_POST_CODE) for c in sorted(found_countries)])
        
        return candidates
    
    
    def guess(self, location):
        # Transliterate / remove diacritics / convert to lower case
        location_norm = unidecode(location).lower().strip()

        candidates = self.apply_rules(location_norm)
        
        if len(candidates):
            # Remove (c,ANY_CITY) if also (c,BIG_CITY)
            remove = [(c,self.R_ANY_CITY) for (c,_) in candidates if (c,self.R_BIG_CITY) in candidates and (c,self.R_ANY_CITY) in candidates]
            candidates.difference_update(remove)
            
            # Count the distinct countries. Only one country = easy guess
            distinct_countries = set([c for (c,_) in candidates])
            if len(distinct_countries) == 1:
                return sorted(distinct_countries)
            
            # Simple majority vote: if multiple clues point to the same country, that's the country
            results = [(c,self.rule_labels[r]) for (c,r) in candidates]
            counter = Counter([elem[0] for elem in results])
            max_count = max(counter.items(), key=lambda elem:elem[1])[1]
            if max_count > 1:
                countries = [c for c,v in counter.items() if v==max_count]
                return sorted(countries)

            # Big city > any city
            na = len(set([c for (c,r) in candidates 
                      if r != self.R_BIG_CITY 
                      and r != self.R_ANY_CITY]))
            if not na:
                countries = set([c for (c,_) in candidates 
                             if (c,self.R_BIG_CITY) in candidates])
                if len(countries):
                    return sorted(countries)
            
            # Country > anything else
            countries = set([c for (c,_) in candidates 
                         if (c,self.R_COUNTRY) in candidates])
            if len(countries):
                return list(countries)
            
            # State_abbrev & TLD => State_abbrev
            na = len(set([c for (c,r) in candidates 
                      if r != self.R_STATE_ABBREV 
                      and r != self.R_TLD]))
            if not na:
                countries = set([c for (c,_) in candidates 
                             if (c,self.R_STATE_ABBREV) in candidates])
                if len(countries) == 1:
                    return sorted(countries)

            # State > any_city
            na = len(set([c for (c,r) in candidates 
                      if r != self.R_STATE 
                      and r != self.R_ANY_CITY]))
            if not na:
                countries = set([c for (c,_) in candidates 
                             if (c,self.R_STATE) in candidates])
                if len(countries) == 1:
                    return sorted(countries)
            
            print location_norm, '--', results, '--', counter
            
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

