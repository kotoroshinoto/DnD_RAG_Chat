import click
from collections import deque
from functools import lru_cache
from itertools import product

from beartype import beartype
from beartype.door import TypeHint, UnionTypeHint, is_subhint
from beartype.typing import Tuple, TypeVar, Any, get_origin, Deque, List

from data_management.utils.typehint_to_str import simplify_type, get_base_name

T = TypeVar('T')


@beartype
def typehint_distance(type_: T, candidate: T) -> Tuple[float, float]:
    """
    Score the specificity of a type match based on how many `Any` elements
    are used and how closely the types match.
    """
    def simplify_hint(th: T)-> T:
        th_origin = get_origin(th)
        if th_origin is None:
            return th
        else:
            return th_origin
            
    check_th:TypeHint[Any] = TypeHint(type_)
    cand_th:TypeHint[Any] = TypeHint(candidate)
    
    if not cand_th.is_superhint(check_th):
        return float('inf'), float('inf')
    
    num_any_matches:float = 0.0
    num_extra_types:float = 0.0
    
    stk:Deque[Tuple[TypeHint[Any],TypeHint[Any]]] = deque([(check_th, cand_th)])
    
    @lru_cache
    def compute_iter_distance(chk_:TypeHint[Any], cnd_:TypeHint[Any]) -> Tuple[float, float]:
        num_any_matches_:float = 0.0
        num_extra_types_:float = 0.0
        tmp:Tuple[TypeHint[Any], List[Any]] = simplify_hint(chk.hint), chk.args
        chk_th = tmp[0]
        chk_origin:TypeHint = simplify_hint(chk_th)
        chk_args:List[Any] = tmp[1]
        tmp = simplify_hint(cnd.hint), cnd.args
        cnd_th = tmp[0]
        cnd_origin:TypeHint = simplify_hint(cnd_th)
        cnd_args:List[Any] = tmp[1]
        
        # print(f"Comparing {chk_origin} to {cnd_origin}")
        if chk_origin == Any and cnd_origin == Any:
            pass
        elif chk_origin != Any and cnd_origin == Any:
            num_any_matches_ += 1.0
        elif not is_subhint(chk_origin, cnd_origin):
            # print("is not subhint")
            num_extra_types_ += 1
            # if they do not match and aren't compatible, there is nothing to add to the stack
        else:
            # print("is subhint")
            chk_is_union = isinstance(chk, UnionTypeHint)
            cnd_is_union = isinstance(cnd, UnionTypeHint)
            # print(f"Chk is union?: {chk_is_union}")
            # print(f"Cnd is union?: {cnd_is_union}")
            if cnd_is_union and chk_is_union:
                # print("Candidate and Check are both union")
                chk_arg_set = set([TypeHint(x) for x in chk_args])
                cnd_arg_set = set([TypeHint(x) for x in cnd_args])
                chk_matched_once = set()
                cnd_matched_once = set()
                matched_items = set()
                for vals_ in product(chk_args, cnd_args):
                    chk_arg: TypeHint[Any] = TypeHint(vals_[0])
                    cnd_arg: TypeHint[Any] = TypeHint(vals_[1])
                    if chk_arg.is_subhint(cnd_arg):
                        chk_matched_once.add(chk_arg)
                        cnd_matched_once.add(cnd_arg)
                        matched_items.add((chk_arg, cnd_arg))
                chk_only = chk_arg_set - chk_matched_once
                cnd_only = cnd_arg_set - cnd_matched_once
                print(f"chk_arg_set: {chk_arg_set}")
                print(f"cnd_arg_set: {cnd_arg_set}")
                print(f"chk_matched_once: {chk_matched_once}")
                print(f"cnd_matched_once: {cnd_matched_once}")
                print(f"chk_only: {chk_only}")
                print(f"cnd_only: {cnd_only}")
                num_any_matches_ += len(chk_only) + len(cnd_only)
                # add pairwise tuples to the stack across both unions
                for chk_arg, cnd_arg in matched_items:
                    stk.appendleft((chk_arg, cnd_arg))
            elif cnd_is_union and not chk_is_union:
                # print("Candidate is union, Check is not")
                # this might match; pair all the union arg types with the non-union type
                for cnd_arg in cnd_args:
                    # print(f"Pairing {chk} and {cnd_arg}")
                    stk.appendleft((chk, TypeHint(cnd_arg)))
            elif len(chk_args) >= 1 and len(cnd_args) >= 1:
                # print("Candidate is not union; args for both typehints >= 1")
                if len(chk_args) != len(cnd_args):
                    raise TypeError(f"Number of args doesn't match: {chk} vs {cnd}")
                else:
                    for i in range(len(cnd_args)):
                        stk.appendleft((TypeHint(chk_args[i]), TypeHint(cnd_args[i])))
            else:
                # print("Candidate is not union; args for at least one of typehints == 0")
                # the types must be compatible, do nothing
                if cnd_origin != chk_origin:
                    num_extra_types_ += 1
                if len(cnd_args) == 0 and len(chk_args) != 0:
                    num_any_matches_ += 1
        return num_any_matches_, num_extra_types_
    
    while len(stk) > 0:
        vals: Tuple[TypeHint[Any], TypeHint[Any]] = stk.popleft()
        chk:TypeHint[Any] = vals[0]
        cnd:TypeHint[Any] = vals[1]
        add_any, add_extra = compute_iter_distance(chk, cnd)
        num_any_matches += add_any
        num_extra_types += add_extra
    return num_any_matches, num_extra_types


