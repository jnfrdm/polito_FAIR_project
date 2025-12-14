import re

### SIMILARITY BETWEEN TITLES ###

# Minimal stopwords set (can be extended)
# Contains common Italian and English stopwords that should be filtered out
# when comparing titles for similarity
IT_STOP = {
    # Italian articles and prepositions
    "a","ad","al","allo","ai","agli","all","agl","alla","alle",
    "col","coi","con","della","delle","dei","del","dello","degli","di",
    "da","dal","dallo","dai","dagli","dalla","dalle",
    "in","nel","nello","nella","nei","negli","nelle","sul","sullo","sulla","sui","sugli","sulle",
    "tra","fra","su","sopra","sotto","oltre","contro","verso","entro",
    
    # Italian definite/indefinite articles
    "il","lo","la","i","gli","le","un","uno","una","l",

    # Italian conjunctions and pronouns
    "e","ed","o","oppure","ma","però","anche","ne","né","che","cui","come","dove","quando",
    "mentre","se","allora","quindi","dunque","poiché","perché",
    
    # Italian adverbs/common words
    "non","più","meno","mai","già","ancora","sempre","ora","adesso","poi","così","solo",
    "quasi","molto","troppo","poco","niente","nulla","tutto","ogni","ognuno",
    "questo","questa","questi","queste","quello","quella","quelli","quelle","ci","vi","mi","ti","si",

    # Common English stopwords
    "a","an","the","and","or","but","if","then","so","because","as","while","until","of","at","by",
    "for","with","about","against","between","into","through","during","before","after","above","below",
    "to","from","up","down","in","out","on","off","over","under",
    "again","further","once","here","there","when","where","why","how","all","any","both","each","few",
    "more","most","other","some","such","no","nor","not","only","own","same","than","too","very","can",
    "will","just","don","should","now","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","having","i","you","he","she","it","we","they","me","him","her","them","my","your",
    "yours","his","their","its","our","ours","theirs","this","that","these","those"
}

def _tokens_fast(s: str):
    """
    Fast tokenization function for title comparison.
    
    Converts string to lowercase, removes all non-alphanumeric characters,
    splits into tokens, and filters out stopwords and very short tokens.
    
    Args:
        s: Input string to tokenize
        
    Returns:
        Set of filtered tokens (words longer than 1 character, not in stopwords)
    """
    # Handle None or non-string inputs
    if s is None or not isinstance(s, str):
        return set()
    # Convert to lowercase and replace non-alphanumeric characters with spaces
    s = re.sub(r"[^a-zA-Z0-9]+", " ", s.lower()).strip()
    # Filter out stopwords and very short tokens (length <= 1)
    return {t for t in s.split() if len(t) > 1 and t not in IT_STOP}

def similarity_titles(s1: str, s2: str) -> float:
    """
    Calculate Jaccard similarity between two titles based on word sets.
    
    This is a base implementation that works well. It can be improved with:
    - Character bigrams/trigrams
    - Better normalization (handling accents, abbreviations, etc.)
    - TF-IDF weighting
    
    Args:
        s1: First title string
        s2: Second title string
        
    Returns:
        Jaccard similarity score between 0.0 and 1.0
        - 1.0 if both titles are empty or identical
        - 0.0 if titles share no common words or if inputs are None/wrong format
        - Otherwise: intersection_size / union_size
    """
    # Validate inputs: return 0 if None or not strings
    if s1 is None or s2 is None or not isinstance(s1, str) or not isinstance(s2, str):
        return 0.0
    
    t1, t2 = _tokens_fast(s1), _tokens_fast(s2)
    # If both are empty, consider them identical
    if not t1 and not t2:
        return 1.0
    # Calculate intersection and union of token sets
    inter = len(t1 & t2)
    union = len(t1 | t2)
    return inter / union if union else 0.0

### SIMILARITY BETWEEN AUTHORS ###

# Normalization: lowercase, removal of punctuation and common titles (IT/EN)
# Set of common titles and honorifics that should be removed when comparing author names
STOPWORDS = {
    # Italian titles
    "dr","dott","dottor","dottore","dottssa","dott.ssa","dott.sso","dott.sse",
    "prof","professor","professore","profssa","prof.ssa",
    "ing","arch","geom","rag","avv","notaio","on","onorevole","pres","presidente",
    "min","ministro","sen","senatore","mons","monsignor","monsignore",
    "rev","reverendo","don","fra","padre","suor","sig","sigra","sig.ra","signor",
    "signore","signora","signorina",
    # English/other titles
    "mr","mrs","ms","miss","sir","lady","lord","madam","madame",
    "reverend","drs","doctor","phd","md","lt","sgt","col","gen","cap","mag",
    "capt","ltcol","ltgen","maj","cpt","colonnello","generale","capitano","maggiore",
}


