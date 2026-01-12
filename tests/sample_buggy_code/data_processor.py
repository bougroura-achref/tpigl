"""
Data Processor Module.

This module provides tools for loading, processing, and saving data.
"""

import json
from typing import Any, Dict, List, Optional, Union

# Constants
MAX_VALUE = 100
MIN_VALUE = 0
THRESHOLD = 50

def load_data(filepath: str) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        parsed JSON data.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(filepath: str, data: Any) -> None:
    """
    Save data to a file as JSON.
    
    Args:
        filepath: Path to the output file.
        data: Data to save.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def process_items(items: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    Process a list of numeric items based on their value.
    
    Args:
        items: List of numbers.
        
    Returns:
        List of processed numbers.
    """
    result = []
    for i in items:
        if i > MAX_VALUE:
            result.append(i * 0.5)
        elif i > THRESHOLD:
            result.append(i * 0.75)
        else:
            result.append(i)
    return result

class DataProcessor:
    """Class for managing data loading, processing, and saving."""
    
    def __init__(self) -> None:
        """Initialize DataProcessor."""
        self.data: Optional[Dict[str, Any]] = None
        self.processed: bool = False
        self.config: Dict[str, int] = {
            "max": MAX_VALUE,
            "min": MIN_VALUE,
            "threshold": THRESHOLD
        }
    
    def load(self, path: str) -> bool:
        """
        Load data into the processor.
        
        Args:
            path: File path to load from.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.data = load_data(path)
            return True
        except (IOError, json.JSONDecodeError):
            return False
    
    def process(self) -> Optional[List[Union[int, float]]]:
        """
        Process the loaded data values using the standard processing rules.
        
        Returns:
            List of processed values or None if no data loaded.
        """
        if self.data is None:
            return None
            
        values = []
        for key in self.data:
            value = self.data[key]
            if isinstance(value, (int, float)):
                values.append(value)
        
        # Use the standalone function for consistent logic
        result = process_items(values)
        self.processed = True
        return result
    
    def save(self, path: str) -> bool:
        """
        Save the current data state.
        
        Args:
            path: File path to save to.
             
        Returns:
            True if successful, False otherwise.
        """
        if not self.processed:
            return False
            
        try:
            save_data(path, self.data)
            return True
        except IOError:
            return False

def main() -> None:
    """Example usage of DataProcessor."""
    dp = DataProcessor()
    if dp.load("data.json"):
        dp.process()
        dp.save("output.json")

if __name__ == "__main__":
    main()
