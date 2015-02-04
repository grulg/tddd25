# -----------------------------------------------------------------------------
# Distributed Systems (TDDD25)
# -----------------------------------------------------------------------------
# Author: Sergiu Rafiliu (sergiu.rafiliu@liu.se)
# Modified: 24 July 2013
#
# Copyright 2012 Linkoping University
# -----------------------------------------------------------------------------

"""Implementation of a simple database class."""

import random


class Database(object):

    """Class containing a database implementation."""

    def __init__(self, db_file):
        self.db_file = db_file
        self.rand = random.Random()
        self.rand.seed()
        
        self.data = []
        with open(self.db_file, "r") as f:
            elem = ""
            for line in f:
                if(line[0] == "%"):
                    self.data.append(elem)
                    elem = ""
                else:
                    elem += line + "\n"
        
        print("Number of fortunes: " + str(len(self.data)))

    def read(self):
        """Read a random location in the database."""
        #
        # Your code here.
        #
        random_index = self.rand.randint(0, len(self.data)-1);
        return self.data[random_index]

    def write(self, fortune):
        """Write a new fortune to the database."""
        #
        # Your code here.
        #
        self.data.append(fortune)
        print("writing " + fortune)
        with open(self.db_file, "a") as f:
            f.write(fortune+"\n%\n")
