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
from unicodeManager import UnicodeReader
from worldCountries import WorldCountries
from blackList import BlackList

this_dir, this_filename = os.path.split(__file__)
DATA_PATH = os.path.join(this_dir, 'data')

class WorldCities():
    
    def __init__(self, MIN_CITY_LENGTH=5, MIN_POPULATION=50000):
        self.MIN_CITY_LENGTH = MIN_CITY_LENGTH
        self.MIN_POPULATION = MIN_POPULATION
        
        # Most likely, these do not refer to actual city names
        self.blackList = BlackList().dict
#        print self.blackList.keys()

        self.city2countryPopulation = {}
        self.largeCity2countryPopulation = {}
        
        countries = WorldCountries()
        
        # Load data
        # GeoNames list of cities: http://download.geonames.org/export/dump/
        f = open(os.path.join(DATA_PATH, 'cities1000.csv'), 'rb')
        reader = UnicodeReader(f)
        
        for row in reader:
            city = unidecode(row[2]).lower().strip()
            # Alternative names/spellings for the same city
            alternatives = [a for a in [unidecode(a).lower().strip() for a in row[3].split(',')] 
                            if len(a) >= self.MIN_CITY_LENGTH 
                            and not self.blackList.has_key(a)]
            population = int(row[14])
            # Country 2-letter code
            code = row[8].lower()
            
            if len(city) >= self.MIN_CITY_LENGTH and not self.blackList.has_key(city):
                try:
                    country = countries.tld2name[code]
                except:
                    # Not all possible 2-letter country codes are known in countries.csv
                    # If necessary, add manually and rerun
                    print 'UNKNOWN CODE:', city, population, code
                    exit()
                    
                self.city2countryPopulation.setdefault(city, set([(country, population)]))
                self.city2countryPopulation[city].add((country, population))
                        
                # Record same country for all alternative names of this city
                for a in alternatives:
                    self.city2countryPopulation.setdefault(a, set([(country, population)]))
                    self.city2countryPopulation[a].add((country, population))
        
                # Also keep a shorter list with large cities only
                if population >= self.MIN_POPULATION:                
                    # Record country for this city
                    # Note: Two cities with the same name in different countries
                    # or even two cities with the same name in the same country
                    # are recorded separately
                    self.largeCity2countryPopulation.setdefault(city, set([(country, population)]))
                    self.largeCity2countryPopulation[city].add((country, population))
                        
                    # Record same country for all alternative names of this city
                    for a in alternatives:
                        self.largeCity2countryPopulation.setdefault(a, set([(country, population)]))
                        self.largeCity2countryPopulation[a].add((country, population))
        f.close()


if __name__=="__main__":
    cities = WorldCities()
            
    print
    print len(cities.largeCity2countryPopulation.keys()), 'world city names with population >=', cities.MIN_POPULATION
    print len(cities.city2countryPopulation.keys()), 'world city names'
