import numpy as np
import ads
import pandas as pd
from numpy  import array
import json
import flask
from flask import Flask, request
from flask_restful import Resource, Api
import config

def resolve_references(refdata):
    # Instantiate the Resolver class
    rsvr = Resolver()
    # First clean the reference data we have been given
    if isinstance(refdata, str):
        try:
            refdata = uh.u2asc(refdata)
        except:
            raise UnicodeDecodingError
    elif isinstance(refdata, list):
        tmp = []
        for ref in refdata:
            try:
                tmp.append(uh.u2asc(ref))
            except:
                sys.stderr.write('Unicode error while converting: %s\n'%ref)
        refdata = tmp
    # Now hand the referene data over to the resolver
    rsvr.resolve(refdata)
    # Return the results
    return rsvr.results



class Resolver:
    def __init__(self):
        self.resolverURL = config.RESOLVER_URL
        self.maxURLlength= config.URL_MAX
        self.LevelMapping= config.LEVEL_MAPPING
        user = "%s@%s" % (config.USER_NAME or 'anonymous', socket.gethostname())
        self.headers = {
                         'User-Agent': 'ADS Reference Resolver Python Client version %s; %s'%(config.RESCLIENT_VERSION,user),
                         'From': '%s' % user,
                         'Content-Type':'application/x-www-form-urlencoded'
                       }
        self.params = {}

    def resolve(self,refdata):
        self.results = []
        if not refdata:
            """
            Really? You called us without given anything to work on?
            """
            raise NoReferenceDataSupplied
        if isinstance(refdata,str):
            """
            This is either one string, or a newline-separated list
            """
            reflist = refdata.split('\n')
        elif isinstance(refdata,list):
            """
            In case of a list of reference strings, there's nothing to be done
            """
            reflist = refdata
        else:
            """
            We don't accept any other formats
            """
            raise InvalidReferenceDataSupplied
        # Fire off the requests to the reference resolver service
        for ref in reflist:
            self.params['resolvethose'] = ref
            self.headers['Content-Length'] = len(self.params['resolvethose'])
            try:
                r = requests.post(self.resolverURL, data=self.params, headers=self.headers)
            except:
                raise ResolveRequestFailed
        # Parse the response and return the results as a list of dictionaries
            self.results += self.__parse_results(r.text.strip())

    def __parse_results(self,results):
        """
        The resolve server responds with some basic HTML formatting, where the actual
        results are listed as an HTML list. The regular expression RE_RESULT captures
        each entry
        """
        reslist = []
        cursor = 0
        match  = RE_RESULTS.search(results,cursor)
        while match:
            doc = {}
            doc['bibcode'] = match.group('bibcode')
            doc['confidence'] = self.__get_confidence_level(match.group('confidence'))
            doc['refstring'] = match.group('refstring')
            reslist.append(doc)
            cursor = match.end()
            match  = RE_RESULTS.search(results,cursor)
        return reslist

    def __get_confidence_level(self,level):
        """
        In essence the resolver confidence levels in the range [0,1,2,3,4,5]. In the case
        of '0' the resolver really couldn't make anything from the reference string. Sometimes
        the resolver comes up with a bibcode, either because the journal string found matches
        an known journal close enough, or because the record simply isn't in the ADS. In those
        cases a '5' is assigned. Be very careful with these bibcodes! All other cases are
        considered as success.
        """
        return self.LevelMapping[level]

ref_String = "Abt, H. 1990, ApJ, 357, 1"
resolve_references(ref_String)
