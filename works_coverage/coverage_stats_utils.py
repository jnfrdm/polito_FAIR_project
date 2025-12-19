#!/usr/bin/env python3
"""
Utility functions for calculating and printing OpenAlex vs Scopus coverage statistics.
These functions are used by OpenAlex_vs_Scopus.py to analyze coverage comparison results.
"""

def extract_statistics(all_results):
    """
    Extract and display statistics from OpenAlex vs Scopus coverage comparison results.
    
    Args:
        all_results: List of dictionaries containing author matching results
    """
    if not all_results:
        print("\n⚠️  No results to analyze.")
        return
    
    # Calculate and display statistics
    print("\n" + "="*80)
    print("STATISTICS: OpenAlex vs Scopus Coverage Comparison")
    print("="*80)
    
    # Total authors processed
    total_authors = len(all_results)
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total authors processed: {total_authors}")
    
    if total_authors > 0:
        # Authors with ORCID
        authors_with_orcid = [r for r in all_results if r.get("orcid") is not None]
        authors_without_orcid = [r for r in all_results if r.get("orcid") is None]
        print(f"   Authors with ORCID: {len(authors_with_orcid)} ({len(authors_with_orcid)/total_authors*100:.2f}%)")
        print(f"   Authors without ORCID: {len(authors_without_orcid)} ({len(authors_without_orcid)/total_authors*100:.2f}%)")
        
        # Authors with Scopus ID
        authors_with_scopus = [r for r in all_results if r.get("scopus_id") is not None]
        authors_without_scopus = [r for r in all_results if r.get("scopus_id") is None]
        print(f"   Authors with Scopus ID: {len(authors_with_scopus)} ({len(authors_with_scopus)/total_authors*100:.2f}%)")
        print(f"   Authors without Scopus ID: {len(authors_without_scopus)} ({len(authors_without_scopus)/total_authors*100:.2f}%)")
    
    # Works statistics
    total_works = sum(r.get("numero_lavori", 0) for r in all_results)
    total_works_with_doi = sum(r.get("numero_lavori_doi", 0) for r in all_results)
    print(f"\n📚 WORKS STATISTICS:")
    print(f"   Total works in IRIS: {total_works}")
    print(f"   Total works with DOI: {total_works_with_doi} ({total_works_with_doi/total_works*100:.2f}%)" if total_works > 0 else "   Total works with DOI: 0")
    
    # OpenAlex statistics
    total_oa_works = sum(r.get("oa_numero_lavori", 0) for r in all_results)
    total_oa_matches = sum(r.get("oa_match", 0) for r in all_results)
    authors_with_oa_profile = [r for r in all_results if r.get("open_alex_id") is not None]
    print(f"\n🅾️🅰️ OPENALEX STATISTICS:")
    print(f"   Authors with OpenAlex profile: {len(authors_with_oa_profile)}")
    print(f"   Total works found on OpenAlex: {total_oa_works}")
    print(f"   Total works matched on OpenAlex: {total_oa_matches}")
    if total_works > 0:
        print(f"   OpenAlex match rate: {total_oa_matches/total_works*100:.2f}%")
    
    # Scopus statistics
    total_scopus_works = sum(r.get("scopus_numero_lavori", 0) for r in all_results)
    total_scopus_matches = sum(r.get("scopus_match", 0) for r in all_results)
    print(f"\n🔎 SCOPUS STATISTICS:")
    print(f"   Total works found on Scopus: {total_scopus_works}")
    print(f"   Total works matched on Scopus: {total_scopus_matches}")
    if total_works > 0:
        print(f"   Scopus match rate: {total_scopus_matches/total_works*100:.2f}%")
    
    # KEY STATISTIC 1: Works with OA matches >= Scopus matches
    works_oa_greater_equal_scopus = [r for r in all_results 
                                     if r.get("oa_match", 0) >= r.get("scopus_match", 0)]
    print(f"\n🎯 KEY STATISTIC 1: When OpenAlex Coverage is greater than or equal to Scopus Coverage")
    if total_authors > 0:
        print(f"   Authors with number of OA matching works >= number of Scopus matching works: {len(works_oa_greater_equal_scopus)} ({len(works_oa_greater_equal_scopus)/total_authors*100:.2f}%)")
    else:
        print(f"   Authors with number of OA matching works >= number of Scopus matching works: {len(works_oa_greater_equal_scopus)}")
    
    # Breakdown of OA vs Scopus comparison
    oa_strictly_greater = [r for r in all_results 
                          if r.get("oa_match", 0) > r.get("scopus_match", 0)]
    oa_equal_scopus = [r for r in all_results 
                       if r.get("oa_match", 0) == r.get("scopus_match", 0)]
    scopus_strictly_greater = [r for r in all_results 
                               if r.get("scopus_match", 0) > r.get("oa_match", 0)]
    if total_authors > 0:
        print(f"   - Authors with OA matches > Scopus matches: {len(oa_strictly_greater)} ({len(oa_strictly_greater)/total_authors*100:.2f}%)")
        print(f"   - Authors with OA matches = Scopus matches: {len(oa_equal_scopus)} ({len(oa_equal_scopus)/total_authors*100:.2f}%)")
        print(f"   - Authors with Scopus matches > OA matches: {len(scopus_strictly_greater)} ({len(scopus_strictly_greater)/total_authors*100:.2f}%)")
    else:
        print(f"   - Authors with OA matches > Scopus matches: {len(oa_strictly_greater)}")
        print(f"   - Authors with OA matches = Scopus matches: {len(oa_equal_scopus)}")
        print(f"   - Authors with Scopus matches > OA matches: {len(scopus_strictly_greater)}")
    
    # Average match differences
    if works_oa_greater_equal_scopus:
        avg_oa_match = sum(r.get("oa_match", 0) for r in works_oa_greater_equal_scopus) / len(works_oa_greater_equal_scopus)
        avg_scopus_match = sum(r.get("scopus_match", 0) for r in works_oa_greater_equal_scopus) / len(works_oa_greater_equal_scopus)
        print(f"   Average OA matches (for authors with OA >= Scopus): {avg_oa_match:.2f}")
        print(f"   Average Scopus matches (for authors with OA >= Scopus): {avg_scopus_match:.2f}")
    
    # KEY STATISTIC 2: Works missing exclusively on OpenAlex
    works_missing_only_oa = [r for r in all_results 
                            if r.get("lavori_mancanti_solo_su_oa", 0) > 0]
    print(f"\n🎯 KEY STATISTIC 2: Works Missing Exclusively on OpenAlex")
    if total_authors > 0:
        print(f"   Authors with number of works missing only on OpenAlex > 0: {len(works_missing_only_oa)} ({len(works_missing_only_oa)/total_authors*100:.2f}%)")
    else:
        print(f"   Authors with number of works missing only on OpenAlex > 0: {len(works_missing_only_oa)}")
    
    if works_missing_only_oa:
        avg_missing_oa = sum(r.get("lavori_mancanti_solo_su_oa", 0) for r in works_missing_only_oa) / len(works_missing_only_oa)
        total_missing_oa = sum(r.get("lavori_mancanti_solo_su_oa", 0) for r in works_missing_only_oa)
        max_missing_oa = max(r.get("lavori_mancanti_solo_su_oa", 0) for r in works_missing_only_oa)
        min_missing_oa = min(r.get("lavori_mancanti_solo_su_oa", 0) for r in works_missing_only_oa)
        print(f"   Average number of works missing only on OpenAlex (for affected authors): {avg_missing_oa:.2f}")
        print(f"   Total works missing only on OpenAlex: {total_missing_oa}")
        print(f"   Maximum number of works missing only on OpenAlex: {max_missing_oa}")
        print(f"   Minimum number of works missing only on OpenAlex: {min_missing_oa}")
    else:
        print(f"   No authors have works missing exclusively on OpenAlex")
    
    # Additional statistics
    print(f"\n📈 ADDITIONAL STATISTICS:")
    
    # Authors with perfect matches on both platforms
    perfect_both = [r for r in all_results 
                   if r.get("oa_match", 0) == r.get("numero_lavori", 0) and 
                      r.get("scopus_match", 0) == r.get("numero_lavori", 0) and
                      r.get("numero_lavori", 0) > 0]
    print(f"   Authors with 100% match rate on both platforms: {len(perfect_both)}")
    
    # Authors with no matches on either platform
    no_matches_both = [r for r in all_results 
                      if r.get("oa_match", 0) == 0 and r.get("scopus_match", 0) == 0 and
                         r.get("numero_lavori", 0) > 0]
    print(f"   Authors with 0% match rate on both platforms: {len(no_matches_both)}")
    
    # Match rate distribution
    authors_with_works = [r for r in all_results if r.get("numero_lavori", 0) > 0]
    if authors_with_works:
        oa_match_rates = [r.get("oa_match", 0) / r.get("numero_lavori", 1) * 100 
                         for r in authors_with_works]
        scopus_match_rates = [r.get("scopus_match", 0) / r.get("numero_lavori", 1) * 100 
                              for r in authors_with_works]
        
        print(f"\n   Match Rate Distribution (for authors with works):")
        print(f"   OpenAlex:")
        print(f"     - Average match rate: {sum(oa_match_rates)/len(oa_match_rates):.2f}%")
        print(f"     - Authors with 100% match: {sum(1 for r in oa_match_rates if r == 100)}")
        print(f"     - Authors with 80-99% match: {sum(1 for r in oa_match_rates if 80 <= r < 100)}")
        print(f"     - Authors with 50-79% match: {sum(1 for r in oa_match_rates if 50 <= r < 80)}")
        print(f"     - Authors with <50% match: {sum(1 for r in oa_match_rates if r < 50)}")
        
        print(f"   Scopus:")
        print(f"     - Average match rate: {sum(scopus_match_rates)/len(scopus_match_rates):.2f}%")
        print(f"     - Authors with 100% match: {sum(1 for r in scopus_match_rates if r == 100)}")
        print(f"     - Authors with 80-99% match: {sum(1 for r in scopus_match_rates if 80 <= r < 100)}")
        print(f"     - Authors with 50-79% match: {sum(1 for r in scopus_match_rates if 50 <= r < 80)}")
        print(f"     - Authors with <50% match: {sum(1 for r in scopus_match_rates if r < 50)}")
    
    # Works per author statistics
    works_per_author = [r.get("numero_lavori", 0) for r in all_results]
    if works_per_author:
        print(f"\n   Works per Author:")
        print(f"     - Average: {sum(works_per_author)/len(works_per_author):.2f}")
        print(f"     - Maximum: {max(works_per_author)}")
        print(f"     - Minimum: {min(works_per_author)}")
        print(f"     - Authors with >50 works: {sum(1 for w in works_per_author if w > 50)}")
        print(f"     - Authors with >100 works: {sum(1 for w in works_per_author if w > 100)}")
    
    print("\n" + "="*80)

