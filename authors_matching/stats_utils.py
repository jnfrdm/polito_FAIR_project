#!/usr/bin/env python3
"""
Utility functions for calculating and printing author matching statistics.
These functions are used by authors_match.py to analyze matching results.
"""

from collections import Counter

def calculate_statistics(data):
    """
    Calculate comprehensive statistics from author matching data.
    
    Args:
        data: List of dictionaries containing author matching results
        
    Returns:
        dict: Dictionary containing calculated statistics
    """
    stats = {}
    
    total_authors = len(data)
    stats['total_authors'] = total_authors
    
    if total_authors == 0:
        return stats
    
    # Basic matching statistics
    authors_with_matches = [a for a in data if a.get('matches_found', 0) > 0]
    authors_without_matches = [a for a in data if a.get('matches_found', 0) == 0]
    
    stats['authors_with_matches'] = len(authors_with_matches)
    stats['authors_without_matches'] = len(authors_without_matches)
    stats['match_rate'] = len(authors_with_matches) / total_authors * 100 if total_authors > 0 else 0
    
    # ORCID statistics
    authors_with_orcid = [a for a in data if a.get('orcid') is not None]
    authors_without_orcid = [a for a in data if a.get('orcid') is None]
    stats['authors_with_orcid'] = len(authors_with_orcid)
    stats['authors_without_orcid'] = len(authors_without_orcid)
    
    # Match count statistics
    authors_single_match = [a for a in data if a.get('matches_found', 0) == 1]
    authors_multiple_matches = [a for a in data if a.get('matches_found', 0) > 1]
    
    stats['authors_single_match'] = len(authors_single_match)
    stats['authors_multiple_matches'] = len(authors_multiple_matches)
    
    # Search method statistics
    search_methods = [a.get('search_method') for a in data if a.get('search_method') is not None]
    stats['search_method_counts'] = dict(Counter(search_methods))
    
    # DOI-based analysis statistics
    authors_with_doi_analysis = [a for a in data if a.get('doi_analysis_performed', False)]
    authors_with_compatible_match = [a for a in data if a.get('compatible_match_found', False)]
    authors_with_similar_match = [a for a in data if a.get('similar_match_found', False)]
    authors_no_compatible_match = [a for a in data if a.get('no_compatible_match', False)]
    
    stats['authors_with_doi_analysis'] = len(authors_with_doi_analysis)
    stats['authors_with_compatible_match'] = len(authors_with_compatible_match)
    stats['authors_with_similar_match'] = len(authors_with_similar_match)
    stats['authors_no_compatible_match'] = len(authors_no_compatible_match)
    
    # Average matches per author
    if authors_with_matches:
        avg_matches = sum(a.get('matches_found', 0) for a in authors_with_matches) / len(authors_with_matches)
        stats['avg_matches_per_author'] = avg_matches
    else:
        stats['avg_matches_per_author'] = 0
    
    # Authors with publications (for DOI analysis)
    authors_with_publications = [a for a in data if a.get('publications_with_doi', 0) > 0]
    stats['authors_with_publications'] = len(authors_with_publications)
    
    if authors_with_publications:
        avg_publications = sum(a.get('publications_with_doi', 0) for a in authors_with_publications) / len(authors_with_publications)
        stats['avg_publications_per_author'] = avg_publications
    else:
        stats['avg_publications_per_author'] = 0
    
    return stats

def print_statistics(stats):
    """
    Print statistics in a readable format.
    
    Args:
        stats: Dictionary containing calculated statistics
    """
    print("\n" + "="*80)
    print("AUTHOR MATCHING STATISTICS")
    print("="*80)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total authors processed: {stats['total_authors']}")
    print(f"   Authors with matches found: {stats['authors_with_matches']} ({stats['match_rate']:.2f}%)")
    print(f"   Authors without matches: {stats['authors_without_matches']}")
    
    print(f"\n🔑 IDENTIFIER STATISTICS:")
    print(f"   Authors with ORCID: {stats['authors_with_orcid']} ({stats['authors_with_orcid']/stats['total_authors']*100:.2f}%)" if stats['total_authors'] > 0 else "   Authors with ORCID: 0")
    print(f"   Authors without ORCID: {stats['authors_without_orcid']} ({stats['authors_without_orcid']/stats['total_authors']*100:.2f}%)" if stats['total_authors'] > 0 else "   Authors without ORCID: 0")
    
    print(f"\n📈 MATCH COUNT STATISTICS:")
    print(f"   Authors with single match: {stats['authors_single_match']}")
    print(f"   Authors with multiple matches: {stats['authors_multiple_matches']}")
    if stats['authors_with_matches'] > 0:
        print(f"   Average matches per author (with matches): {stats['avg_matches_per_author']:.2f}")
    
    print(f"\n🔍 SEARCH METHOD STATISTICS:")
    if stats.get('search_method_counts'):
        print(f"   Method usage counts:")
        for method, count in stats['search_method_counts'].items():
            print(f"   - {method}: {count}")
    else:
        print(f"   No search method data available")
    
    print(f"\n📚 DOI-BASED ANALYSIS STATISTICS:")
    print(f"   Authors with publications (DOI available): {stats['authors_with_publications']}")
    if stats['authors_with_publications'] > 0:
        print(f"   Average publications per author: {stats['avg_publications_per_author']:.2f}")
    print(f"   Authors that required DOI-based analysis: {stats['authors_with_doi_analysis']}")
    print(f"   Authors with compatible match found: {stats['authors_with_compatible_match']}")
    print(f"   Authors with similar match found: {stats['authors_with_similar_match']}")
    print(f"   Authors with no compatible match: {stats['authors_no_compatible_match']}")
    
    print("\n" + "="*80)

