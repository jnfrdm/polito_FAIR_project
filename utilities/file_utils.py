#!/usr/bin/env python3
"""
File utility functions for reading and writing files
"""

import json
from decimal import Decimal


def default_serializer(obj):
    """
    Default serializer for JSON encoding of special types.
    
    Args:
        obj: Object to serialize
        
    Returns:
        Serialized representation of the object
    """
    if isinstance(obj, Decimal):
        return int(obj)  # or str(obj) if you prefer string
    return str(obj)


def write_json_to_file(data, file_path, indent=4, ensure_ascii=False, default=None, cursor=None, conn=None):
    """
    Write data to a JSON file with error handling.
    Closes database connections and exits if file writing fails.
    
    Args:
        data: Data to write (will be serialized to JSON)
        file_path (str): Path to the output file
        indent (int): JSON indentation level (default: 4)
        ensure_ascii (bool): Whether to ensure ASCII encoding (default: False)
        default (callable): Custom serializer function (default: default_serializer)
        cursor: Database cursor (optional, used for cleanup on error)
        conn: Database connection (optional, used for cleanup on error)
        
    Returns:
        bool: True if successful
    """
    if default is None:
        default = default_serializer
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent, default=default)
            print(f"Results written to {file_path}\n\n")
            return True
    except IOError as e:
        print(f"Error writing to file: {e}")
        if cursor and conn:
            cursor.close()
            conn.close()
        exit(1)


def read_json_from_file(file_path, cursor=None, conn=None):
    """
    Read data from a JSON file with error handling.
    Closes database connections and exits if file reading fails.
    
    Args:
        file_path (str): Path to the JSON file to read
        cursor: Database cursor (optional, used for cleanup on error)
        conn: Database connection (optional, used for cleanup on error)
        
    Returns:
        dict or list: Parsed JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except IOError as e:
        print(f"Errore nella lettura del file: {e}")
        if cursor and conn:
            cursor.close()
            conn.close()
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing del JSON: {e}")
        if cursor and conn:
            cursor.close()
            conn.close()
        exit(1)


def parse_author_pairs(stringa_autori):
    """
    Parse author string and extract name/surname pairs.
    
    Parses a semicolon-separated string of authors where each author
    can be in the format "surname, name" or just "name".
    
    Args:
        stringa_autori (str): String containing authors separated by semicolons
        
    Returns:
        list: List of tuples (nome, cognome) where nome is the first name
              and cognome is the surname. If no comma is present, cognome is empty string.
    """
    coppie_raw = stringa_autori.split(';')
    coppie_autori = []
    for p in coppie_raw:
        p = p.strip()              
        if not p:   
            continue
        if ',' in p:
            cognome, nome = p.split(',', 1)  
            coppie_autori.append((nome.strip(), cognome.strip()))
        else:
            coppie_autori.append((p.strip(), ""))
    coppie_autori = [f"{elem[0]} {elem[1]}" for elem in coppie_autori] # Format: "Nome Cognome"
    return coppie_autori

