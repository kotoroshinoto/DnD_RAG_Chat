import pytest
from typing import List, Dict, Union
from functools import lru_cache
from collections import deque
from beartype.door import TypeHint, is_subhint, is_bearable
from beartype.typing import List, Tuple, Any, Deque, get_origin, Callable, Optional, get_args
from beartype.cave import IterableType
from itertools import product
from data_management.utils.typehint_distance import typehint_distance
from data_management.utils.typehint_to_str import typehint_to_str


def gen_id(value):
    if is_bearable(value, Union[int, float]):
        return str(value)
    else:
        return typehint_to_str(value)

# Assuming the function `score_match` is defined as in your example
pos_inf = float('inf')
@pytest.mark.parametrize("check_type, candidate_type, expected_complexity, expected_specificity", [
        # Basic types
    (int, int, 0, 0),
    (int, float, float('inf'), float('inf')),
    (str, float, float('inf'), float('inf')),
    (int, Union[int, str], 0, 1),  # Union vs specific
    
    # Matching Unions
    (Union[int, str], Union[int, str], 0, 0),  # Exact match
    (Union[int, str], Union[str, float], float('inf'), float('inf')),  # Incompatible
    (Union[int, str], float, float('inf'), float('inf')),  # No match
    (Union[int, float], Union[float, str], float('inf'), float('inf')),  # No match
    
    # Matching Generics
    (List[int], List[int], 0, 0),  # Exact match
    (List[int], List[float], float('inf'), float('inf')),  # No match
    (List[int], List[Union[str, int]], 0, 1),  # Union vs specific
    
    # Nested types
    (List[Dict[str, int]], List[Dict[str, int]], 0, 0),  # Exact match
    (List[Dict[str, int]], List[Dict[str, str]], float('inf'), float('inf')),  # Incompatible types
    (List[Dict[str, int]], List[Dict[str, Union[str, int]]], 0, 1),  # Union vs specific
    
    # Matching with complex unions
    (List[int], Union[List[int], Dict[str, int]], 0, 1),  # Union match
    (Dict[str, str], Union[List[int], Dict[str, int]], float('inf'), float('inf')),  # Incompatible types
    (float, Union[List[int], Dict[str, int]], float('inf'), float('inf')),  # Incompatible types
    
    # Complex nested generics
    (List[Union[Dict[str, int], Dict[str, str]]], List[Union[Dict[str, int], Dict[str, str]]], 0, 0),
    (List[Union[Dict[str, int], Dict[str, str]]], List[Union[Dict[str, str], Dict[str, float]]], float('inf'), float('inf')),
    
    # Unions with different nesting levels
    (Union[List[int], Dict[str, int]], List[int], float('inf'), float('inf')),
    (Union[List[int], Dict[str, int]], Dict[str, str], float('inf'), float('inf')),
    
    # Edge cases
    (List[Dict[str, int]], Dict[str, int], float('inf'), float('inf')),
    (List[Dict[str, int]], List[str], float('inf'), float('inf')),
    (Dict[str, int], Dict[str, int], 0, 0),
    (Dict[str, int], Dict[str, str], float('inf'), float('inf')),
    (List[Dict[str, int]], List[Dict[str, float]], float('inf'), float('inf')),
], ids=gen_id)
def test_score_match(check_type, candidate_type, expected_complexity, expected_specificity):
    complexity, specificity = typehint_distance(check_type, candidate_type)
    assert complexity == expected_complexity, f"Expected complexity {expected_complexity} but got {complexity} for {check_type} vs {candidate_type}"
    assert specificity == expected_specificity, f"Expected specificity {expected_specificity} but got {specificity} for {check_type} vs {candidate_type}"
