"""
===============================================================================
    Name: Main Script Processor
    Description:  This script serves as the entry point for processing YAML 
                  files using the `ScriptProcessor` class. It reads the YAML 
                  content from a file, validates the structure, builds a 
                  semantic tree, and outputs the result. The script handles 
                  errors gracefully, logging detailed messages and exiting 
                  with appropriate status codes in case of failure.

    Author:       Jerry Hung
    Email:        chiehlee.hung@gmail.com
    Created Date: 2024-08-08
    Last Updated: 2024-09-11
    Version:      1.0.2
    
    License:      Commercial License
                  This software is licensed under a commercial license. 
                  Redistribution and use in source and binary forms, with or 
                  without modification, are not permitted without explicit 
                  written permission from the author.

                  Unauthorized copying of this software, via any medium, is 
                  strictly prohibited.

    Usage:        Run this script with the path to a YAML file as an argument:
                      $ python main.py <path_to_yml_file>

                  The script will validate the YAML file and generate a 
                  semantic tree in JSON format if successful. If errors occur, 
                  detailed logs will be printed, and the script will exit with 
                  a non-zero status code.

    Requirements: Python 3.10.12
                  
    Notes:        This script is part of the Script Validation and Processing 
                  system, version 1.0.0.
===============================================================================
"""

import sys
import os
from datetime import datetime
from loguru import logger
from script_processor import ScriptProcessor

# Create a 'logs' directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Generate a timestamp for the log file name
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(log_dir, f"log_{current_time}.log")

# Configure loguru to log to both stderr and the newly created log file
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add(log_file, format="{time} {level} {message}", level="DEBUG", rotation="2 MB", compression="zip")

def main(file_path: str, ssh_details: dict):
    try:
        # Step 1: Read the YAML file content
        with open(file_path, "r") as file:
            file_content = file.read()

        # Step 2: Initialize ScriptProcessor
        processor = ScriptProcessor()

        # Step 3: Process the file content to generate the semantic tree JSON
        tree_json = processor.process(file_content)

        # Step 4: Check if processing resulted in an error
        if isinstance(tree_json, dict) and tree_json.get("status") == "error":
            # Log the error details if processing failed
            logger.error(f"Error Code: {tree_json.get('error_code')}")
            logger.error(f"Error Message: {tree_json.get('error_message')}")
            logger.error(f"Details: {tree_json.get('details')}")
            sys.exit(1)
        else:
            # Log the generated tree JSON string if processing succeeded
            logger.info("Generated Tree JSON:")
            logger.debug(tree_json)

        # Step 5: Execute the semantic tree using the executor method
        result = processor.executor(tree_json, ssh_details)

        # Step 6: Check and log the execution result
        if isinstance(result, dict) and result.get("status") == "error":
            # Log the error details if execution failed
            logger.error(f"Error Code: {result.get('error_code')}")
            logger.error(f"Error Message: {result.get('error_message')}")
            logger.error(f"Details: {result.get('details')}")
            sys.exit(1)
        else:
            # Log the execution results if succeeded
            logger.info("Execution Results:")
            logger.debug(result)

    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
        sys.exit(2)
    except KeyError as e:
        logger.error(f"Missing required SSH detail: {str(e)}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        logger.info("Usage: python main.py <path_to_yml_file> <hostname> <username> <password> <port>")
        sys.exit(5)
    else:
        file_path = sys.argv[1]
        ssh_details = {
            'hostname': sys.argv[2],
            'username': sys.argv[3],
            'password': sys.argv[4],
            'port': int(sys.argv[5])
        }
        main(file_path, ssh_details)
