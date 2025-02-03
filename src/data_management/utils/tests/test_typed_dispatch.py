from collections import defaultdict
from functools import wraps

import pytest
from beartype import beartype
from beartype.typing import (
    Callable,
    Dict,
    List,
    Type,
    TypeVar,
    Optional,
    Any,
    Union,
    DefaultDict,
)
from beartype.door import (
    TypeHint,
    infer_hint
)
from data_management.utils.typed_dispatch import typed_singledispatch, typed_singledispatchmethod
# Example usage of the custom decorator


# The base function (generic handler)
@typed_singledispatch
def process(value):
    return 0

# Specialized function for handling integers
@process.register(int)
def _(value: int):
    return 1

# Specialized function for handling strings
@process.register(str)
def _(value: str):
    return 2

# Specialized function for handling lists
@process.register(list)
def _(value: list):
    return 3

@process.register(list[int])
def _(value: list[int]):
    return 4

@process.register(list[str])
def _(value: list[str]):
    return 5

@process.register(list[Union[int,str]])
def _(value: list[Union[int,str]]):
    return 6

class TypedSingleDispatchMethodClassTester:
    def __init__(self):
        pass
    
    @typed_singledispatchmethod
    def process(self, value):
        return 7
    
    # Specialized function for handling integers
    @process.register(int)
    def _(self, value: int):
        return 8
    
    # Specialized function for handling strings
    @process.register(str)
    def _(self, value: str):
        return 9
    
    # Specialized function for handling lists
    @process.register(list)
    def _(self, value: list):
        return 10
    
    @process.register(list[int])
    def _(self, value: list[int]):
        return 11
    
    @process.register(list[str])
    def _(self, value: list[str]):
        return 12
    
    @process.register(list[Union[int, str]])
    def _(self, value: list[Union[int, str]]):
        return 13
    
    @typed_singledispatchmethod
    @classmethod
    def classprocess(cls, value):
        return 14
    
    # Specialized function for handling integers
    @classprocess.register(int)
    @classmethod
    def _(cls, value: int):
        return 15
    
    # Specialized function for handling strings
    @classprocess.register(str)
    @classmethod
    def _(cls, value: str):
        return 16
    
    # Specialized function for handling lists
    @classprocess.register(list)
    @classmethod
    def _(cls, value: list):
        return 17
    
    @classprocess.register(list[int])
    @classmethod
    def _(cls, value: list[int]):
        return 18
    
    @classprocess.register(list[str])
    @classmethod
    def _(cls, value: list[str]):
        return 19
    
    @classprocess.register(list[Union[int, str]])
    @classmethod
    def _(cls, value: list[Union[int, str]]):
        return 20


@pytest.mark.parametrize(
        "dispatch_value, return_value",
        [
                (42, 1),
                ("hello", 2),
                ([[],[]], 3),
                ([1,2,3], 4),
                (['a', 'b', 'c'],5),
                (['a', 'b', 'c', 1],6),
                ([3.14, 0])
        ]
)
def test_typed_dispatch(dispatch_value, return_value):
    assert process(dispatch_value) == return_value


@pytest.mark.parametrize(
        "dispatch_value, return_value",
        [
                (42, 8),
                ("hello", 9),
                ([[],[]], 10),
                ([1,2,3], 11),
                (['a', 'b', 'c'],12),
                (['a', 'b', 'c', 1],13),
                ([3.14, 7])
        ]
)
def test_typed_dispatchmethod(dispatch_value, return_value):
    obj:TypedSingleDispatchMethodClassTester = TypedSingleDispatchMethodClassTester()
    assert obj.process(dispatch_value) == return_value
    

@pytest.mark.parametrize(
        "dispatch_value, return_value",
        [
                (42, 15),
                ("hello", 16),
                ([[],[]], 17),
                ([1,2,3], 18),
                (['a', 'b', 'c'],19),
                (['a', 'b', 'c', 1],20),
                ([3.14, 14])
        ]
)
def test_typed_dispatchclassmethod(dispatch_value, return_value):
    obj: TypedSingleDispatchMethodClassTester = TypedSingleDispatchMethodClassTester()
    assert obj.classprocess(dispatch_value) == return_value

# Test with different types
# process(42)        # Will use the `int` registered function
# process("hello")   # Will use the `str` registered function
# process([1, 2, 3]) # Will use the `list` registered function
# process(['a', 'b', 'c'])
# process(['a', 'b', 'c', 1])
# process(3.14)      # Will use the default function (no specific handler for `float`)

