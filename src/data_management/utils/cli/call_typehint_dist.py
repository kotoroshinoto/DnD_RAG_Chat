import click
from beartype import beartype
from beartype.typing import *
from beartype.cave import *
from data_management.utils.typehint_distance import typehint_distance


@click.command()
@click.option('--imports', type=click.STRING, multiple=True, help='provide an import statement that provides your non-builtins.  Cannot use *')
@click.argument('typehint1', type=click.STRING)
@click.argument('typehint2', type=click.STRING)
@beartype
def main(typehint1:str, typehint2:str, imports:Union[tuple[str], tuple]) -> None:
    """
    This will automatically import all the types provided by beartype within beartype.typing and beartype.cave, but you may require specific types from another package.
    :param typehint1: typehint to be checked
    :param typehint2: typehint to be checked against
    :param imports: a list of import statements that will provide your non-builtin type names for your typehints. Cannot use *
    :return:
    """
    for import_stmnt in imports:
        exec(import_stmnt)
    local_vars = dict()
    exec(f'th1 = {typehint1}', globals(), local_vars)
    exec(f'th2 = {typehint2}', globals(), local_vars)
    th1 = local_vars['th1']
    th2 = local_vars['th2']
    score = typehint_distance(th1, th2)
    print(score)

if __name__ == '__main__':
    main()