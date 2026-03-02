"""
A search engine that will search an inverted index 
"""
def search():
    print("Search engine running...")
    
    query = input("Enter search term: ")

    import sys
    import os
    import re
    import math
    import sqlite3
    import time
    from collections import Counter

    # Use simple dictionary data structures in Python to maintain lists with hash keys
    docs = {}
    resultslist = {}

    # Regular expression to extract words, extract ID from path, check for hexa value
    chars = re.compile(r'\W+')
    pattid = re.compile(r'(\d{3})/(\d{3})/(\d{3})')

    #
    # Docs class: Used to store information about each unit document. In this is the Term object which stores each
    # unique instance of termid or a docid.
    #
    class Docs:
        def __init__(self):
            self.terms = {}

    #
    # Term class: used to store information or each unique termid
    #
    class Term:
        def __init__(self):
            self.docfreq = 0
            self.termfreq = 0
            self.idf = 0.0
            self.tfidf = 0.0

    # split on any chars
    def splitchars(line):
        return chars.split(line)

    # this small routine is used to accumulate query idf values
    def elenQ(elen, term):
        return(float(math.pow(term.idf, 2)) + float(elen))

    # this small routine is used to accumulate document tfidf values
    def elenD(elen, term):
        return(float(math.pow(term.tfidf, 2)) + float(elen))

    # Function to initialize database connection
    def initialize_database(db_path):
        try:
            con = sqlite3.connect(db_path)
            con.isolation_level = None
            cur = con.cursor()
            return con, cur
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            sys.exit(1)

    # Function to get the total number of documents in the collection
    def get_document_count(cur):
        try:
            q = "select count(*) from documentdictionary"
            cur.execute(q)
            row = cur.fetchone()
            return row[0]
        except sqlite3.Error as e:
            print(f"Error fetching document count: {e}")
            sys.exit(1)

    # Helper function that checks whether a given term exists in the termdictionary table of the database.
    def term_in_database(term, cur):
        """
        Checks if a given term exists in the termdictionary table of the database.

        Args:
            term (str): The term to check.
            cur (sqlite3.Cursor): The database cursor object.

        Returns:
            bool: True if the term exists, False otherwise.
        """
        try:
            # SQL query to count occurrences of the term in the database (case-insensitive)
            q = "SELECT COUNT(*) FROM termdictionary WHERE LOWER(term) = ?"
            cur.execute(q, (term.lower(),))  # Use the term in lowercase for consistent matching
            row = cur.fetchone()
            return row[0] > 0  # If count > 0, the term exists in the database
        except sqlite3.Error as e:
            print(f"Database error while checking term '{term}': {e}")
            return False


    # Function to process the query and create a query vector
    def process_query(query, cur):
        l = splitchars(query)
        query_terms = Counter(l) #count the occurrences of each element in a list, l
        query_vector = {}
        for term, freq in query_terms.items():
            lower_term = term.lower().strip()
            query_vector[lower_term] = freq

        # Validate terms against the database
        query_vector = {term: freq for term, freq in query_vector.items() if term_in_database(term, cur)}

        return query_vector

    # Function to fetch document data for the query terms
    def fetch_document_data(query_vector, cur, docs, documents):
        for term in query_vector.keys():
            try:
                q = "SELECT COUNT(*) FROM termdictionary WHERE LOWER(term) = ?"
                cur.execute(q, (term,))
                row = cur.fetchone()

                if row[0] > 0:
                    q = """
                    SELECT DISTINCT docid, tfidf, docfreq, termfreq, posting.termid 
                    FROM termdictionary, posting 
                    WHERE posting.termid = termdictionary.termid AND term = ? 
                    ORDER BY docid, posting.termid
                    """
                    cur.execute(q, (term,))
                    for row in cur:
                        i_termid = row[4]
                        i_docid = row[0]

                        if i_docid not in docs:
                            docs[i_docid] = Docs()

                        if i_termid not in docs[i_docid].terms:
                            docs[i_docid].terms[i_termid] = Term()
                            docs[i_docid].terms[i_termid].docfreq = row[2]
                            docs[i_docid].terms[i_termid].termfreq = row[3]
                            docs[i_docid].terms[i_termid].idf = math.log(documents / (row[2] + 1))
                            docs[i_docid].terms[i_termid].tfidf = row[1]
            except sqlite3.Error as e:
                print(f"Error fetching document data: {e}")
                sys.exit(1)

    # Function call to compute cosine similarity between the query and each document
    def compute_similarities(query_vector, docs, documents):
        resultslist = {}
        #
        #Computing the Euclidean length (or magnitude) of the query vector
        #
        query_length = 0
        for termid in query_vector.keys():
            for docid in docs.keys():
                if termid in docs[docid].terms:
                    term = Term() # Setting the idf value for the term
                    term.idf = math.log(documents / (docs[docid].terms[termid].docfreq + 1))
                    query_length = elenQ(query_length, term)
        query_length = math.sqrt(query_length)

        for docid in docs.keys():
            doc_vector = docs[docid].terms
            dot_product = 0
            for term in query_vector.keys():
                if term in doc_vector:
                    dot_product += query_vector[term] * doc_vector[term].tfidf

            doc_length = 0
            for termid in doc_vector:
                doc_length += elenD(0, doc_vector[termid])
            doc_length = math.sqrt(doc_length)

            if query_length > 0 and doc_length > 0:
                cosine_similarity = dot_product / (query_length * doc_length)

        return resultslist

    if __name__ == '__main__':
        # Generalized database path
        db_path = "D:/Unit 2 Prog Assign/cacm/inverted_index.db" # Path to be edited
        con, cur = initialize_database(db_path)

        try:
            # Prompt user for search terms
            query = input('Enter your search terms, each separated by a space: ')

            # Record start time
            t_start = time.time()

            # Get the total number of documents
            documents = get_document_count(cur)

            # Process query
            query_vector = process_query(query, cur)

            # Fetch document data
            fetch_document_data(query_vector, cur, docs)

            # Remove documents not containing all query terms
            for docid in list(docs.keys()):
                if not all(term in docs[docid].terms for term in query_vector.keys()):     # Check if all query terms are present in the document's terms
                    del docs[docid]

            # Compute similarities
            resultslist = compute_similarities(query_vector, docs, documents)

            # Sort and print the top 20 results
            keylist = sorted(resultslist.keys(), reverse=True)
            print(f"The Top {min(len(keylist), 20)} Relevant Documents are:")
            for i, key in enumerate(keylist[:20]):
                cur.execute("SELECT DocumentName FROM documentdictionary WHERE docid = ?", (resultslist[key],))
                row = cur.fetchone()
                print(f"Document: {row[0]} has Cosine Similarity of {key:.6f}")

            # Print elapsed time
            t_end = time.time()
            print(f"Search completed in {t_end - t_start:.2f} seconds.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            con.close()
    print("Search complete.")
