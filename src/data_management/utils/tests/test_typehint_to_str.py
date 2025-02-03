import pytest
from typing import List, Dict, Tuple, Callable, Union, Optional
from beartype.cave import NoneType
from beartype.typing import Any

from data_management.utils.typehint_to_str import typehint_to_str

@pytest.mark.parametrize(
    "typehint, expected",
    [
        (int,'int'),
        (str,'str'),
        (bool,'bool'),
        (float,'float'),
        (complex,'complex'),
        (bytes,'bytes'),
        (bytearray,'bytearray'),
        (memoryview,'memoryview'),
    ]
)
def test_basic_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Optional[int],'Union[int,NoneType]'),
        (Optional[Union[int, str]],'Union[int,NoneType,str]'),
    ]
)
def test_optional_types(typehint, expected):
    assert typehint_to_str(typehint) == expected
    


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Union[int, str],'Union[int,str]'),
        (Union[int, str, bool],'Union[bool,int,str]'),
    ]
)
def test_union_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (List[int],'list[int]'),
        (List[Union[int, str]],'list[Union[int,str]]'),
        (List[List[int]],'list[list[int]]'),
        
    ]
)
def test_list_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Tuple[int, str],'tuple[int,str]'),
        (Tuple[Union[int, str], bool],'tuple[Union[int,str],bool]'),
        (Tuple[int, str, bool],'tuple[int,str,bool]'),
    ]
)
def test_tuple_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Callable[[int, str], bool],'Callable[[int,str],bool]'),
        (Callable[[str], Union[int, float]],'Callable[[str],Union[float,int]]'),
        (Callable[[int], Optional[str]],'Callable[[int],Union[NoneType,str]]'),
    ]
)
def test_callable_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Dict[str, int],'dict[str,int]'),
        (Dict[str, Union[int, str]],'dict[str,Union[int,str]]'),
    ]
)
def test_dict_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (List[Dict[str, Tuple[int, str]]],'list[dict[str,tuple[int,str]]]'),
        (Dict[str, List[Union[int, str]]],'dict[str,list[Union[int,str]]]'),
        (Callable[[List[Union[int, str]]], Dict[str, int]],'Callable[[list[Union[int,str]]],dict[str,int]]'),

    ]
)
def test_nested_types(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Optional[None],'NoneType'),
        (Union[None, int],'Union[int,NoneType]'),
        
    ]
)
def test_optional_with_none(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Any,'Any'),
        (Callable,'Callable'),
        (List,'list'),

    ]
)
def test_edge_cases(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (Callable[[str, bytes, bool], Union[int, float]],'Callable[[str,bytes,bool],Union[float,int]]'),
    ]
)
def test_complex_type(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (List[int], 'list[int]'),
        (Tuple[int, str], 'tuple[int,str]'),
        (Dict[str, Union[int, str]], 'dict[str,Union[int,str]]'),
        (Callable[[str], bool], 'Callable[[str],bool]'),
        (Optional[Union[int, float]], 'Union[float,int,NoneType]'),
        (Union[int, str, bool], 'Union[bool,int,str]'),
        (Optional[List[Dict[str, int]]], 'Union[list[dict[str,int]],NoneType]')
    ]
)
def test_various_typehints(typehint, expected):
    assert typehint_to_str(typehint) == expected


@pytest.mark.parametrize(
    "typehint, expected",
    [
        (List[Dict[str, List[Tuple[int, Optional[str]]]]],'list[dict[str,list[tuple[int,Union[NoneType,str]]]]]'),
    ]
)
# For testing deeply nested types
def test_deeply_nested_types(typehint, expected):
    assert typehint_to_str(typehint) == expected

