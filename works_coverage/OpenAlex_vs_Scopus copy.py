#!/usr/bin/env python3
"""
Script to compare OpenAlex and Scopus coverage for authors from IRIS database.
For each author, it retrieves their works from IRIS, OpenAlex, and Scopus,
then compares the coverage to identify missing works on each platform.
"""

PRINT_NOT_MATCHED_WORKS = False  # If True, print titles of works not matched
SAVE_RESULTS_TO_FILE = True  # If True, save results to JSON file
EXTRACT_STATS_ONLY = False  # If True, load results from file and extract statistics without processing
RESULTS_FILE_PATH = None  # Path to results file (if None, will look for most recent oa_vs_scopus_results_*.txt)

import os
import sys
import time
import requests
import re
import math
from datetime import datetime
from collections import defaultdict
from collections import Counter

# Add the project root directory to Python path to enable imports from utilities
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utilities.db_utils import test_connection, execute_query_with_connection
from utilities.file_utils import write_json_to_file, read_json_from_file
from utilities.sim_lib import similarity_titles, author_similarity
from works_coverage.coverage_stats_utils import extract_statistics
import glob

# ROR identifier for Politecnico di Torino
ROR_POLITO = 'https://ror.org/00bgk9508'

# Check if we should only extract statistics from file
if EXTRACT_STATS_ONLY:
    # Find the results file to load
    if RESULTS_FILE_PATH and os.path.exists(RESULTS_FILE_PATH):
        results_file = RESULTS_FILE_PATH
    elif RESULTS_FILE_PATH:
        print(f"❌ Error: Specified results file not found: {RESULTS_FILE_PATH}")
        exit(1)
    else:
        # Look for the most recent results file
        results_files = glob.glob("oa_vs_scopus_results_*.txt")
        if not results_files:
            print("❌ Error: No results files found (oa_vs_scopus_results_*.txt)")
            print("   Please specify RESULTS_FILE_PATH or run the script with EXTRACT_STATS_ONLY = False")
            exit(1)
        # Sort by modification time and get the most recent
        results_file = max(results_files, key=os.path.getmtime)
    
    print(f"📂 Loading results from: {results_file}")
    all_results = read_json_from_file(results_file, cursor=None, conn=None)
    print(f"✅ Loaded {len(all_results)} author results")
    
    # Extract and display statistics
    extract_statistics(all_results)
    
    exit(0)

# Test database connection and get connection/cursor objects
conn, cursor = test_connection()

# Query to retrieve authors from IRIS database
# Starting from authors in iris_ods_l1_rm_person, find the employee ID (matricola) by matching
# tax code (codice fiscale) with dwpauper_vista_personale_attivo and select all useful data
# (first name, last name, Scopus ID, ORCID, etc.)
distinct_author_query = """
select iolrp.FIRST_NAME as NOME_AUTORE, iolrp.LAST_NAME as COGNOME_AUTORE, iolrp.ORCID as ORCID, 
       iolrp.SCOPUS_ID as SCOPUS_ID, iolrp.CODICE_FISCALE as COD_FIS, dvpa.MATRICOLA as matricola, 
       dvpa.POSIZIONE as POSIZIONE, YEAR(iolrp.BIRTH_DATE) as BIRTH_DATE
from iris_ods_l1_rm_person iolrp 
left join dwpauper_vista_personale_attivo dvpa on iolrp.CODICE_FISCALE = dvpa.COD_FISCALE 
where dvpa.MATRICOLA is not null and iolrp.SCOPUS_ID is not null and YEAR(iolrp.BIRTH_DATE) > 1950
"""

# Execute query to retrieve authors from IRIS database
results = execute_query_with_connection(cursor, distinct_author_query, conn=conn)

authors_output_file = "all_anagrafe.txt"

# Write query results to JSON file for processing
write_json_to_file(results, authors_output_file, cursor=cursor, conn=conn)

# Read the JSON file containing authors data
authors = read_json_from_file(authors_output_file, cursor=cursor, conn=conn) 

# List to store results for all authors
all_results = []

# List to store works missing exclusively in OpenAlex (with full details)
works_missing_only_oa_details = []

