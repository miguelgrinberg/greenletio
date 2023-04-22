import runpy
import sys
from greenletio import patch_blocking


def main():
    with patch_blocking():
        if sys.argv[1] == '-m':
            sys.argv = sys.argv[2:]
            runpy.run_module(sys.argv[0], run_name='__main__', alter_sys=True)
        else:
            sys.argv = sys.argv[1:]
            runpy.run_path(sys.argv[0], run_name='__main__')
