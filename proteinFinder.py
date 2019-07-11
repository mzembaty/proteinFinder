import csv
import argparse
import requests
import time
import json
import pandas as pd
from io import StringIO


####################
# Custome Errors ##
##################


###############
# Functions ##
#############
def initArguments():
    information = ('id,protein names,genes,existence,organism,ec,'
                   'feature(METAL BINDING),keywords,comment(PATHWAY),'
                   'comment(SUBCELLULAR LOCATION),comment(DOMAIN),families,'
                   'sequence')
    parser = argparse.ArgumentParser()
    parser.add_argument("inputFile", help="Path to csv"
                        "file with query strings")
    parser.add_argument("outputFile", help="Path to file the results should be"
                        "saved")
    parser.add_argument("website", help="Which website should be queried",
                        choices=['ncbi', 'uniprot', 'ncbi+uniprot'])
    parser.add_argument("--noheaders", help="When reading input csv does not"
                        "skip first row",
                        action="store_true")
    parser.add_argument("-db", "--database", help="Database which should"
                        "be queried", default="protein")
    parser.add_argument("-c", "--columns", help="When quiering Uniprot,"
                        "depicts, which type of information should be"
                        "downloaded. Terms have to be comma seperated",
                        default=information)
    parser.add_argument("--organism", help="Narrow down the search to"
                        "specified organism")
    parser.add_argument("-i", "--inputDataType", choices=['text', 'id'],
                        default='text', help="Type of data stored in "
                        "input File")
    parser.add_argument("--idType", help="What database the IDs are from?",
                        default="ACC+ID")
    args = parser.parse_args()
    return args


def readQueryFile(srcFile, noheaders=False):
    '''Read query strings from .csv file

    Parameters
    ----------
        srcFile: string
            Path to .csv file with query strings in first column.

        noheaders: boolean
            If true, first row of csv file will be skipped.

    Returns
    -------
        queryLst: list[string]
            List of query strings the databse should be searched for.

    '''

    with open(srcFile) as f:
        reader = csv.reader(f, delimiter=',')
        if noheaders is False:
            next(reader, None)
            # Feedback
            print("Skipping headers")
        queryLst = []
        orgaLst = []
        for row in reader:
            queryLst.append(str(row[0]))
            try:
                orgaLst.append(str(row[1]))
            except:
                pass
        # TODO add Organism

    if not any(queryLst):
        raise Exception("No data loaded")
    else:
        return queryLst, orgaLst


class NCBI:
    '''Object handling ncbi API

    Attributes
    ----------
    queryLst: list of str
        List with query strings the database should be searched for.
    db: str
        Name of the database, that should be searched in. Full list of options
        under:
        https://www.ncbi.nlm.nih.gov/books/NBK25497/table/chapter2.T._entrez_unique_identifiers_ui/?report=objectonly

    '''
    def __init__(self, queryLst, db):
        self.queryLst = queryLst

    def queryNcbiDb(self, queryLst, db="protein", outFormat="json"):
        '''Querys list of strings in NCBI database

        Makes http GET request to Query NCBI Entrez Programming Utilities
        (E-utilities) and retrieves response. Only 10 querys per second
        allowed.

        Parameters
        ----------
        queryLst: list of str:
            List with query strings the database should be searched for.
        db: str
            Name of the database that should be searched in.
        outFormat: str
            Output format response from the database ('xml' or 'json').

        Returns
        -------
            resLst: list of response objects
                List of response objects retrieved from the NCBI server
                by the GET() call.

        '''
        base_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        esearch_URL = base_URL + "esearch.fcgi/"

        # Parameters
        apiKey = "" # PUT YOUR KEY HERE FOR FASTER QUERY
        dbName = db
        outFormat = outFormat
        resLst = []

        queryLstLength = len(queryLst)
        assert queryLstLength != 0

        # one database request for each query
        for i, query_term in enumerate(queryLst):
            # Feedback
            print(f'Query {i+1} of {queryLstLength}')

            # request to database
            payload = {
                'term': query_term,
                'db': dbName,
                'retmode': outFormat,
                'api_key': apiKey,
                }
            response = requests.get(esearch_URL, payload)

            # handling errors
            if (not response.ok):
                print(response.status_code)

            resLst.append(response)
            # NCBI only allowes 10 querys per second with Key
            if apiKey:
                time.sleep(0.1)
            else:
                time.sleep(0.4)
        return resLst

    def getNcbiIdFromResponse(self, resLst, queryLst):
        '''process json server response / get the matching ids for the query

        Parameters
        ----------
        resLst: list of response objects
                List of response objects retrieved from the NCBI server.
        queryLst: list of str:
            List with query strings the database was searched by.

        Returns
        -------
        idsDic:dict
            KEY: Query string, VALUE: List of IDs from response.

        '''
        assert len(resLst) == len(queryLst)
        idsLst = []
        for response in resLst:
            responseJSON = json.loads(response.text)
            id = responseJSON['esearchresult']['idlist']
            if not id:
                idsLst.append(['Not Found'])
            else:
                idsLst.append(id)
        idsDic = dict(zip(queryLst, idsLst))
        return idsDic

    def query(self, queryLst, db):
        '''Get NCBI IDs from a list of query terms

        Parameters
        ----------
        queryLst: list of str:
            List with query strings the database was searched by.
        db: str
            Name of the database that should be searched in.

        Returns
        -------
        idsDic: dict
            KEY: Query string, VALUE: List of IDs from response.

        '''
        resLst = self.queryNcbiDb(queryLst, db)
        idsDic = self.getNcbiIdFromResponse(resLst, queryLst)
        return idsDic

    def saveNcbiIDs(self, idsDic, idLabel, outputFile):
        '''Creates a pandas dataframe and saves the table as csv

        Parameters
        ----------
        idsDic: dict
            KEY: Query string, VALUE: List of IDs from response.
        idLabel: str
            Label for the IDs retrieved. Is later used as primary key.
        outputFile: str
            Path the .csv file will be saved in.

        Returns
        -------
        queryDF: pandas data frame
            Stores query terms aswell as the matching IDs,
            retrieved from database search.

        '''
        # creates rows for data frame
        queryDFRows = []
        for key, value in idsDic.items():
            for v in value:
                queryDFRows.append([key, v])
        queryDF = pd.DataFrame(queryDFRows, columns=["query", idLabel])
        queryDF.to_csv(outputFile)
        return queryDF
