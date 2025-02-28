"""Path utilities for SQLite-RX."""
import os
import logging
from pathlib import Path
from typing import Union, Optional

LOG = logging.getLogger(__name__)

def resolve_database_path(path: Union[str, bytes, Path], 
                         data_directory: Optional[Union[str, Path]] = None) -> Union[str, bytes, Path]:
    """
    Resolve a database path, handling relative paths, absolute paths, and memory databases.
    
    Args:
        path: The database path (can be string, bytes, or Path)
        data_directory: Optional base directory for relative paths
        
    Returns:
        The resolved path in the same type as the input path
    """
    # Handle :memory: database
    if path == ":memory:":
        return path
        
    # Handle None or empty paths
    if not path:
        return path
        
    # No data directory specified, return original path
    if not data_directory:
        return path
        
    # Convert to Path object for consistent handling
    original_type = type(path)
    is_bytes = isinstance(path, bytes)
    
    try:
        # Convert bytes to string if needed
        if is_bytes:
            path_str = path.decode()
        else:
            path_str = str(path)
            
        # Convert to Path objects
        path_obj = Path(path_str)
        data_dir_obj = Path(data_directory)
        
        # Create data directory if it doesn't exist
        if not data_dir_obj.exists():
            LOG.info(f"Creating data directory: {data_dir_obj}")
            data_dir_obj.mkdir(parents=True, exist_ok=True)
        
        # If path is absolute, use it directly
        if path_obj.is_absolute():
            resolved = path_obj
        else:
            # Resolve relative path against data directory
            resolved = data_dir_obj / path_obj
            
        # Return in the original type
        if is_bytes:
            return str(resolved).encode()
        elif original_type == str:
            return str(resolved)
        else:
            return resolved
            
    except Exception as e:
        LOG.warning(f"Error resolving database path '{path}': {e}")
        return path  # Return original path if resolution fails
