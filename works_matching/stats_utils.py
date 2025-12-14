#!/usr/bin/env python3
"""
Utility functions for calculating and printing matching statistics.
These functions are used by match_works.py to analyze matching results.
"""

from collections import Counter

def calculate_statistics(data):
    """
    Calculate comprehensive statistics from matching data.
    """
    stats = {}
    
    total_works = len(data)
    stats['total_works'] = total_works
    
    # Basic matching statistics
    matched_works = [w for w in data if w.get('matched') is True]
    match_found_works = [w for w in data if w.get('match_found') is True]
    unmatched_works = [w for w in data if w.get('match_found') is False]
    
    stats['matched'] = len(matched_works)
    stats['match_found'] = len(match_found_works)
    stats['unmatched'] = len(unmatched_works)
    stats['match_rate'] = len(match_found_works) / total_works * 100 if total_works > 0 else 0
    
    # Similarity score statistics
    similarity_scores = [w.get('similarity_score') for w in match_found_works 
                        if w.get('similarity_score') is not None]
    
    if similarity_scores:
        # Similarity score distribution
        stats['similarity_distribution'] = {
            'perfect_matches (1.0)': sum(1 for s in similarity_scores if s == 1.0),
            'high_quality (0.9-1.0)': sum(1 for s in similarity_scores if 0.9 <= s < 1.0),
            'good_quality (0.8-0.9)': sum(1 for s in similarity_scores if 0.8 <= s < 0.9),
            'moderate_quality (0.7-0.8)': sum(1 for s in similarity_scores if 0.7 <= s < 0.8),
            'low_quality (0.5-0.7)': sum(1 for s in similarity_scores if 0.5 <= s < 0.7),
            'poor_quality (<0.5)': sum(1 for s in similarity_scores if s < 0.5),
            'high_confidence (>0.8)': sum(1 for s in similarity_scores if s > 0.8),
        }
    else:
        stats['similarity_distribution'] = None
    
    # Search method statistics
    search_methods = [w.get('search_method') for w in match_found_works 
                     if w.get('search_method') is not None]
    stats['search_method_counts'] = dict(Counter(search_methods))
    
    return stats

def print_statistics(stats):
    """
    Print statistics in a readable format.
    """
    print("\n" + "="*80)
    print("MATCHING ALGORITHM PERFORMANCE STATISTICS")
    print("="*80)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total works processed: {stats['total_works']}")
    print(f"   Works with matches found: {stats['match_found']} ({stats['match_rate']:.2f}%)")
    print(f"   Works matched (matched=True): {stats['matched']}")
    print(f"   Works not matched: {stats['unmatched']}")
    
    print(f"\n📈 SIMILARITY SCORE STATISTICS:")
    if stats['similarity_distribution']:
        dist = stats['similarity_distribution']
        print(f"\n   Distribution:")
        print(f"   - Perfect matches (1.0): {dist['perfect_matches (1.0)']}")
        print(f"   - High quality (0.9-1.0): {dist['high_quality (0.9-1.0)']}")
        print(f"   - Good quality (0.8-0.9): {dist['good_quality (0.8-0.9)']}")
        print(f"   - Moderate quality (0.7-0.8): {dist['moderate_quality (0.7-0.8)']}")
        print(f"   - Low quality (0.5-0.7): {dist['low_quality (0.5-0.7)']}")
        print(f"   - Poor quality (<0.5): {dist['poor_quality (<0.5)']}")
        print(f"   - High confidence (>0.8): {dist['high_confidence (>0.8)']}")
    
    print(f"\n🔍 SEARCH METHOD STATISTICS:")
    print(f"   Method usage counts:")
    for method, count in stats['search_method_counts'].items():
        print(f"   - {method}: {count}")
    
    print("\n" + "="*80)

