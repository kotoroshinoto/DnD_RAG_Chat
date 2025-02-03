from collections import deque, defaultdict, OrderedDict
from beartype.typing import Deque, Tuple, get_origin, get_args, Any, Callable, Optional, Union, List, Dict, DefaultDict, OrderedDict, Type, Generic
from beartype.door import TypeHint, infer_hint, is_bearable
from beartype.cave import IterableType, NoneType, StrType, HintGenericSubscriptedType
from beartype import beartype


@beartype
def simplify_type(t_: Any) -> Any:
    """Simplifies a type hint to its base type (origin) or returns itself if not generic."""
    if isinstance(t_, TypeHint):
        t_ = t_.hint  # Unwrap TypeHint first
    
    origin = get_origin(t_)
    
    return origin if origin is not None else t_


@beartype
def get_base_name(btth_: Any) -> str:
    simple_type = simplify_type(btth_)
    # print(f'[get_base_name]: {btth_}: {simple_type.__name__}')
    return simple_type.__name__


class TypeHintTreeNode:
    def __init__(self, name: str) -> None:
        """Initialize a tree node with a name and an ordered dictionary of children."""
        self.name: str = name  # The base name (e.g., "List", "Dict")
        self.next_i = 0
        self.children: OrderedDict[Tuple[int, str], 'TypeHintTreeNode'] = OrderedDict()
    
    def __getitem__(self, key_type: Any) -> 'List[TypeHintTreeNode]':
        if is_bearable(key_type, Tuple[int,str]):
            return [self.children[key_type]]
        use_key = get_base_name(key_type)
        collected_children = []
        for _, v in self.children.items():
            if v.name == use_key:
                collected_children.append(v)
        return collected_children

    def add_child(self, child_type: Union[str, TypeHint[Any], HintGenericSubscriptedType, Type]) -> 'Tuple[int, TypeHintTreeNode]':
        """Adds a child node using the full type hint as the key but stores the base name."""
        # child_key = self.type_to_str_repr(child_type)
        if is_bearable(child_type, str):
            base_name = child_type
        else:
            base_name = get_base_name(child_type)
        new_key = (self.next_i, base_name)
        self.next_i += 1
        self.children[new_key] = TypeHintTreeNode(base_name)
        return new_key[0],self.children[new_key]
    
    def __repr__(self) -> str:
        """Provide a more formal representation for debugging."""
        if len(self.children) > 0:
            child_repr_list = [f'{i}, {repr(v)}' for i,v in self.children.items()]
            return f"TypeHintTreeNode(name={self.name!r}, children=[{','.join(child_repr_list)}])"
        else:
            return f"TypeHintTreeNode(name={self.name!r})"
    
    def __str__(self) -> str:
        """Provide a human-readable string representation."""
        if len(self.children) == 0:
            return self.name
        child_names = ','.join(str(child) for child in self.children.values())
        return f"{self.name}[{child_names}]"
    

def typehint_to_str(th):
    bt_th = TypeHint(th)
    # print(bt_th)
    tree: TypeHintTreeNode = TypeHintTreeNode(get_base_name(th))
    stk: Deque[Tuple[Union[TypeHint, list[Any]], TypeHintTreeNode]] = deque()
    stk.appendleft((bt_th, tree))
    i = 0
    while stk:
        # print(f'\n{i}th loop')
        i += 1
        vals:Tuple[Union[TypeHint, list[Any]], TypeHintTreeNode] = stk.popleft()
        if not is_bearable(vals[0], TypeHint):
            typ:List[Any] = vals[0]
            node: TypeHintTreeNode = vals[1]
            args = typ
            # print(f'name: ""')
            # print(f'type: list of types: {args}')
            # print(f'args: {args}')
        else:
            typ: TypeHint[Any] = vals[0]
            node: TypeHintTreeNode = vals[1]
            args = get_args(typ.hint)
            # print(f'name: {node.name}')
            # print(f'type: {typ}')
            # print(f'args: {args}')
        if node.name == 'Union':
            def type_sorting_key(type_ref: Any)->str:
                return get_base_name(type_ref).lower()
            args = sorted(args, key=type_sorting_key)
        for arg in args:
            if isinstance(arg, list):
                # print(f"Arg is Iterable Type: {type(arg)}, {arg}")
                arg_node_index, arg_node = node.add_child("")
                stk.appendleft((arg, arg_node))
            else:
                # print(f"Arg is a type/class: {type(arg)}, {arg}")
                arg_th = TypeHint(arg)
                simple_type = simplify_type(arg)
                # print(f"Simplified type: {simple_type}")
                arg_node_index, arg_node = node.add_child(simple_type)
                stk.appendleft((arg_th, arg_node))
        # break
    return str(tree)


# print(typehint_to_str(Callable[[str, bytes, bool], Optional[Union[int,float]]]))
# import abc
# print(typehint_to_str(List[Dict[Union[str, int, bool], Union[abc.ABC, bool, complex, deque, float, int,str]]]))
# print(typehint_to_str(Callable[[int,str], bool]))