# Process all authors
main_loop_count = 0
print(f"\n")
for author_item in authors:

    main_loop_count += 1
    # Skip authors before a certain index (can be modified to process specific ranges)
    if main_loop_count > 0:
        
        # Extract author information from IRIS
        author_employee_id = author_item.get("matricola")  # Employee ID (matricola)
        author_first_name = author_item.get("NOME_AUTORE")  # First name
        author_last_name = author_item.get("COGNOME_AUTORE")  # Last name
        author_orcid = author_item.get("ORCID")  # ORCID identifier
        author_tax_code = author_item.get("COD_FIS")  # Tax code (codice fiscale)
        author_role = author_item.get("POSIZIONE")  # Position/role
        author_birth_year = author_item.get("BIRTH_DATE")  # Birth year
        author_scopus_id = author_item.get("SCOPUS_ID")  # Scopus Author ID (e.g., 57213302418)

        # Query to retrieve all works of the author from IRIS
        iris_works_query = f"""select prpb.TITOLO as titolo, prpb.cd_doi as doi, prpb.ANNO as anno, 
                                   prpb.HANDLE as HANDLE, prpb.NOME_EDITORE as nome_editore, 
                                   prpb.STRINGA_AUTORI as stringa_autori
            from pub_ri_prodotti_autori as prpa 
            join pub_ri_prodotti_base as prpb 
            on prpa.ID_PRODOTTO = prpb.ID_PRODOTTO 
            where prpa.matricola = {author_employee_id}"""

        iris_works = execute_query_with_connection(cursor, iris_works_query, conn=conn)
        iris_works_with_doi = [work for work in iris_works if work.get("doi")]

        print(f"*** 👤 AUTHOR {main_loop_count}/{len(authors)} ***")
        print(f"Employee ID: {author_employee_id}")
        print(f"First Name: {author_first_name}")
        print(f"Last Name: {author_last_name}")
        print(f"Tax Code: {author_tax_code}")
        print(f"Birth Year: {author_birth_year}")
        print(f"Role: {author_role}")       
        print(f"Number of works: {len(iris_works)}")
        print(f"Number of works with DOI: {len(iris_works_with_doi)}")
        
        # Validate and extract Scopus Author ID
        if not author_scopus_id:
            print(f"🔴 Author without Scopus AuthorID")
        else:
            match = re.search(r'(\d{10,11})', author_scopus_id)
            if match:
                author_scopus_id = match.group(1)
                print(f"Scopus AuthorID: {author_scopus_id}")
            else:
                print(f"🔴 Invalid Scopus AuthorID: {author_scopus_id}")
                author_scopus_id = None
        

        ### If author has ORCID, proceed with OpenAlex search
        oa_works_count = 0                        
        oa_matched_count = 0
        oa_missing_iris_works = []
        openalex_author_id_final = None
        
        if author_orcid is not None:
            print(f"ORCID: {author_orcid}")
            print(f"\n🅾️🅰️🔎 Searching for profile and works on OpenAlex using Name, Last Name and ORCID...")

            # Search for author on OpenAlex using ORCID
            orcid_search_url = f"https://api.openalex.org/authors?per-page=10&search={author_first_name}%20{author_last_name}&filter=orcid:https://orcid.org/{author_orcid}"
            response = requests.get(orcid_search_url)

            if response.status_code == 200:
                response.raise_for_status()
                oa_authors_results = response.json()
                oa_search_count = oa_authors_results['meta']['count']
                print(f"✅ Found {oa_search_count} OpenAlex profile(s)!")

                if oa_search_count >= 1:
                    oa_works = []
                    first_author_found = True
                    
                    # Process each OpenAlex profile found
                    for oa_author_profile in oa_authors_results['results']:
                        openalex_author_id = oa_author_profile['id']
                        openalex_display_name = oa_author_profile['display_name']
                        print(f"✅ Found OpenAlex profile with ID = {openalex_author_id} and display_name = {openalex_display_name}!")
                        
                        # Extract OpenAlex ID (remove URL prefix)
                        openalex_author_id_extracted = openalex_author_id.split("https://openalex.org/")[1]
                        if first_author_found:
                            first_author_found = False
                            openalex_author_id_final = openalex_author_id_extracted
                        
                        # Search for works by this author on OpenAlex
                        per_page_number = 50
                        page_number = 1
                        works_by_id_search_url = f"https://api.openalex.org/works?per-page={per_page_number}&page={page_number}&filter=authorships.author.id:{openalex_author_id_extracted}"
                        response = requests.get(works_by_id_search_url)

                        # Retrieve OpenAlex works, page by page
                        if response.status_code == 200:
                            response.raise_for_status()
                            page_oa_works = response.json()
                            oa_works_count = page_oa_works['meta']['count']

                            print(f"✅ Found {oa_works_count} works on OpenAlex!")
                            
                            # Save works from the first page
                            for work in page_oa_works['results']:
                                oa_works.append(work)

                            # Retrieve and save works from remaining pages
                            oa_pages_count = math.ceil(oa_works_count / per_page_number)
                            for idx in range(2, oa_pages_count + 1):
                                page_number += 1
                                works_by_id_search_url = f"https://api.openalex.org/works?per-page={per_page_number}&page={page_number}&filter=authorships.author.id:{openalex_author_id_extracted}"
                                response = requests.get(works_by_id_search_url)
                                if response.status_code == 200:
                                    response.raise_for_status()
                                    page_oa_works = response.json()
                                    for work in page_oa_works['results']:
                                        oa_works.append(work)
                        else:
                            print("❌ No works found on OpenAlex")     

                    print(f"\n🔎 Comparing OpenAlex works with IRIS works...")
                    # Compare IRIS works with OpenAlex works
                    oa_matched_count = 0
                    oa_missing_iris_works = []  # Store full work objects, not just titles
                    
                    for iris_work in iris_works:
                        found_similarity = False
                        
                        # First, try to match with works already retrieved from author's profile
                        for oa_work in oa_works:

                            # Match by DOI
                            if oa_work.get("doi") is not None and iris_work.get("doi") is not None:
                                oa_doi = oa_work['doi'].split("https://doi.org/")[1].lower()
                                iris_doi = iris_work.get("doi").lower()
                                if oa_doi == iris_doi or similarity_titles(oa_doi, iris_doi) > 0.5:
                                    oa_matched_count += 1
                                    found_similarity = True
                                    break

                            # Match by title similarity
                            if oa_work.get("title") is not None and iris_work.get("titolo") is not None:
                                similarity_score = similarity_titles(iris_work.get("titolo"), oa_work.get("title"))
                                if similarity_score > 0.5:
                                    oa_matched_count += 1
                                    found_similarity = True
                                    break

                        # If not found in author's profile, try searching by DOI
                        if found_similarity == False:
                            if iris_work.get("doi") is not None:
                                work_by_doi_url = f"https://api.openalex.org/works?filter=doi:{iris_work.get('doi').lower()}"
                                response = requests.get(work_by_doi_url)
                                if response.status_code == 200:
                                    response.raise_for_status()
                                    oa_work_by_doi = response.json()
                                    if oa_work_by_doi['meta']['count'] == 1:
                                        # Check if author is in the work's authorships
                                        for oa_work_author in oa_work_by_doi['results'][0]['authorships']:
                                            author_display_name = oa_work_author['author']['display_name']
                                            if author_display_name is not None and author_similarity(
                                                f"{author_first_name} {author_last_name}", 
                                                author_display_name
                                            ) > 0.5:
                                                oa_matched_count += 1
                                                found_similarity = True
                                                break

                            # If still not found, try searching by title
                            if iris_work.get("titolo") is not None and found_similarity is False:
                                work_by_title_url = f"https://api.openalex.org/works?search={iris_work.get('titolo')}"
                                response = requests.get(work_by_title_url)
                                if response.status_code == 200:
                                    response.raise_for_status()
                                    oa_works_by_title = response.json()
                                    if oa_works_by_title['meta']['count'] > 0:
                                        for oa_work_by_title in oa_works_by_title['results']:
                                            for oa_work_author in oa_work_by_title['authorships']:
                                                author_display_name = oa_work_author['author']['display_name']
                                                if (author_display_name is not None and 
                                                    author_similarity(f"{author_first_name} {author_last_name}", 
                                                                    author_display_name) > 0.5 and 
                                                    found_similarity is False):
                                                    oa_matched_count += 1    
                                                    found_similarity = True
                                                    break

                        # If still not found, add full work object to missing works list
                        if found_similarity == False:
                            oa_missing_iris_works.append(iris_work)

                    print(f"👌 Works match: {oa_matched_count}/{len(iris_works)} (number of works matching on OpenAlex / total number of author's works)")
                    if PRINT_NOT_MATCHED_WORKS:
                        if (oa_matched_count < len(iris_works)):
                            print(f"❌ Missing Works (title):")
                            print(*[missing_work.get("titolo") for missing_work in oa_missing_iris_works], sep='\n')
                else:
                    print("❌ No results found on OpenAlex")
            else:
                print("❌ No results found on OpenAlex")
                
        else:
            print(f"🔴 Author without ORCID")

        ### If author has Scopus ID, proceed with Scopus search
        scopus_works_count = 0                      
        scopus_matched_count = 0
        scopus_missing_iris_works = []
        scopus_work_mapping = {}  # Map IRIS works to their matched Scopus works (initialize outside if block)
        
        if author_scopus_id is not None:
            print(f"\n\n🔎 Searching for profile and works on Scopus...")

            # Search for author in Scopus table using AuthorID
            scopus_author_data_query = f"""select nome, cognome
                from pub_scopus_articles_author 
                where AUTHORID = {author_scopus_id}"""
            scopus_author_data = execute_query_with_connection(cursor, scopus_author_data_query, conn=conn)
            
            if scopus_author_data:
                scopus_author_data = scopus_author_data[0] 
                print(f"✅ Found Scopus profile with ID = {author_scopus_id} and name = {scopus_author_data.get('nome')} {scopus_author_data.get('cognome')}!")
                
                # Query to retrieve all works of the author from Scopus
                scopus_works_query = f"""select psa.TITLE as title, psa.DOI as doi
                    from pub_scopus_articles_author psaa
                    join pub_scopus_articles psa on psaa.PUBID = psa.PUBID
                    where psaa.AUTHORID = {author_scopus_id}"""
                scopus_works = execute_query_with_connection(cursor, scopus_works_query, conn=conn)
                scopus_works_count = len(scopus_works)
                
                print(f"✅ Found {scopus_works_count} works on Scopus!")

                print(f"\n🔎 Comparing Scopus works with IRIS works...")
                # Compare IRIS works with Scopus works
                scopus_matched_count = 0
                scopus_missing_iris_works = []  # Store titles of works not found in Scopus
                scopus_work_mapping = {}  # Map IRIS works to their matched Scopus works (reinitialize for this author)
                
                for iris_work in iris_works:
                    found_similarity = False
                    matched_scopus_work = None

                    for scopus_work in scopus_works:
                        # Match by DOI
                        if scopus_work.get("doi") is not None and iris_work.get("doi") is not None:
                            if scopus_work.get("doi").lower() == iris_work.get("doi").lower():
                                scopus_matched_count += 1
                                found_similarity = True
                                matched_scopus_work = scopus_work
                                break

                        # Match by title similarity
                        if scopus_work.get("title") is not None and found_similarity == False:
                            similarity_score = similarity_titles(iris_work.get("titolo"), scopus_work.get("title"))
                            if similarity_score > 0.5:
                                scopus_matched_count += 1
                                found_similarity = True
                                matched_scopus_work = scopus_work
                                break

                    if found_similarity == False:
                        scopus_missing_iris_works.append(iris_work.get("titolo"))
                    else:
                        # Store mapping of IRIS work to matched Scopus work
                        scopus_work_mapping[iris_work.get("titolo")] = matched_scopus_work

                print(f"👌 Works match: {scopus_matched_count}/{len(iris_works)} (number of works matching on Scopus / total number of author's works)")
                if PRINT_NOT_MATCHED_WORKS:
                    if (scopus_matched_count < len(iris_works)):
                        print(f"❌ Missing Works (title):")
                        print(*[missing_work for missing_work in scopus_missing_iris_works], sep='\n')
            else:
                print(f"❌ No results found on Scopus")
        
        # Calculate works missing only on OpenAlex (present in Scopus but not in OpenAlex)
        # Only calculate if we have both OpenAlex and Scopus data
        works_missing_only_on_oa = 0
        if author_orcid is not None and author_scopus_id is not None and len(oa_missing_iris_works) > 0:
            # Compare by title to find works missing only in OpenAlex
            oa_missing_titles = {work.get("titolo") for work in oa_missing_iris_works}
            scopus_missing_titles = set(scopus_missing_iris_works)
            works_missing_only_on_oa_titles = oa_missing_titles - scopus_missing_titles
            
            works_missing_only_on_oa = len(works_missing_only_on_oa_titles)
            print(f"❌ {works_missing_only_on_oa} works missing only on OpenAlex (title):")
            print(*[title for title in works_missing_only_on_oa_titles], sep='\n')
            
            # Collect detailed information for works missing exclusively in OpenAlex
            for iris_work in oa_missing_iris_works:
                iris_title = iris_work.get("titolo")
                if iris_title in works_missing_only_on_oa_titles:
                    # Find the corresponding Scopus work if it exists
                    matched_scopus_work = scopus_work_mapping.get(iris_title, None)
                    
                    # Create detailed record
                    work_detail = {
                        # Author information
                        "author_matricola": author_employee_id,
                        "author_first_name": author_first_name,
                        "author_last_name": author_last_name,
                        "author_orcid": author_orcid,
                        "author_scopus_id": author_scopus_id,
                        "author_tax_code": author_tax_code,
                        "author_role": author_role,
                        "author_birth_year": author_birth_year,
                        # IRIS work information
                        "iris_title": iris_work.get("titolo"),
                        "iris_doi": iris_work.get("doi"),
                        "iris_year": iris_work.get("anno"),
                        "iris_handle": iris_work.get("HANDLE"),
                        "iris_publisher": iris_work.get("nome_editore"),
                        "iris_authors": iris_work.get("stringa_autori"),
                        # Scopus work information (if matched)
                        "scopus_title": matched_scopus_work.get("title") if matched_scopus_work else None,
                        "scopus_doi": matched_scopus_work.get("doi") if matched_scopus_work else None,
                    }
                    works_missing_only_oa_details.append(work_detail)
        else:
            print(f"❌ Cannot determine works missing only on OpenAlex (missing ORCID or Scopus ID)")
        
        # Store results for this author
        if SAVE_RESULTS_TO_FILE:
            author_result = {
                "matricola": author_employee_id,
                "nome_autore": author_first_name,
                "cognome_autore": author_last_name,
                "cod_fis": author_tax_code,
                "orcid": author_orcid,
                "scopus_id": author_scopus_id,
                "open_alex_id": openalex_author_id_final if openalex_author_id_final else None,
                "numero_lavori": len(iris_works),
                "numero_lavori_doi": len(iris_works_with_doi),
                "oa_numero_lavori": oa_works_count,
                "oa_match": oa_matched_count,
                "scopus_numero_lavori": scopus_works_count,
                "scopus_match": scopus_matched_count,
                "lavori_mancanti_solo_su_oa": works_missing_only_on_oa,
                "dt_ins": datetime.today().strftime('%Y-%m-%d')
            }
            all_results.append(author_result)

        # Final spacing
        print(f"\n\n\n")

# Close database connection
cursor.close()
conn.close()

# Save results to JSON file
if SAVE_RESULTS_TO_FILE and all_results:
    results_filename = f"oa_vs_scopus_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    write_json_to_file(all_results, results_filename, cursor=None, conn=None)
    print(f"\n📁 Results saved to: {results_filename}")
    
    # Extract and display statistics
    extract_statistics(all_results)
else:
    print("\n⚠️  No results to save.")

# Save works missing exclusively in OpenAlex to JSON file
if works_missing_only_oa_details:
    json_filename = f"works_missing_only_openalex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    write_json_to_file(works_missing_only_oa_details, json_filename, cursor=None, conn=None)
    print(f"\n📊 JSON file with {len(works_missing_only_oa_details)} works missing exclusively in OpenAlex saved to: {json_filename}")
    print(f"   The file is in JSON format and can be easily opened in any text editor or browser.")
else:
    print("\n⚠️  No works missing exclusively in OpenAlex to save.")
