# Protein Finder
This is a Python script for pulling data out of 
https://www.ncbi.nlm.nih.gov/ and https://www.uniprot.org/
using their APIs. It programmatically downloads all information
found for given search terms in the databases. It saves biologists
hours or even days of time.

Usage
========

Basic Functionality
-------------------

Let's assume we have a csv File containing gene loci. The loci
were originally from the NCBI database. Now we want to have more
information about the gene product. We start with the input file,
named 'genes.csv'. It stores the following information:

Gene loci:

| gene_loci |
|-----------|
| Dshi_0051 |
| Dshi_0052 |
| Dshi_0053 |
| Dshi_0054 |
| Dshi_0055 |
| Dshi_0056 |
| Dshi_0057 |
| Dshi_0057 |
| Dshi_0058 |
| Dshi_0059 |
| Dshi_0060 |
| Dshi_0061 |
| CC_2_9    |

We start the command line prompt and navigate to the folder containing
proteinFinder.py. To use the Protein Finder module we need to know what
kind of arguments the script is expecting. We can go look it up in
documentation or we just type in:


    python3 proteinFinder.py -h

The flag -h is short for help. This command shows all arguments the script
is able to process and a short description:


    usage: proteinFinder.py [-h] [--noheaders] [-db DATABASE] [-c COLUMNS]
                        [--organism ORGANISM] [-i {text,id}] [--idType IDTYPE]
                        inputFile outputFile {ncbi,uniprot,ncbi+uniprot}

    positional arguments:
    inputFile             Path to csvfile with query strings
    outputFile            Path to file the results should besaved
    {ncbi,uniprot,ncbi+uniprot}
                            Which website should be queried

    optional arguments:
    -h, --help            show this help message and exit
    --noheaders           When reading the input file it does notskip the first row
    -db DATABASE, --database DATABASE
                            Database which shouldbe queried
    -c COLUMNS, --columns COLUMNS
                            When quiering Uniprot,depicts, which type of
                            information should be downloaded. Terms have to be
                            comma seperated
    --organism ORGANISM   Narrow down the search tospecified organism
    -i {text,id}, --inputDataType {text,id}
                            Type of data stored in input File
    --idType IDTYPE       What database the IDs are from?

For the script working proberly, the positional arguments are required.
The minimum working script, would be:


    python3 proteinFinder.py inputFilePath outputFilePath websiteToQuery

In our case the data is stored in a csv file called 'genes.csv'. And
we want the endresult to be saved in 'proteinInformation.csv'. Since
Uniprot does not recognise our gene loci we first need to query NCBI,
for the ID. And with that ID we query the Uniprot database. luckily the
script is smart and handles this with the simple argument 'ncbi+uniprot'.
So we end up with the following command:


    python3 proteinFinder.py genes.csv proteinInformation.csv ncbi+uniprot

The script informs us that it ignores the first line in the input file,
which contains the headers. If you don't want this behaviour, you need
to pass the argument '--noheaders'. We also get a feedback on the status
of the querys:


    Skipping headers
    Query 1 of 12
    Query 2 of 12
    Query 3 of 12
    Query 4 of 12
    Query 5 of 12
    Query 6 of 12
    Query 7 of 12
    Query 8 of 12
    Query 9 of 12
    Query 10 of 12
    Query 11 of 12
    Query 12 of 12

The information found by the search are summed up in the table. The resulting
table in 'proteinInformation.csv'should look similar to this:

| query     | ID_NCBI   | Entry  | Protein names                              | Gene names     | Protein existence      |
|-----------|-----------|--------|--------------------------------------------|----------------|------------------------|
| Dshi_0051 | 157910367 | A8LJX4 | Uncharacterized protein                    | Dshi_0051      | Predicted              |
| Dshi_0052 | 157910368 | A8LJX5 | Uncharacterized protein                    | Dshi_0052      | Predicted              |
| Dshi_0053 | 157910369 | A8LJX6 | HI0933 family protein                      | Dshi_0053      | Predicted              |
| Dshi_0054 | 157910370 | A8LJX7 | Glutathione S-transferase like protein     | gst2 Dshi_0054 | Predicted              |
| Dshi_0055 | 157910371 | A8LJX8 | DNA polymerase III, delta subunit          | holA Dshi_0055 | Predicted              |
| Dshi_0056 | 157910372 | A8LJX9 | Uncharacterized protein                    | Dshi_0056      | Predicted              |
| Dshi_0057 | 189082998 | A8LJY0 | Leucine--tRNA ligase                       | leuS Dshi_0057 | Inferred from homology |
| Dshi_0057 | 157910373 | A8LJY0 | Leucine--tRNA ligase                       | leuS Dshi_0057 | Inferred from homology |
| Dshi_0058 | 157910374 | A8LJY1 | Outer-membrane lipoprotein carrier protein | lolA Dshi_0058 | Inferred from homology |
| Dshi_0059 | 157910375 | A8LJY2 | DNA translocase                            | ftsK Dshi_0059 | Inferred from homology |
| Dshi_0060 | 157910376 | A8LJY3 | Aminotransferase class I and II            | Dshi_0060      | Predicted              |
| Dshi_0061 | 157910377 | A8LJY4 | Amidase                                    | Dshi_0061      | Inferred from homology |
| CC_2_9    | Not Found |        |                                            |                |                        |

The table stores the original query, the IDs found in NCBI and the Uniport
entry. Overall the search was successful. However there are 2 interesting
cases. First, when the script does not find some entrys, it will fill the row
with a 'Not Found' tag. Second, Dshi_0057 seems to appear twice. This is by
design. When multiple IDs or entries are found for a query, each ID or entry,
will be represented in a unique row. The reason is, there is no way for the
programmer to safely determine what entry is relevant. Therefore every table,
has to be inspected for such duplicates and be eliminated by hand.

Searching NCBI
--------------

To query NCBI you need to specify which database should be queried. A full list
of all names can be found [here](https://www.ncbi.nlm.nih.gov/books/NBK25497/table/chapter2.T._entrez_unique_identifiers_ui/?report=objectonly).
Right now only text search is available for NCBI.


    python3 proteinFinder.py genes.csv proteinInformation.csv ncbi -db protein


Searching Uniprot
-----------------

Uniprot can be searched in two ways.

### Query with search terms

    python3 proteinFinder.py genes.csv proteinInformation.csv uniprot

First it can be searched by search terms. This takes a long time since
every term needs to make its own request to the database.

### Query with IDs

    python3 proteinFinder.py genes.csv proteinInformation.csv uniprot --inputDataType id

The second way is to search by ID. To search with IDs the parameter
--inputDataType needs to be set to 'id'.

The IDs can be from variouse
databases. Uniprot is able to map (translate) a given ID to its own
accession number. For this the database has to specified from which
the data come from. The database can be set with the argument --idType.
A list of all available databases can be found
[here](https://www.uniprot.org/help/api_idmapping).

----------------

More detailed information can be found in the documentation.
