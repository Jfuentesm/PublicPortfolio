# src/backend/canvas/node_processor.py
"""
node_processor.py

This module provides functionality to process nodes and their relationships
within the canvas. It supports operations such as grouping nodes and validating
connections between nodes.
"""

from typing import List, Dict, Any


class NodeProcessor:
    """
    Processes nodes and connections in the canvas layout.
    """

    def group_nodes(self, nodes: List[Dict[str, Any]], group_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group nodes based on a specific key.

        Args:
            nodes (List[Dict[str, Any]]): List of node dictionaries.
            group_key (str): The key to group nodes by.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary with group_key values as keys and lists of nodes as values.
        """
        grouped = {}
        for node in nodes:
            key = node.get(group_key, "ungrouped")
            grouped.setdefault(key, []).append(node)
        return grouped

    def validate_connection(self, source_node: Dict[str, Any], target_node: Dict[str, Any], connection_type: str) -> bool:
        """
        Validate a connection between two nodes based on connection type.

        Args:
            source_node (Dict[str, Any]): The source node data.
            target_node (Dict[str, Any]): The target node data.
            connection_type (str): Type of connection (e.g., "arrow", "line").

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        # Example validation: ensure nodes are not the same and connection type is supported
        if source_node.get("id") == target_node.get("id"):
            return False
        if connection_type not in ["arrow", "line"]:
            return False
        return True