def normalize_author(name: str):
    """
    Normalize an author name by converting to lowercase, removing punctuation,
    and filtering out common titles/honorifics.
    
    Args:
        name: Author name string
        
    Returns:
        List of normalized tokens (words) without stopwords
    """
    # Handle None or non-string inputs
    if name is None or not isinstance(name, str):
        return []
    # Convert to lowercase and remove punctuation
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    # Split into tokens and filter out stopwords
    tokens = [t for t in name.split() if t and t not in STOPWORDS]
    return tokens

def initials(tokens):
    """
    Extract the first character (initial) from each token.
    
    Args:
        tokens: List of token strings
        
    Returns:
        List of first characters from each token
    """
    # Handle None or non-list inputs
    if tokens is None or not isinstance(tokens, list):
        return []
    return [t[0] for t in tokens if t]

def author_similarity(a: str, b: str) -> float:
    """
    Calculate similarity between two author names.
    
    Uses multiple heuristics:
    - Token set intersection/union (Jaccard)
    - Initial matching
    - Surname matching with/without first name initial
    
    Args:
        a: First author name
        b: Second author name
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    ta, tb = normalize_author(a), normalize_author(b)
    # If either name is empty after normalization, no similarity
    if not ta or not tb:
        return 0.0
    
    # Identical case: exact match after normalization
    if ta == tb:
        return 1.0
    
    # Calculate base similarity using token intersection/union
    inter = len(set(ta) & set(tb))
    union = len(set(ta) | set(tb))
    base = inter / union if union else 0.0

    # Check if initials match (if only initials are available but they match)
    ia, ib = initials(ta), initials(tb)
    if ia == ib and ia:  # Only initials but they match
        base = max(base, 0.6)
    
    # If surnames match (last token)
    if ta[-1] == tb[-1]:
        if ta[0][0] == tb[0][0]:
            # First name initial + surname match
            base = max(base, 0.8)
        else:
            # Only surname matches
            base = max(base, 0.7)
    
    return base

def similarity_authors(lst1, lst2):
    """
    Calculate similarity between two lists of authors using greedy matching.
    
    Uses a greedy algorithm: for each author in the first list, matches it
    with the best unmatched author in the second list.
    
    Args:
        lst1: First list of author names
        lst2: Second list of author names
        
    Returns:
        Average similarity score between 0.0 and 1.0
        - 1.0 if both lists are empty
        - 0.0 if one list is empty and the other is not, or if inputs are None/wrong format
    """
    # Validate inputs: return 0 if None or not lists
    if lst1 is None or lst2 is None or not isinstance(lst1, list) or not isinstance(lst2, list):
        return 0.0
    
    if not lst1 and not lst2:
        return 1.0
    if not lst1 or not lst2:
        return 0.0
    
    # Build similarity matrix: similarity between each pair of authors
    sim_matrix = [[author_similarity(a, b) for b in lst2] for a in lst1]
    
    # Greedy matching: always pick the best remaining match
    used_b = set()  # Track which authors from lst2 have been matched
    total = 0
    for row in sim_matrix:
        best = -1
        best_idx = None
        # Find the best unmatched author in lst2 for current author in lst1
        for j, val in enumerate(row):
            if j not in used_b and val > best:
                best, best_idx = val, j
        if best_idx is not None:
            used_b.add(best_idx)
            total += best
    
    # Return average similarity normalized by the maximum list length
    return total / max(len(lst1), len(lst2))


### COMPLEX SIMILARITY BETWEEN AUTHORS (HUNGARIAN ALGORITHM) ###

# Note: The functions normalize_author, initials, and author_similarity are
# duplicated here. They are identical to the versions above and could be
# consolidated to avoid code duplication.

# --- Normalization and similarity between individual authors ---
def normalize_author(name: str):
    """
    Normalize an author name (duplicate of function above).
    See the first normalize_author function for documentation.
    """
    # Handle None or non-string inputs
    if name is None or not isinstance(name, str):
        return []
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    tokens = [t for t in name.split() if t and t not in STOPWORDS]
    return tokens

def initials(tokens):
    """
    Extract initials from tokens (duplicate of function above).
    See the first initials function for documentation.
    """
    # Handle None or non-list inputs
    if tokens is None or not isinstance(tokens, list):
        return []
    return [t[0] for t in tokens if t]

def author_similarity(a: str, b: str) -> float:
    """
    Calculate similarity between two author names (duplicate of function above).
    See the first author_similarity function for documentation.
    """
    ta, tb = normalize_author(a), normalize_author(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0

    inter = len(set(ta) & set(tb))
    union = len(set(ta) | set(tb))
    base = inter / union if union else 0.0

    ia, ib = initials(ta), initials(tb)
    if ia == ib and ia:
        base = max(base, 0.6)

    if ta[-1] == tb[-1]:
        if ta[0][0] == tb[0][0]:
            # First name initial + surname match
            base = max(base, 0.8)
        else:
            # Only surname matches
            base = max(base, 0.7)

    return base

# --- Hungarian (Munkres) algorithm for minimum cost assignment on square matrix ---

def hungarian_min_cost(cost):
    """
    Hungarian (Munkres) algorithm for minimum cost assignment on a square matrix.
    
    Implements the Hungarian algorithm to find the optimal assignment that minimizes
    the total cost. The algorithm works by finding independent zeros and augmenting
    paths to create an optimal matching.
    
    Args:
        cost: NxN matrix (list of lists) of float costs
        
    Returns:
        List of (row, column) tuples representing the optimal assignment
    """
    import math
    N = len(cost)
    # Create a working copy of the cost matrix
    C = [row[:] for row in cost]

    # Row reduction: subtract minimum from each row
    for i in range(N):
        m = min(C[i])
        for j in range(N):
            C[i][j] -= m
    # Column reduction: subtract minimum from each column
    for j in range(N):
        m = min(C[i][j] for i in range(N))
        for i in range(N):
            C[i][j] -= m

    # Mask matrix: 0=unmarked, 1=starred, 2=primed
    mask = [[0]*N for _ in range(N)]
    row_cover = [False]*N  # Track covered rows
    col_cover = [False]*N  # Track covered columns

    # Find independent zeros and mark them with stars
    for i in range(N):
        for j in range(N):
            if C[i][j] == 0 and not row_cover[i] and not col_cover[j]:
                mask[i][j] = 1  # Star this zero
                row_cover[i] = True
                col_cover[j] = True
    # Reset covers for main algorithm
    row_cover = [False]*N
    col_cover = [False]*N

    def cover_star_columns():
        """Cover all columns containing a starred zero."""
        for i in range(N):
            for j in range(N):
                if mask[i][j] == 1:
                    col_cover[j] = True
        return sum(col_cover)

    def find_a_zero():
        """Find an uncovered zero in the matrix."""
        for i in range(N):
            if not row_cover[i]:
                for j in range(N):
                    if (not col_cover[j]) and C[i][j] == 0:
                        return i, j
        return None, None

    def find_star_in_row(r):
        """Find a starred zero in the given row."""
        for j in range(N):
            if mask[r][j] == 1:
                return j
        return None

    def find_star_in_col(c):
        """Find a starred zero in the given column."""
        for i in range(N):
            if mask[i][c] == 1:
                return i
        return None

    def find_prime_in_row(r):
        """Find a primed zero in the given row."""
        for j in range(N):
            if mask[r][j] == 2:
                return j
        return None

    def augment_path(path):
        """Augment the path by flipping stars and primes."""
        for (r, c) in path:
            if mask[r][c] == 1:
                mask[r][c] = 0  # Unstar
            elif mask[r][c] == 2:
                mask[r][c] = 1  # Star

    def clear_primes():
        """Clear all primed zeros."""
        for i in range(N):
            for j in range(N):
                if mask[i][j] == 2:
                    mask[i][j] = 0

    def smallest_uncovered():
        """Find the smallest uncovered value in the matrix."""
        m = math.inf
        for i in range(N):
            if not row_cover[i]:
                for j in range(N):
                    if not col_cover[j] and C[i][j] < m:
                        m = C[i][j]
        return 0.0 if m is math.inf else m

    # Main algorithm loop
    count = cover_star_columns()
    while count < N:
        # Find an uncovered zero
        z_r, z_c = find_a_zero()
        # If no uncovered zero exists, adjust the matrix
        while z_r is None:
            m = smallest_uncovered()
            # Add m to covered rows, subtract from uncovered columns
            for i in range(N):
                for j in range(N):
                    if row_cover[i]:
                        C[i][j] += m
                    if not col_cover[j]:
                        C[i][j] -= m
            z_r, z_c = find_a_zero()

        # Prime the uncovered zero
        mask[z_r][z_c] = 2
        star_col = find_star_in_row(z_r)
        if star_col is not None:
            # Cover the row and uncover the column
            row_cover[z_r] = True
            col_cover[star_col] = False
        else:
            # Build augmenting path
            path = [(z_r, z_c)]
            star_row = find_star_in_col(z_c)
            while star_row is not None:
                path.append((star_row, z_c))
                prime_col = find_prime_in_row(star_row)
                path.append((star_row, prime_col))
                z_c = prime_col
                star_row = find_star_in_col(z_c)
            # Augment the path and reset covers
            augment_path(path)
            clear_primes()
            row_cover = [False]*N
            col_cover = [False]*N
            count = cover_star_columns()

    # Extract the final assignment from starred zeros
    assignment = []
    for i in range(N):
        for j in range(N):
            if mask[i][j] == 1:
                assignment.append((i, j))
                break
    return assignment

# --- Similarity between author lists using Hungarian algorithm to maximize similarity sum ---
def similarity_authors_hungarian(lst1, lst2):
    """
    Calculate similarity between two lists of authors using the Hungarian algorithm.
    
    This provides optimal matching (better than greedy) by finding the assignment
    that maximizes the total similarity. The algorithm handles cases where lists
    have different lengths by padding with dummy entries.
    
    Args:
        lst1: First list of author names
        lst2: Second list of author names
        
    Returns:
        Average similarity score between 0.0 and 1.0
        - 1.0 if both lists are empty
        - 0.0 if one list is empty and the other is not
    """
    n, m = len(lst1), len(lst2)
    if n == 0 and m == 0:
        return 1.0
    if n == 0 or m == 0:
        return 0.0

    # Build similarity matrix between all pairs of authors
    sim = [[author_similarity(a, b) for b in lst2] for a in lst1]
    N = max(n, m)

    # Convert similarity to cost: cost = 1 - similarity
    # Pad with cost 1.0 (equivalent to similarity 0.0) to make matrix square
    cost = [[1.0]*N for _ in range(N)]
    for i in range(n):
        for j in range(m):
            cost[i][j] = 1.0 - sim[i][j]

    # Find optimal assignment using Hungarian algorithm
    assignment = hungarian_min_cost(cost)

    # Calculate total similarity from the optimal assignment
    total_sim = 0.0
    for (i, j) in assignment:
        if i < n and j < m:
            total_sim += sim[i][j]
    return total_sim / N

### SIMILARITY BETWEEN PUBLICATION YEARS ###

def similarity_years(year1, year2):
    """
    Calculate similarity between two publication years.
    
    Uses a step function that decreases similarity as the year difference increases.
    The similarity drops more sharply for larger differences, reflecting that
    publications far apart in time are less likely to be related.
    
    Args:
        year1: First publication year (integer)
        year2: Second publication year (integer)
        
    Returns:
        Similarity score between 0.05 and 1.0:
        - 1.0 if years are identical
        - 0.7 if difference <= 5 years
        - 0.5 if difference <= 10 years
        - 0.3 if difference <= 20 years
        - 0.2 if difference <= 50 years
        - 0.1 if difference <= 100 years
        - 0.05 if difference > 100 years
        - 0.0 if inputs are None or wrong format
    """
    # Validate inputs: return 0 if None or not integers
    if year1 is None or year2 is None or not isinstance(year1, (int, float)) or not isinstance(year2, (int, float)):
        return 0.0
    
    # Convert to int if float (in case year comes as float)
    try:
        year1 = int(year1)
        year2 = int(year2)
    except (ValueError, TypeError):
        return 0.0
    
    years_dif = abs(year1 - year2)
    if years_dif == 0:
        return 1
    if years_dif > 0 and years_dif <= 5:
        return 0.7
    if years_dif > 5 and years_dif <= 10:
        return 0.5
    if years_dif > 10 and years_dif <= 20:
        return 0.3
    if years_dif > 20 and years_dif <= 50:
        return 0.2
    if years_dif > 50 and years_dif <= 100:
        return 0.1
    if years_dif > 100:
        return 0.05
    
