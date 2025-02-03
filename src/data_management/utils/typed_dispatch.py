from collections import defaultdict
from functools import wraps
from types import MethodType

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
    DefaultDict
)
from beartype.door import (
    TypeHint,
    infer_hint
)

from data_management.utils.typehint_distance import typehint_distance
from data_management.utils.typehint_to_str import typehint_to_str
T = TypeVar('T')
R = TypeVar('R', bound=Optional[Any])
C = TypeVar('C', bound=Callable[..., R])



def typed_singledispatch(func: C) -> C:
    # This will store registered functions for specific types
    registry: Dict[TypeHint, Callable] = {}
    base_func = func  # Store the base function
    
    # Expose a dispatch method to manually dispatch based on type
    def dispatch(value: Optional[Any]) -> C:
        th_instance:TypeHint = TypeHint(infer_hint(value))
        matching_instances: DefaultDict[float, List[C]] = defaultdict(list)
        matching_types: DefaultDict[float, List[TypeHint]] = defaultdict(list)
        if th_instance in registry:
            return registry[th_instance]
        else:
            for values in registry.items():
                reg_th:TypeHint = values[0]
                func_:C = values[1]
                if th_instance.is_subhint(reg_th):  # Check if it's a subtype
                    dist = typehint_distance(type_=th_instance.hint, candidate=reg_th.hint)
                    matching_instances[dist].append(func_)
                    matching_types[dist].append(reg_th)
        if len(matching_instances) > 0:
            best_key_value = min(matching_instances.keys())
            best_matches = matching_instances[best_key_value]
            best_matches_types = matching_types[best_key_value]
            print(f"value to dispatch: {value}")
            print(f"inferred type: {typehint_to_str(th_instance.hint)}")
            print(f"Best Match Distance: {best_key_value}")
            print(f"{[typehint_to_str(x) for x in best_matches_types]}")
            if len(best_matches) == 1:
                return best_matches[0]
            else:
                raise TypeError(f"There were too many matching registrations: value:{value}, inferred_type:{typehint_to_str(th_instance.hint)}, matches:"
                          f"{[typehint_to_str(x) for x in best_matches_types]}")
        else:
            return base_func
            # raise TypeError(f"Could not find a registered type matching: {th_instance}; registered types:{registry.keys()}")
    
    # The base function, used when no type matches
    @wraps(func)
    def dispatcher(value, *args, **kwargs) -> R:
        return dispatch(value)(value, *args, **kwargs)
    
    # Register a function for a specific type
    def register(type_: Type) -> C:
        th_instance = TypeHint(type_)
        if th_instance in registry:
            raise ValueError(f"TypeHint: '{typehint_to_str(th_instance.hint)}' already registered")
        def wrapper(func_: C) -> C:
            registry[th_instance] = func_
            return func_
        
        return wrapper
        
    # Attach the `dispatch` method to the dispatcher
    dispatcher.dispatch = dispatch
    
    # Attach the `register` function to the dispatcher, so it can be used to register handlers
    dispatcher.register = register
    
    # Make the dispatcher callable by returning it as the function itself
    return dispatcher


def typed_singledispatchmethod(func: C) -> C:
    # This will store registered functions for specific types
    registry: Dict[TypeHint, Callable] = {}
    base_func = func  # Store the base function
    
    # Expose a dispatch method to manually dispatch based on type
    def dispatch(slf_or_cls:Any, value: Optional[Any]) -> C:
        th_instance:TypeHint = TypeHint(infer_hint(value))
        matching_instances: DefaultDict[float, List[C]] = defaultdict(list)
        matching_types: DefaultDict[float, List[TypeHint]] = defaultdict(list)
        if th_instance in registry:
            return registry[th_instance]
        else:
            for values in registry.items():
                reg_th:TypeHint = values[0]
                func_:C = values[1]
                if th_instance.is_subhint(reg_th):  # Check if it's a subtype
                    dist = typehint_distance(type_=th_instance.hint, candidate=reg_th.hint)
                    matching_instances[dist].append(func_)
                    matching_types[dist].append(reg_th)
        if len(matching_instances) > 0:
            best_key_value = min(matching_instances.keys())
            best_matches = matching_instances[best_key_value]
            best_matches_types = matching_types[best_key_value]
            print(f"value to dispatch: {value}")
            print(f"inferred type: {typehint_to_str(th_instance.hint)}")
            print(f"Best Match Distance: {best_key_value}")
            print(f"{[typehint_to_str(x) for x in best_matches_types]}")
            if len(best_matches) == 1:
                return best_matches[0]
            else:
                raise TypeError(f"There were too many matching registrations: value:{value}, inferred_type:{typehint_to_str(th_instance.hint)}, matches:"
                          f"{[typehint_to_str(x) for x in best_matches_types]}")
        else:
            return base_func
            # raise TypeError(f"Could not find a registered type matching: {th_instance}; registered types:{registry.keys()}")
    
    # The base function, used when no type matches
    @wraps(func)
    def dispatcher(slf_or_cls:Any, value:Optional[Any], *args, **kwargs) -> R:
        func = dispatch(slf_or_cls, value)
        if isinstance(func, classmethod):
            bound_func = MethodType(func.__func__, slf_or_cls)
        else:
            bound_func = MethodType(func, slf_or_cls)
        return bound_func(value, *args, **kwargs)
    
    # Register a function for a specific type
    def register(type_: Type) -> C:
        th_instance = TypeHint(type_)
        if th_instance in registry:
            raise ValueError(f"TypeHint: '{typehint_to_str(th_instance.hint)}' already registered")
        def wrapper(func_: C) -> C:
            registry[th_instance] = func_
            return func_
        
        return wrapper
        
    # Attach the `dispatch` method to the dispatcher
    dispatcher.dispatch = dispatch
    
    # Attach the `register` function to the dispatcher, so it can be used to register handlers
    dispatcher.register = register
    
    # Make the dispatcher callable by returning it as the function itself
    return dispatcher
