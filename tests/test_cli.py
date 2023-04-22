import sys
import unittest
from unittest.mock import patch
from greenletio.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_module(self):
        with patch('greenletio.cli.runpy') as runpy:
            sys.argv = ['greenletio', '-m', 'myapp', 'foo']
            main()
            runpy.run_module.assert_called_with('myapp', run_name='__main__',
                                                alter_sys=True)

    def test_cli_script(self):
        with patch('greenletio.cli.runpy') as runpy:
            sys.argv = ['greenletio', 'myapp.py', 'foo']
            main()
            runpy.run_path.assert_called_with('myapp.py', run_name='__main__')
