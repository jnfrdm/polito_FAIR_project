# Polito FAIR Project

A Python project for matching and comparing academic authors and works between IRIS (Politecnico di Torino's institutional repository), OpenAlex, and Scopus databases. This project implements FAIR (Findable, Accessible, Interoperable, Reusable) data principles for academic research data management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Modules](#modules)
- [Dependencies](#dependencies)
- [License](#license)

## 🎯 Overview

This project provides tools for:
- **Author Matching**: Matching authors from IRIS database with OpenAlex profiles using ORCID, name, and affiliation matching
- **Work Matching**: Matching publications from IRIS with OpenAlex works using DOI, title, institution, and publication year
- **Coverage Analysis**: Comparing coverage of authors' works between OpenAlex and Scopus databases

The project is designed to help researchers and institutions:
- Identify and link authors across different academic databases
- Match publications between institutional repositories and open databases
- Analyze coverage gaps between different academic platforms
- Generate statistics on matching performance and database coverage

## ✨ Features

### Author Matching (`authors_matching/`)
- Search OpenAlex by ORCID (when available) for reliable author identification
- Fallback to name and institution-based search when ORCID is unavailable
- DOI-based work analysis for disambiguating multiple author matches
- Comprehensive statistics on matching performance

### Work Matching (`works_matching/`)
- Multi-strategy matching: DOI → Title/Institution/Year → Title-only
- Similarity scoring based on titles, authors, and publication years
- Handles multiple matches with best-match selection
- Detailed matching statistics and performance metrics

### Coverage Analysis (`works_coverage/`)
- Compare OpenAlex and Scopus coverage for authors
- Identify works missing exclusively on each platform
- Generate comprehensive coverage statistics
- Support for batch processing and result persistence

## 📁 Project Structure

```
polito_FAIR_project/
├── authors_matching/
│   ├── authors_match.py          # Main author matching script
│   ├── stats_utils.py            # Author matching statistics utilities
│   └── search_author.ipynb       # Jupyter notebook for author search
├── works_matching/
│   ├── works_match.py            # Main work matching script
│   ├── stats_utils.py            # Work matching statistics utilities
│   └── search_work.ipynb         # Jupyter notebook for work search
├── works_coverage/
│   ├── OpenAlex_vs_Scopus.py     # Main coverage comparison script
│   ├── coverage_stats_utils.py   # Coverage statistics utilities
│   └── OpenAlex_vs_Scopus copy.py # Backup/alternative version
├── utilities/
│   ├── db_utils.py               # Database connection and query utilities
│   ├── file_utils.py             # File I/O utilities (JSON)
│   └── sim_lib.py                # Similarity calculation functions
├── .env                          # Environment variables (not in repo)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── LICENSE                       # License file
└── README.md                     # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- MySQL database access (for IRIS database)
- Internet connection (for OpenAlex API access)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd polito_FAIR_project
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root with your database credentials:
   ```env
   user=your_db_username
   password=your_db_password
   host=your_db_host
   database=your_database_name
   ```

## ⚙️ Configuration

### Database Configuration

The project requires access to a MySQL database containing IRIS data. Configure your connection in the `.env` file:

```env
user=your_username
password=your_password
host=localhost
database=iris_database
```

### API Configuration

- **OpenAlex API**: No API key required. The project uses the public OpenAlex API with rate limiting (0.1s delay between calls).
- **Scopus**: Access to Scopus data is through the IRIS database tables (`pub_scopus_articles`, `pub_scopus_articles_author`).

### Rate Limiting

The scripts include built-in rate limiting to respect API limits:
- Author search: 0.1 seconds delay
- Work search by DOI: 0.05 seconds delay
- General API calls: 0.1 seconds delay

## 📖 Usage

### Author Matching

Match authors from IRIS with OpenAlex profiles:

```bash
python authors_matching/authors_match.py
```

This script will:
1. Fetch all authors from IRIS database
2. Search OpenAlex for each author (by ORCID if available, otherwise by name/institution)
3. For authors with multiple matches, perform DOI-based analysis
4. Generate and display matching statistics

### Work Matching

Match publications from IRIS with OpenAlex works:

```bash
python works_matching/works_match.py
```

This script will:
1. Fetch works from IRIS database (configure date range in the script)
2. Search OpenAlex for each work (by DOI, then title/institution/year, then title-only)
3. Calculate similarity scores for multiple matches
4. Generate and display matching statistics
5. Save statistics to a JSON file

**Note**: Modify the SQL query in `works_match.py` to adjust the date range and limit of works to process.

### Coverage Analysis

Compare OpenAlex and Scopus coverage for authors:

```bash
python works_coverage/OpenAlex_vs_Scopus.py
```

This script will:
1. Fetch authors from IRIS with ORCID and Scopus IDs
2. Retrieve works from IRIS, OpenAlex, and Scopus for each author
3. Compare coverage and identify missing works
4. Generate comprehensive coverage statistics
5. Save results to a JSON file

**Configuration options** (at the top of the script):
- `PRINT_NOT_MATCHED_WORKS`: Print titles of unmatched works
- `SAVE_RESULTS_TO_FILE`: Save results to JSON file
- `EXTRACT_STATS_ONLY`: Load results from file and extract statistics only

## 📦 Modules

### `utilities/db_utils.py`
Database utility functions for MySQL operations:
- `test_connection()`: Test and establish database connection
- `execute_query()`: Execute SELECT queries
- `execute_insert()`: Execute INSERT queries
- `execute_query_with_connection()`: Execute queries with existing connection

### `utilities/file_utils.py`
File I/O utilities:
- `write_json_to_file()`: Write data to JSON files
- `read_json_from_file()`: Read data from JSON files
- `parse_author_pairs()`: Parse author strings into name pairs

### `utilities/sim_lib.py`
Similarity calculation functions:
- `similarity_titles()`: Calculate Jaccard similarity between titles
- `author_similarity()`: Calculate similarity between author names
- `similarity_authors()`: Calculate similarity between author lists (greedy matching)
- `similarity_years()`: Calculate similarity between publication years

### Statistics Modules
- `authors_matching/stats_utils.py`: Author matching statistics
- `works_matching/stats_utils.py`: Work matching statistics
- `works_coverage/coverage_stats_utils.py`: Coverage comparison statistics

## 📊 Dependencies

See `requirements.txt` for the complete list. Main dependencies:

- `mysql-connector-python`: MySQL database connectivity
- `requests`: HTTP library for API calls

Standard library modules used:
- `os`, `sys`, `time`, `json`, `re`, `math`
- `datetime`, `collections`, `pathlib`, `decimal`

## 🔒 Security Notes

- **Never commit `.env` file**: The `.env` file contains sensitive database credentials and is already in `.gitignore`
- **Database credentials**: Keep your database credentials secure and never share them
- **API keys**: If you add API keys in the future, store them in `.env` and never commit them

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or issues, please open an issue on the repository.

---

**Note**: This project is designed for use with the IRIS database at Politecnico di Torino. Adaptations may be needed for other institutional repositories.

