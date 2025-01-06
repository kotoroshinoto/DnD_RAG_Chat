import shutil
from typing import Callable, List, Union, Optional

import click
import functools
import pip
import sys
import os
import platform
import subprocess
import tempfile
import venv
from pathlib import Path


class RunsSubprocess:
    def __init__(self, venv_path: Optional[Union[str, Path]]=None):
        if venv_path is not None:
            self._venv_path = Path(venv_path)
        else:
            self._venv_path = None
    def _build_venv_activate_command(self):
        scripts_path = self._venv_path / "Scripts"
        if platform.system() == 'Windows':
            activate_cmd = 'cmd /c call'
            activate_script = scripts_path / "activate.bat"
        else:
            activate_cmd = 'source'
            activate_script = scripts_path / "activate"
        return ' '.join([activate_cmd, str(activate_script)])
    
    def has_valid_venv(self) -> bool:
        return not (
                (self._venv_path is None)
                or (isinstance(self._venv_path, str) and len(str(self._venv_path)) == 0)
                or isinstance(self._venv_path, Path) and not self._venv_path.exists()
        )
    
    def _assemble_args(self, command: Optional[Union[str, List[str]]]) -> str:
        invalid_env = not self.has_valid_venv()
        if invalid_env:
            activate_command = None
        else:
            activate_command = self._build_venv_activate_command()
        if isinstance(command, str):
            command = [command]
        
        if activate_command is None:
            if command is None:
                raise RuntimeError("Nothing to do")
            return ' '.join(command)
        else:
            if command is None:
                return f'{activate_command}'
            else:
                # Combine the activate command and the target command
                return f'{activate_command} && ' + ' '.join(command)
    
    def __call__(self, command: Optional[Union[str, List[str]]]=None, *args, **kwargs):
        args_str = self._assemble_args(command)
        print(f"Attempting to execute: '{args_str}'")
        return subprocess.run(args=args_str, *args, **kwargs)

def read_yn(prompt):
    response = input(f'{prompt}\n')
    if response.lower() in {'y', 'yes'}:
        return True
    elif response.lower() in {'n', 'no'}:
        return False
    else:
        raise ValueError("Invalid response")


def do_venv_if_user_requires() -> RunsSubprocess:
    try:
        if read_yn("Do you want to use a virtual environment?"):
            if read_yn("Do you want to create a virtual environment?"):
                venv_path = Path(input("Enter the path where you would like to create a virtual "
                                       "environment:\n"))
                venv.create(venv_path)
            else:
                venv_path = Path(input("Enter the path to your existing virtual environment:\n"))
                if not venv_path.exists():
                    raise ValueError("the provided path does not exist")
            runs_proc = RunsSubprocess(venv_path=venv_path)
            completed_proc = runs_proc()
            if completed_proc.returncode != 0:
                raise ValueError("Failed to activate virtual environment")
            else:
                print("Successfully activated virtual environment", file=sys.stdout)
            return runs_proc
        else:
            return RunsSubprocess()
    except ValueError as e:
        print(e, file=sys.stderr)
        exit(1)

def install_dependencies(local_process_run_func: RunsSubprocess):
    requirements_txt = local_process_run_func(
            ['pdm', 'export', '--without-hashes'],
            capture_output=True,
            text=True
    )
    if requirements_txt.returncode != 0:
        print("Error Detected, aborting.")
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, dir='.') as f:
        print(requirements_txt.stdout)
        f.write(requirements_txt.stdout)
        f.flush()
        print(f.name)
        tmpfile_path = Path('.') / f.name
    
    try:
        print("Installing dependencies...")
        # pip.main(['install', '-v', '-r', f.name])
        import shutil
        if shutil.which('pip') is None:
            raise RuntimeError("pip not found")
        else:
            print("pip is available")
        cmd = ['pip', 'install', '-v', '-r', str(tmpfile_path)]
        comp_process_obj = local_process_run_func(
                cmd
        )
        
        if comp_process_obj.returncode != 0:
            print(f"Error Detected,{comp_process_obj.returncode} aborting.")
    except Exception as e:
        print(f"Error Detected,{e}", file=sys.stderr)
    tmpfile_path.unlink()

if __name__ == "__main__":
    process_run_func = do_venv_if_user_requires()
    process_run_func(command=['pip install -v pdm'])
    install_dependencies(process_run_func)
    if process_run_func.has_valid_venv():
        print(f"In the future, before working with this repository or running commands for pdm or "
              f"pip, execute the following: {process_run_func._build_venv_activate_command()}")
