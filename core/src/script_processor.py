"""
===============================================================================
    Module Name: Script Processor
    Description:  This module provides the ScriptProcessor class, which handles 
                  the end-to-end processing of YAML files. The processing 
                  involves validating the file using the ScriptValidator and 
                  building a semantic tree with the SemanticTreeBuilder. The 
                  module is designed to capture and handle errors at each step 
                  and return structured error messages or a semantic tree in 
                  JSON format.

    Author:       Jerry Hung
    Email:        chiehlee.hung@gmail.com
    Created Date: 2024-08-08
    Last Updated: 2024-09-02
    Version:      1.0.2
    
    License:      Commercial License
                  This software is licensed under a commercial license. 
                  Redistribution and use in source and binary forms, with or 
                  without modification, are not permitted without explicit 
                  written permission from the author.

                  Unauthorized copying of this software, via any medium, is 
                  strictly prohibited.

    Usage:        Instantiate the `ScriptProcessor` class and call the `process`
                  method with the YAML file content as a string to validate the 
                  file and build the semantic tree. The output will be either a 
                  JSON string of the tree or a structured error message.

    Requirements: Python 3.10.12
                  
    Notes:        This module is part of the Script Validation and Processing 
                  system, version 1.0.0.
===============================================================================
"""

import json
from typing import Union, Dict, List
from enum import Enum
from loguru import logger  # 添加 loguru

from .script_validator import ScriptValidator, ValidationError
from .semantic_tree_builder import SemanticTreeBuilder
from .semantic_tree_executor import SemanticTreeExecutor


class ScriptProcessorError(Enum):
    FILE_VALIDATION_FAILED = ("P001", "File validation failed")
    TREE_BUILDING_FAILED = ("P002", "Tree building failed")
    EXECUTION_FAILED = ("P003", "Execution failed")
    UNKNOWN_ERROR = ("P004", "Unknown error")


