#!/usr/bin/env python3
"""
Author matching script that:
1. Gets all authors from IRIS (with ORCID if available)
2. Searches OpenAlex for matching authors: first by ORCID if available, then by name and affiliation
3. For authors with multiple matches, uses DOI-based work analysis to find the best match
"""

import os
import sys
import time
import requests
from collections import Counter

# Add the project root directory to Python path to enable imports from utilities
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utilities.db_utils import test_connection, execute_query_with_connection
from utilities.sim_lib import author_similarity
from authors_matching.stats_utils import calculate_statistics, print_statistics

# Constants
ROR_POLITO = 'https://ror.org/00bgk9508'  # ROR identifier for Politecnico di Torino
OPENALEX_API_BASE = 'https://api.openalex.org'  # Base URL for OpenAlex API
API_DELAY = 0.1  # Delay between API calls to respect rate limits (in seconds)
WORK_API_DELAY = 0.05  # Delay when fetching work data by DOI (in seconds)

# Test database connection and get connection/cursor objects
conn, cursor = test_connection()

print("=" * 80)
print("AUTHOR MATCHING WITH OPENALEX")
print("=" * 80)
print()

# Query to get all distinct authors from IRIS database
# Returns: matricola (employee ID), NOME_AUTORE (first name), COGNOME_AUTORE (last name), ORCID
select_all_authors_query = """
SELECT DISTINCT matricola, NOME_AUTORE, COGNOME_AUTORE, ORCID
FROM pub_ri_prodotti_autori
"""

print("Fetching all authors from IRIS...")
authors = execute_query_with_connection(cursor, select_all_authors_query, conn=conn)
print(f"Found {len(authors)} authors to process\n")
print("=" * 80)
print()

# Main loop: process each author completely in one iteration
# For each author: search OpenAlex -> analyze matches -> output results
main_loop_count = 0
total = len(authors)

# List to store statistics data for each author
stats_data = []

