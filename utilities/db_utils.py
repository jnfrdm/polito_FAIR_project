#!/usr/bin/env python3
"""
Database utility functions for MySQL operations
"""

import mysql.connector
from mysql.connector import Error, errorcode
import os
from pathlib import Path


def load_env_file():
    """
    Load environment variables from .env file.
    Looks for .env file in the project root directory.
    
    Returns:
        dict: Dictionary containing environment variables
    """
    # Get the project root directory (parent of utilities directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file = project_root / '.env'
    
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Split on first '=' sign
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    env_vars[key] = value
    else:
        # Fallback to system environment variables if .env doesn't exist
        env_vars = {
            'user': os.getenv('user', ''),
            'password': os.getenv('password', ''),
            'host': os.getenv('host', ''),
            'database': os.getenv('database', '')
        }
    
    return env_vars


def get_db_connection():
    """
    Create and return a MySQL database connection using environment variables.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object
        
    Raises:
        mysql.connector.Error: If connection fails
    """
    env = load_env_file()
    config = {
        'user': env['user'],
        'password': env['password'],
        'host': env['host'],
        'database': env['database'],
    }
    
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        raise mysql.connector.Error(f"Errore di connessione: {err}")


def test_connection():
    """
    Test database connection and return connection and cursor objects.
    Exits the program if connection fails.
    
    Returns:
        tuple: (connection, cursor) objects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Errore di connessione: {err}")
        exit(1)


def execute_query(query, params=None):
    """
    Execute a SELECT query and return results.
    
    Args:
        query (str): SQL SELECT query to execute
        params (tuple, optional): Parameters for parameterized query
        
    Returns:
        list: List of dictionaries containing query results
        
    Raises:
        mysql.connector.Error: If query execution fails
    """
    conn, cursor = test_connection()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        raise mysql.connector.Error(f"Errore nell'esecuzione della query: {err}")
    finally:
        cursor.close()
        conn.close()


def execute_insert(query, params):
    """
    Execute an INSERT query with parameters.
    
    Args:
        query (str): SQL INSERT query to execute
        params (tuple or list): Parameters for the INSERT query
        
    Returns:
        int: Number of affected rows
        
    Raises:
        mysql.connector.Error: If insert execution fails
    """
    conn, cursor = test_connection()
    try:
        cursor.execute(query, params)
        conn.commit()
        affected_rows = cursor.rowcount
        return affected_rows
    except mysql.connector.Error as err:
        conn.rollback()
        raise mysql.connector.Error(f"Errore nell'inserimento: {err}")
    finally:
        cursor.close()
        conn.close()


def execute_insert_many(query, params_list):
    """
    Execute multiple INSERT queries in a batch.
    
    Args:
        query (str): SQL INSERT query to execute
        params_list (list): List of parameter tuples/lists for batch insert
        
    Returns:
        int: Number of affected rows
        
    Raises:
        mysql.connector.Error: If batch insert execution fails
    """
    conn, cursor = test_connection()
    try:
        cursor.executemany(query, params_list)
        conn.commit()
        affected_rows = cursor.rowcount
        return affected_rows
    except mysql.connector.Error as err:
        conn.rollback()
        raise mysql.connector.Error(f"Errore nell'inserimento multiplo: {err}")
    finally:
        cursor.close()
        conn.close()


def get_connection_and_cursor():
    """
    Get a database connection and cursor that remain open for multiple operations.
    Useful when you need to perform multiple queries/inserts in a transaction.
    
    Returns:
        tuple: (connection, cursor) objects
        
    Raises:
        mysql.connector.Error: If connection or cursor creation fails
    """
    return test_connection()


def execute_query_with_connection(cursor, query, params=None, conn=None):
    """
    Execute a SELECT query using an existing cursor.
    This function does not close the connection, allowing for multiple operations.
    Closes connections and exits if query execution fails.
    
    Args:
        cursor: Existing database cursor
        query (str): SQL SELECT query to execute
        params (tuple, optional): Parameters for parameterized query
        conn: Database connection (optional, used for cleanup on error)
        
    Returns:
        list: List of dictionaries containing query results
    """
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Errore nell'esecuzione della query: {err}")
        if conn:
            cursor.close()
            conn.close()
        exit(1)


def execute_insert_with_connection(cursor, conn, query, params):
    """
    Execute an INSERT query with parameters using an existing connection and cursor.
    This function does not close the connection, allowing for multiple operations.
    
    Args:
        cursor: Existing database cursor
        conn: Existing database connection
        query (str): SQL INSERT query to execute
        params (tuple or list): Parameters for the INSERT query
        
    Returns:
        int: Number of affected rows
        
    Raises:
        mysql.connector.Error: If insert execution fails
    """
    try:
        cursor.execute(query, params)
        conn.commit()
        affected_rows = cursor.rowcount
        return affected_rows
    except mysql.connector.Error as err:
        conn.rollback()
        raise mysql.connector.Error(f"Errore nell'inserimento: {err}")