class ScriptProcessor:
    def __init__(self):
        self.validator = ScriptValidator()
        self.tree_builder = SemanticTreeBuilder()

    def process_yml(self, file_content: str) -> Union[str, Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]]:
        try:
            logger.info("Validating YAML file content.")
            # Step 1: Validate the YAML file :)
            script_data = self.validator.validate_file(file_content)
            
            # Step 2: Build the semantic tree for each check in the script :)
            checks = []
            for check in script_data['checks']:
                logger.debug(f"Building tree for check ID: {check['id']}")
                tree = self.tree_builder.build_tree({
                    'id': check['id'],
                    'condition': check['condition'],
                    'rules': check['rules']
                })
                
                # Step 3: Check for errors during tree building :)
                if tree is None:
                    errors = self.tree_builder.get_errors()
                    logger.error("Tree building failed. Errors: {}", errors)
                    return {
                        "status": "error",
                        "error_code": ScriptProcessorError.TREE_BUILDING_FAILED.value[0],
                        "error_message": ScriptProcessorError.TREE_BUILDING_FAILED.value[1],
                        "details": errors
                    }
                checks.append(json.loads(self.tree_builder.tree_to_json(tree)))
            
            # Step 4: Return the JSON string of the tree if all checks passed :)
            result = {"checks": checks}
            logger.info("Semantic tree built successfully.")
            return json.dumps(result, separators=(',', ':'))
        
        except ValidationError as sve:
            logger.error("Validation failed. Errors: {}", sve.errors)
            return {
                "status": "error",
                "error_code": ScriptProcessorError.FILE_VALIDATION_FAILED.value[0],
                "error_message": ScriptProcessorError.FILE_VALIDATION_FAILED.value[1],
                "details": sve.errors
            }
        
        except Exception as e:
            logger.error("An unexpected error occurred: {}", str(e))
            return {
                "status": "error",
                "error_code": ScriptProcessorError.UNKNOWN_ERROR.value[0],
                "error_message": ScriptProcessorError.UNKNOWN_ERROR.value[1],
                "details": str(e)
            }
        
    def process_json(self, script_list: List[Dict[str, Union[str, List[str]]]]) -> Union[str, Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]]:
        try:
            logger.info("Processing JSON script list.")
            
            # Step 1: Validate the script list :)
            # self.validator.validate_json(script_list) # TODO: Implement JSON validation
            
            # Step 2: Build the semantic tree for each script in the script list :)
            checks = []
            for script in script_list:
                logger.debug(f"Building tree for script ID: {script['script_id']}")
                tree = self.tree_builder.build_tree({
                    'id': script['script_id'],
                    'condition': script.get('condition', ''),
                    'rules': script.get('rules', [])
                })
                
                # Step 3: Check for errors during tree building :)
                if tree is None:
                    errors = self.tree_builder.get_errors()
                    logger.error("Tree building failed. Errors: {}", errors)
                    return {
                        "status": "error",
                        "error_code": ScriptProcessorError.TREE_BUILDING_FAILED.value[0],
                        "error_message": ScriptProcessorError.TREE_BUILDING_FAILED.value[1],
                        "details": errors
                    }
                checks.append(json.loads(self.tree_builder.tree_to_json(tree)))
            
            # Step 4: Return the JSON string of the tree if all checks passed :)
            result = {"checks": checks}
            logger.info("Semantic tree built successfully.")
            return json.dumps(result, separators=(',', ':'))
        
        except json.JSONDecodeError as je:
            logger.error("JSON decoding failed. Errors: {}", str(je))
            return {
                "status": "error",
                "error_code": ScriptProcessorError.FILE_VALIDATION_FAILED.value[0],
                "error_message": "JSON decoding failed",
                "details": str(je)
            }
        
        except ValidationError as sve:
            logger.error("Validation failed. Errors: {}", sve.errors)
            return {
                "status": "error",
                "error_code": ScriptProcessorError.FILE_VALIDATION_FAILED.value[0],
                "error_message": ScriptProcessorError.FILE_VALIDATION_FAILED.value[1],
                "details": sve.errors
            }
        
        except Exception as e:
            logger.error("An unexpected error occurred: {}", str(e))
            return {
                "status": "error",
                "error_code": ScriptProcessorError.UNKNOWN_ERROR.value[0],
                "error_message": ScriptProcessorError.UNKNOWN_ERROR.value[1],
                "details": str(e)
            }

    def executor(self, tree_json: str, ssh_details: Dict[str, Union[str, int]]) -> Dict[str, Union[str, Dict]]:
        try:
            logger.info("Executing semantic tree.")
            # Step 1: Convert JSON string to a Python dictionary for execution :)
            semantic_tree = json.loads(tree_json)

            # Step 2: Initialize the SemanticTreeExecutor with SSH details :)
            executor = SemanticTreeExecutor(
                ip=ssh_details['ip'],
                username=ssh_details['username'],
                password=ssh_details['password'],
                port=ssh_details.get('port', 22)
            )

            # Step 3: Execute the semantic tree :)
            execution_result = executor.execute_tree(semantic_tree)

            # Step 4: Check for success or handle errors in execution :)
            if not execution_result.success:
                logger.error("Execution failed. Results: {}", execution_result.results)
                return {
                    "status": "error",
                    "executed_count": execution_result.executed_count,
                    "error_code": ScriptProcessorError.EXECUTION_FAILED.value[0],
                    "error_message": execution_result.error or ScriptProcessorError.EXECUTION_FAILED.value[1],
                    "details": execution_result.results
                }

            # Step 5: Return the successful execution results :)
            logger.info("Execution completed successfully.")
            return {
                "status": "success",
                "executed_count": execution_result.executed_count,
                "results": execution_result.results
            }

        except Exception as e:
            logger.error("An unexpected error occurred: {}", str(e))
            return {
                "status": "error",
                "error_code": ScriptProcessorError.UNKNOWN_ERROR.value[0],
                "error_message": ScriptProcessorError.UNKNOWN_ERROR.value[1],
                "details": str(e)
            }