for idx, author in enumerate(authors, 1):
    main_loop_count += 1
    
    # Extract author information from database record
    matricola = author.get("matricola")  # Employee ID
    nome = author.get("NOME_AUTORE")  # First name
    cognome = author.get("COGNOME_AUTORE")  # Last name
    orcid = author.get("ORCID")  # ORCID identifier (may be None)
    
    # Skip authors with missing essential information
    if not matricola or not nome or not cognome:
        continue
    
    print(f"[{main_loop_count}/{total}] Processing: {nome} {cognome} (matricola: {matricola})")
    print("-" * 80)
    
    # Initialize statistics entry for this author
    author_stats = {
        "matricola": matricola,
        "nome": nome,
        "cognome": cognome,
        "orcid": orcid,
        "matches_found": 0,
        "search_method": None,
        "doi_analysis_performed": False,
        "compatible_match_found": False,
        "similar_match_found": False,
        "no_compatible_match": False,
        "publications_with_doi": 0
    }
    
    # STEP 1: Search OpenAlex for this author
    # Try ORCID search first (more reliable), then fall back to name/affiliation search
    search_successful = False
    oa_authors = []  # List of (display_name, oa_id) tuples for matching authors
    
    # If ORCID is present, search OpenAlex by ORCID first (more reliable than name search)
    if orcid:
        print(f"  🔍 Searching by ORCID...")
        
        # Search OpenAlex using ORCID filter
        # ORCID format in OpenAlex API: https://orcid.org/{orcid}
        # Also include name in search query to improve accuracy
        search_query = f"{nome}%20{cognome}"
        url = f"{OPENALEX_API_BASE}/authors?search={search_query}&filter=orcid:https://orcid.org/{orcid}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                response_data = response.json()
                count = response_data.get("meta", {}).get("count", 0)
                if count >= 1:
                    # Extract matching authors from results
                    results = response_data.get('results', [])
                    for match_author in results:
                        if match_author.get('id') and match_author.get('display_name'):
                            oa_authors.append((match_author['display_name'], match_author['id']))
                    search_successful = True
                    print(f"  ✅ Found {len(oa_authors)} author(s) by ORCID")
                    author_stats["search_method"] = "ORCID"
                else:
                    print(f"  ⚠️  No match found by ORCID, falling back to name/affiliation search")
            else:
                print(f"  ⚠️  API error with ORCID search, falling back to name/affiliation search")
        except Exception as e:
            print(f"  ⚠️  Error searching by ORCID: {e}, falling back to name/affiliation search")
    
    # If no ORCID or ORCID search failed, search by name and affiliation (Politecnico di Torino)
    # This is a broader search that may return multiple potential matches
    if not search_successful:
        if orcid:
            print(f"  🔍 Searching by name/institution...")
        else:
            print(f"  🔍 Searching by name/institution (no ORCID available)...")
        
        # Search by author name and filter by Politecnico di Torino ROR identifier
        search_query = f"{nome}%20{cognome}"
        url = f"{OPENALEX_API_BASE}/authors?search={search_query}&filter=affiliations.institution.ror:{ROR_POLITO}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Extract matching authors from results
                results = response.json().get('results', [])
                for match_author in results:
                    if match_author.get('id') and match_author.get('display_name'):
                        oa_authors.append((match_author['display_name'], match_author['id']))
                if oa_authors:
                    print(f"  ✅ Found {len(oa_authors)} author(s) by name/institution")
                    if not author_stats["search_method"]:
                        author_stats["search_method"] = "name_institution"
                else:
                    print(f"  ⚠️  No match found by name/institution")
                    if not author_stats["search_method"]:
                        author_stats["search_method"] = "name_institution"
        except Exception as e:
            print(f"  Error searching OpenAlex for {nome} {cognome}: {e}")
    
    # Rate limiting: delay between API calls to avoid overwhelming the API
    time.sleep(API_DELAY)
    
    # If no matches found, skip to next author (no further processing possible)
    if not oa_authors:
        print(f"  No OpenAlex matches found for this author")
        print()
        author_stats["matches_found"] = 0
        stats_data.append(author_stats)
        continue
    
    # Update statistics with number of matches found
    author_stats["matches_found"] = len(oa_authors)
    
    # Display all found matches
    print(f"  Found {len(oa_authors)} OpenAlex candidate(s):")
    for oa_idx, (display_name_choose, id_choose) in enumerate(oa_authors, 1):
        print(f"    {oa_idx}. {display_name_choose} ({id_choose})")
    
    # STEP 2: If multiple matches found, use DOI-based work analysis to find the best match
    # This analyzes which OpenAlex author appears most frequently in the author's publications
    if len(oa_authors) > 1:
        print(f"  Multiple matches found - checking for DOI-based analysis...")
        
        # Query to get all DOIs for publications by this author (matricola)
        # Joins pub_ri_prodotti_autori with pub_ri_prodotti_base to get DOI information
        select_doi_by_matricola_query = """
        SELECT DISTINCT iw.cd_doi as doi
        FROM pub_ri_prodotti_autori AS it
        INNER JOIN pub_ri_prodotti_base AS iw
        ON it.handle = iw.HANDLE 
        WHERE iw.cd_doi IS NOT NULL AND it.matricola = %s
        """
        
        dois = execute_query_with_connection(cursor, select_doi_by_matricola_query, params=(matricola,), conn=conn)
        author_stats["publications_with_doi"] = len(dois)
        print(f"  Found {len(dois)} publication(s) with DOI")
        
        # Need at least one DOI to perform analysis
        if len(dois) == 0:
            print("  ⚠️  No publications with DOI found - cannot perform detailed analysis")
            print()
            stats_data.append(author_stats)
            continue
        
        # Mark that DOI-based analysis is being performed
        author_stats["doi_analysis_performed"] = True
        
        # Collect all authors from works to find which OpenAlex author appears most frequently
        # This helps identify the correct author when multiple matches exist
        all_authors_data = []  # List of all author tuples found in works
        counter = Counter()  # Count occurrences of each author across all works
        doi_count = 0
        
        # For each DOI, fetch the work from OpenAlex and extract all authors
        for d_item in dois:
            doi_count += 1
            doi = d_item.get("doi")
            if not doi:
                continue
            
            # Fetch work data from OpenAlex using DOI
            url = f"{OPENALEX_API_BASE}/works/https://doi.org/{doi}"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    authorships = data.get("authorships", [])
                    
                    # Extract all authors from this work
                    for authorship in authorships:
                        author = authorship.get("author")
                        if author and author.get("display_name") and author.get("id"):
                            couple = (author["display_name"], author["id"])
                            all_authors_data.append(couple)
                            counter[couple] += 1  # Count how many times this author appears
            except Exception as e:
                print(f"  Error fetching work by DOI {doi}: {e}")
            
            # Progress indicator (overwrites same line)
            print(f"  Investigating work authors {doi_count}/{len(dois)} ... ", end="\r")
            time.sleep(WORK_API_DELAY)  # Rate limiting
        
        print()  # New line after progress indicator
        
        # If no authors found in any works, cannot perform analysis
        if not counter:
            print("  ⚠️  No authors found in works")
            print()
            stats_data.append(author_stats)
            continue
        
        # First pass: look for exact matches in top 3 most common authors from works
        # Check if any of the OpenAlex candidates match the most frequent authors in the works
        flag = False
        ranking_position = 0
        for item in counter.most_common(3):  # Check top 3 most frequent authors
            ranking_position += 1
            item_data, count = item
            item_display_name = item_data[0]  # Author display name
            item_id = item_data[1]  # OpenAlex author ID
            
            # Check if this author ID matches any of our OpenAlex candidates
            for oa_display_name, oa_id in oa_authors:
                if item_id == oa_id:
                    print(f"  ✓ Compatible match found: {item_display_name} ({count} occurrences, rank {ranking_position})")
                    print(f"    OpenAlex ID: {item_id}")
                    author_stats["compatible_match_found"] = True
                    flag = True
                    break
            
            if flag:
                break
        
        # Second pass: if no exact match found, look for similar names using similarity scoring
        # This handles cases where the name might be slightly different (e.g., middle initials)
        last_flag = False
        if not flag:
            for item in counter.most_common():
                item_data, count = item
                item_display_name = item_data[0]
                item_id = item_data[1]
                
                # Calculate similarity between IRIS name and OpenAlex author name
                iris_full_name = f"{nome} {cognome}"
                score_similarity = author_similarity(item_display_name, iris_full_name)
                
                # If similarity is high enough (>0.7), consider it a match
                if score_similarity > 0.7:
                    print(f"  ✓ Similar match found: {item_display_name} ({count} occurrences, similarity: {score_similarity:.2f})")
                    print(f"    OpenAlex ID: {item_id}")
                    author_stats["similar_match_found"] = True
                    last_flag = True
                    break
            
            # If still no match found, report the most frequent author (even if incompatible)
            if not last_flag:
                most_common = counter.most_common(1)
                if most_common:
                    item_data, count = most_common[0]
                    print(f"  ✗ No compatible match found")
                    print(f"    Most frequent (incompatible): {item_data[0]} ({count} occurrences)")
                    print(f"    OpenAlex ID: {item_data[1]}")
                    author_stats["no_compatible_match"] = True
                else:
                    print(f"  ✗ No result")
                    author_stats["no_compatible_match"] = True
    else:
        # Single match found - no need for further analysis (unique match)
        if oa_authors:
            oa_display_name, oa_id = oa_authors[0]
            print(f"  ✓ Single match found - no further analysis needed")
            print(f"    OpenAlex ID: {oa_id}")
    
    # Add statistics entry to list
    stats_data.append(author_stats)
    
    print()

print("=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)
print(f"Processed {main_loop_count} authors")

# Calculate and display statistics
if stats_data:
    print("\nCalculating statistics...")
    stats = calculate_statistics(stats_data)
    print_statistics(stats)

# Close database connection and cursor
cursor.close()
conn.close()