# END CLASS NCBI


class Uniprot:
    def queryUniprotID(self, queryStr, organismID):
        '''
        Querys UniProt Database to get accession number of the gene/protein

        Parameters
        ----------
        queryStr: str
            Query term (gene, protein, ect) to search for in the database.

        Returns
        -------
        accessionNumbers: list of str
            List of query results for the search term.

        '''
        baseURL = 'https://www.uniprot.org/uniprot/'

        orgQuery = '+AND+organism:' + str(organismID)
        payload = {'query': queryStr + orgQuery, 'sort': 'score',
                   'format': 'list'}
        result = requests.get(baseURL, payload)

        if result.ok:
            if result.text.strip():
                accessionNumbers = result.text.strip()
            else:
                accessionNumbers = 'Not found'
        else:
            result.raise_for_status()
            accessionNumbers = False
        return accessionNumbers

    def queryTerms(self, queryLst, organismID, outputFormat='list',
                   sort='score', idLabel='ID_Uniprot'):
        ''' Search Uniprot database based on search terms

        Parameters
        ----------
        queryLst: list of str:
            List with query strings the database was searched by.
        organismID: str
            Limit the search results to this organism.
        outputFormat: str
            Type of format from the server. All choices under,
            https://www.uniprot.org/help/api_queries .
        sort: str
            Determines how the results should be sorted.
        idLabel: str
            Label for the IDs retrieved. Is later used as primary key.

        Returns
        -------
        idDf: pandas data frame
            Contains information about query term and retrieved id.

        '''
        baseURL = 'https://www.uniprot.org/uniprot/'

        # Parameters
        outputFormat = outputFormat
        idsAllLst = []

        queryLstLength = len(queryLst)
        assert queryLstLength != 0

        rows = []
        # one database request for each query
        for i, queryTerm in enumerate(queryLst):
            # Feedback
            print(f'Query {i+1} of {queryLstLength}')

            # request to database
            idsStr = self.queryUniprotID(queryTerm, organismID)
            idsLst = idsStr.split("\n")

            # Create rows for melted data frame
            for _id in idsLst:
                rows.append([queryTerm, _id])

        idDf = pd.DataFrame(rows, columns=["query", idLabel])
        return idDf

    def mapRetrieveUniprot(self, ids2map,
                           source_fmt='ACC+ID',
                           target_fmt='ACC',
                           output_fmt='tab',
                           colNames='id,entry name,organism'):
        '''Calls Uniprot API to map (translate) IDs from or to Uniprot
        database and retrieve entries after mapping.

        Makes a POST request  with a list of IDs to Uniprot API. The API can
        map foreign IDs to Uniprot Accession numbers or Uniprot Accession
        numbers to foreign IDs. Also after mapping, Uniprot searches the
        results, it responses with the results in a desired output format.


        Parameters
        ----------
        ids2map: list of strings
            List of ID strings that should be mapped
        sourceFmt: string
            Database identifier of uniprot, from which the ID is from
            (List of identifiers: https://www.uniprot.org/help/api_idmapping)
        targetFmt: string
            Database identifier of uniprot, to which the ID should mapped
        outputFmt: string
            Desired output format from Uniprot API
            (List of possible formats https://www.uniprot.org/help/api_queries)
        colNames: string
            Optional. Only used when outputFmt is 'tab' or
            'xls'. Comma seperated list of column names to retrieve from entry
            (List of possible columns:
            https://www.uniprot.org/help/uniprotkb_column_names)

        Returns
        -------
        response.text: JSON as str
            Response body of POST request.
        '''

        baseURL = 'https://www.uniprot.org/uploadlists/'
        if hasattr(ids2map, 'pop'):
            ids2map = ' '.join(ids2map)
        assert isinstance(ids2map, str) is True
        payload = {
                'query': ids2map,
                'from': source_fmt,
                'to': target_fmt,
                'format': output_fmt,
                'columns': colNames
                }
        response = requests.post(baseURL, payload)
        if response.ok:
            if response.text.strip():
                return response.text
            else:
                raise Exception("Uniprot found no matching results")
        else:
            response.raise_for_status()

    def getUniprotEntrysWithNCBIIds(self, queryDF, colNames, idLabel):
        '''Get Uniprot information'''
        # Get Uniprot Response
        resBody = self.mapRetrieveUniprot(queryDF[idLabel].tolist(),
                                          'P_GI', 'ACC', 'tab', colNames)

        return resBody

    def matchQueryWithResponse(self, queryDf, responseDf, idLabel):
        ''' Outer join with query and response dataframe

        Parameters
        ----------
        queryDf: pandas data frame
            Stores query terms aswell as the matching IDs,
            retrieved from database search.
        responseDf: pandas data frame
            Stores response data from the server.
        idLabel: string
            Label for the IDs retrieved. Is used as primary key.

        Returns
        -------
        allProtInfoDf: pandas data frame
            Stores query terms and response information.

        '''
        dfIDCol = responseDf[idLabel].str.split(',')
        dfIDCol = dfIDCol.apply(pd.Series, 1).stack()
        dfIDCol.index = dfIDCol.index.droplevel(-1)
        dfIDCol.name = idLabel
        del responseDf[idLabel]
        responseDf = responseDf.join(dfIDCol)
        allProtInfoDf = queryDf.merge(responseDf, on=idLabel, how='outer')
        return allProtInfoDf

    def processUniprotRes(self, resBody, queryDf, outPath, idLabel):
        '''Creates data frame out of Uniprot POST Request

        Parameters
        ----------
        resBody: JSON as str
            Response body from GET() request of uniprot.
        queryDf: pandas data frame
            Stores query terms aswell as the matching IDs,
            retrieved from database search.
        outPath: str
            Path to output file.
        idLabel: string
            Label for the IDs retrieved. Is used as primary key.

        Returns
        -------
        protInfoDf: pandas data frame
            Stores query terms and response information.

        '''
        responseCSV = StringIO(resBody)
        responseDf = pd.read_csv(responseCSV, sep="\t")

        # query names have to be matched with ALL matching IDs
        queryColumnName = responseDf.columns.values.tolist()[-1]
        responseDf.rename(columns={queryColumnName: idLabel}, inplace=True)
        responseDf[idLabel] = responseDf[idLabel].astype(str)
        protInfoDf = self.matchQueryWithResponse(queryDf,
                                                 responseDf, idLabel)
        protInfoDf.to_csv(outPath)

        return protInfoDf

