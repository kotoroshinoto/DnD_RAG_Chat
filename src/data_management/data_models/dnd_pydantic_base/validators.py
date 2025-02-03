from functools import partial, partialmethod

from pydantic import validate_call


dnd_rag_validate_call = partial(
        validate_call,
        config={
                'arbitrary_types_allowed': True,
                'extra':'forbid',
                'validate_default':True,
        },
        validate_return=True
)
