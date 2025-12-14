#!/usr/bin/env python3
"""
Script to match works from IRIS database with OpenAlex works
by searching for publications first using doi, then eventually using title, institution (Politecnico di Torino),
and publication year.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# Add the project root directory to Python path to enable imports from utilities
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utilities.db_utils import test_connection, execute_query_with_connection
from utilities.file_utils import write_json_to_file, read_json_from_file, parse_author_pairs
from utilities.sim_lib import similarity_authors
from utilities.sim_lib import similarity_titles
from utilities.sim_lib import similarity_years
from works_matching.stats_utils import calculate_statistics, print_statistics

# Flag to enable/disable saving statistics to JSON file
PRINT_STATS = True

# ROR identifier for Politecnico di Torino
ROR_POLITO = 'https://ror.org/00bgk9508'

# Test database connection and get connection/cursor objects
conn, cursor = test_connection()

# Query to get all works from IRIS database
# Returns: HANDLE, TITOLO (title), ANNO (year), STRINGA_AUTORI (authors string),
# DS_PROPRIETARIO (owner description), MATRICOLA_PROPRIETARIO (owner ID), CD_SCOPUS (Scopus ID), CD_DOI (DOI)
select_works_IRIS_query = """
select distinct HANDLE, TITOLO, ANNO, STRINGA_AUTORI, DS_PROPRIETARIO, MATRICOLA_PROPRIETARIO, CD_SCOPUS, CD_DOI
from pub_ri_prodotti_base
where anno > 2003 and anno < 2005 and cd_doi is null
limit 200
"""

# Execute query to retrieve works from IRIS database
results = execute_query_with_connection(cursor, select_works_IRIS_query, conn=conn)

# Output file to store query results
output_file = "names_from_IRIS.txt"

# Write query results to JSON file for processing
write_json_to_file(results, output_file, cursor=cursor, conn=conn)

# Read the JSON file containing works data
data = read_json_from_file(output_file, cursor=cursor, conn=conn) 

# Counter for processed works
count = 0

# List to store statistics for each work (if PRINT_STATS is True)
stats_data = []

# Process each work from the IRIS database
for item in data:
        count += 1

        # Process all works (condition can be modified to filter specific ranges)
        if count > 0:
                # Extract work metadata from IRIS database record
                handle = item.get("HANDLE")
                titolo = item.get("TITOLO")  # Title
                anno = item.get("ANNO")  # Publication year
                stringa_autori = item.get("STRINGA_AUTORI")  # Authors string
                ds_proprietario = item.get("DS_PROPRIETARIO")  # Owner description
                matricola_proprietario = item.get("MATRICOLA_PROPRIETARIO")  # Owner ID
                cd_scopus = item.get("CD_SCOPUS")  # Scopus ID
                doi = item.get("CD_DOI")  # DOI
                authors = parse_author_pairs(stringa_autori)

                print(f"Handle: {handle}")
                print(f"Title: {titolo}")
                print(f"Year: {anno}")
                print(f"DOI: {doi}")
                print(f"Authors: {authors}")

                # Initialize statistics entry for this work (if PRINT_STATS is enabled)
                if PRINT_STATS:
                        work_stats = {
                                "handle": handle,
                                "title": titolo,
                                "year": anno,
                                "authors": authors,
                                "doi": doi,
                                "scopus_id": cd_scopus,
                                "matched": False,
                                "match_found": False,
                                "similarity_score": None,
                                "openalex_id": None,
                                "openalex_title": None,
                                "openalex_authors": None,
                                "openalex_year": None,
                                "search_method": None
                        }
        
                try:
                        work_results = []
                        search_successful = False
                        
                        # If DOI is present, search OpenAlex by DOI first
                        if doi:
                                print(f"🔍 [{count}/{len(data)}] Searching by DOI...")
                                
                                # Search OpenAlex using DOI filter
                                url = f"https://api.openalex.org/works?filter=doi:{doi}"
                                response = requests.get(url)
                                
                                if response.status_code == 200 and response.json().get("meta", {}).get("count", 0) >= 1:
                                        work_results = response.json().get('results', [])
                                        search_successful = True
                                        print(f"✅ Found {len(work_results)} work(s) by DOI")
                                        if PRINT_STATS:
                                                work_stats["search_method"] = "DOI"
                                else:
                                        print(f"⚠️  No match found by DOI, falling back to title/institution/year search")
                        
                        # If no DOI or DOI search failed, search by title, institution, and year
                        if not search_successful:
                                print(f"🔍 [{count}/{len(data)}] Searching by title/institution/year...")

                                # First attempt: Search OpenAlex using title.search filter
                                # Filters by: title search, Politecnico di Torino institution, publication year
                                url = f"https://api.openalex.org/works?filter=title.search:{titolo},institutions.ror:{ROR_POLITO},publication_year:{anno}"
                                response = requests.get(url) 

                                # If first attempt fails or returns no results, try general search
                                if response.status_code != 200 or response.json().get("meta", {}).get("count", 0) < 1:
                                        
                                        # Second attempt: Use general search instead of title.search filter
                                        url = f"https://api.openalex.org/works?search={titolo}&filter=institutions.ror:{ROR_POLITO},publication_year:{anno}"
                                        response = requests.get(url) 
                                        
                                        # If second attempt also fails, try general search without filters
                                        if response.status_code != 200 or response.json().get("meta", {}).get("count", 0) < 1:
                                                
                                                # Third attempt: General search without any filters
                                                print(f"🔍 [{count}/{len(data)}] Searching by title only (no filters)...")
                                                url = f"https://api.openalex.org/works?search={titolo}"
                                                response = requests.get(url)
                                                
                                                # If third attempt also fails, log error and skip to next work
                                                if response.status_code != 200 or response.json().get("meta", {}).get("count", 0) < 1:
                                                        if response.status_code != 200:
                                                                print(f"❌ API Error")
                                                elif response.json().get("meta", {}).get("count", 0) < 1:
                                                        print(f"⚠️  No match found")
                                                        print("─" * 80)
                                                        print()
                                                        # Update statistics for no match (if PRINT_STATS is enabled)
                                                        if PRINT_STATS:
                                                                work_stats["matched"] = False
                                                                work_stats["match_found"] = False
                                                                work_stats["search_method"] = "title_only"
                                                                stats_data.append(work_stats)
                                                        continue
                                                else:
                                                        work_results = response.json().get('results', [])
                                                        print(f"✅ Found {len(work_results)} work(s) by title only")
                                                        if PRINT_STATS:
                                                                work_stats["search_method"] = "title_only"
                                        else:
                                                # Extract work results from OpenAlex API response (second attempt succeeded)
                                                work_results = response.json().get('results', [])
                                                print(f"✅ Found {len(work_results)} work(s) by title/institution/year")
                                                if PRINT_STATS:
                                                        work_stats["search_method"] = "title_institution_year_general"
                                else:
                                        # Extract work results from OpenAlex API response (first attempt succeeded)
                                        work_results = response.json().get('results', [])
                                        print(f"✅ Found {len(work_results)} work(s) by title/institution/year")
                                        if PRINT_STATS:
                                                work_stats["search_method"] = "title_institution_year_filter"
                        
                        # Process each matched work from OpenAlex
                        if len(work_results) == 0:
                                # No results found (shouldn't happen due to checks above, but handle just in case)
                                if PRINT_STATS:
                                        work_stats["matched"] = False
                                        work_stats["match_found"] = False
                                        stats_data.append(work_stats)
                                continue
                        elif len(work_results) > 1:
                                print(f"📚 Multiple works found ({len(work_results)}) - Evaluating similarity...")
                                results_count = 0
                                best_score = -1
                                best_OA_ID = None
                                best_OA_display_name = None
                                best_OA_authors = None
                                best_OA_year = None
                                best_OA_cited_by_count = None
                                best_OA_created_date = None
                                
                                for work in work_results:
                                        results_count += 1
                                        print(f"\n   📄 Work #{results_count}/{len(work_results)}:")
                                        print(f"      Title: {work.get('display_name', 'N/A')}")
                                        print(f"      ID: {work.get('id', 'N/A')}")
                                        print(f"      Type: {work.get('type', 'N/A')}")
                                        authors_OA = [a.get("author", {}).get("display_name", "N/A") for a in work.get("authorships", [])]
                                        print(f"      Authors: {authors_OA}")

                                        # Calculate similarity between titles, authors, and years
                                        work_display_name = work.get('display_name', '')
                                        titles_similarity = similarity_titles(titolo, work_display_name)
                                        authors_similarity = similarity_authors(authors, authors_OA)
                                        years_similarity = similarity_years(anno, work.get('publication_year'))

                                        similarity_score = titles_similarity*0.5 + authors_similarity*0.25 + years_similarity*0.25
                                        print(f"      📊 Similarity score: {similarity_score:.3f}")

                                        if similarity_score > best_score:
                                                best_score = similarity_score      
                                                best_OA_ID = work.get('id')
                                                best_OA_display_name = work.get('display_name')
                                                best_OA_authors = [a.get("author", {}).get("display_name", "N/A") for a in work.get("authorships", [])]
                                                best_OA_year = work.get('publication_year')
                                print(f"\n   🏆 Best match selected:")
                                print(f"      Title: {best_OA_display_name}")
                                print(f"      ID: {best_OA_ID}")
                                print(f"      Authors: {best_OA_authors}")
                                
                                # Update statistics with best match (if PRINT_STATS is enabled)
                                if PRINT_STATS:
                                        work_stats["matched"] = True
                                        work_stats["match_found"] = True
                                        work_stats["similarity_score"] = best_score
                                        work_stats["openalex_id"] = best_OA_ID
                                        work_stats["openalex_title"] = best_OA_display_name
                                        work_stats["openalex_authors"] = best_OA_authors
                                        work_stats["openalex_year"] = best_OA_year
                        else:
                                print(f"✨ Single work found:")
                                print(f"   Title: {work_results[0].get('display_name', 'N/A')}")
                                print(f"   ID: {work_results[0].get('id', 'N/A')}")
                                authors_OA = [a.get("author", {}).get("display_name", "N/A") for a in work_results[0].get("authorships", [])]
                                print(f"   Authors: {authors_OA}")
                                # calculating similarity score
                                work_display_name = work_results[0].get('display_name', '')
                                titles_similarity = similarity_titles(titolo, work_display_name)
                                authors_similarity = similarity_authors(authors, authors_OA)
                                years_similarity = similarity_years(anno, work_results[0].get('publication_year'))
                                similarity_score = titles_similarity*0.5 + authors_similarity*0.25 + years_similarity*0.25
                                print(f"      Similarity score: {similarity_score:.3f}")
                                
                                # Update statistics with single match (if PRINT_STATS is enabled)
                                if PRINT_STATS:
                                        work_stats["matched"] = True
                                        work_stats["match_found"] = True
                                        work_stats["similarity_score"] = similarity_score
                                        work_stats["openalex_id"] = work_results[0].get('id')
                                        work_stats["openalex_title"] = work_results[0].get('display_name')
                                        work_stats["openalex_authors"] = authors_OA
                                        work_stats["openalex_year"] = work_results[0].get('publication_year')
                        
                        # Add statistics entry to list (if PRINT_STATS is enabled)
                        if PRINT_STATS:
                                stats_data.append(work_stats)

                except Exception as e:
                        # If API or other error occurs, exit program
                        print(f"💥 FATAL ERROR: {e}")
                        print(f"   Work: #{count}/{len(work_results)} - {handle} - {titolo} - {anno}")
                        exit(1)

                # Delay between processing different works to avoid overwhelming the API
                print("─" * 80)
                time.sleep(0.1)

# Close database connection and cursor
cursor.close()
conn.close()

# Calculate and display statistics if PRINT_STATS is enabled
if PRINT_STATS:
        # Calculate comprehensive statistics
        print("\nCalculating statistics...")
        stats = calculate_statistics(stats_data)
        
        # Print statistics in readable format
        print_statistics(stats)
        
        # Save calculated matching statistics to JSON file
        stats_filename = f"matching_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
                with open(stats_filename, 'w', encoding='utf-8') as f:
                        json.dump(stats, f, indent=2, ensure_ascii=False)
                print(f"\n📊 Matching statistics saved to: {stats_filename}")
        except Exception as e:
                print(f"⚠️  Error saving statistics: {e}")