####################
# Program #########
##################

if __name__ == "__main__":
    args = initArguments()

    # Read File
    queryLst, orgaLst = readQueryFile(args.inputFile, args.noheaders)

    if args.website == 'ncbi':
        # Query NCBI
        ncbi = NCBI(queryLst, args.database)
        idRes = ncbi.query(queryLst, args.database)
        queryDF = ncbi.saveNcbiIDs(idRes, 'ID_NCBI', args.outputFile)

    elif args.website == 'ncbi+uniprot':
        # Query NCBI+Uniprot
        ncbi = NCBI(queryLst, args.database)
        idRes = ncbi.query(queryLst, args.database)
        queryDF = ncbi.saveNcbiIDs(idRes, 'ID_NCBI', args.outputFile)

        uniNCBI = Uniprot()
        res = uniNCBI.mapRetrieveUniprot(queryDF['ID_NCBI'].tolist(),
                                         'P_GI', 'ACC', 'tab', args.columns)
        protInfoDf = uniNCBI.processUniprotRes(res, queryDF,
                                               args.outputFile, "ID_NCBI")

    elif args.website == 'uniprot':
        uni = Uniprot()
        # Query Uniprot by foreign database IDs
        if args.inputDataType == 'id':
            if not args.idType:
                raise Exception('Declare idType in arguments')
            res = uni.mapRetrieveUniprot(queryLst,
                                         args.idType,
                                         'ACC',
                                         'tab',
                                         args.columns)
            queryDF = pd.DataFrame({'query': queryLst})
            protInfoDf = uni.processUniprotRes(res, queryDF,
                                               args.outputFile, "query")
        else:
            # Query Uniprot by search terms
            idsDf = uni.queryTerms(queryLst, args.organism)
            idsDf.to_csv(args.outputFile)
