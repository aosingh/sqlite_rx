# test_cli_client.py
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
from sqlite_rx.cli import client
from sqlite_rx import __version__

def test_main_help():
    # Test help display
    with patch('sys.argv', ['sqlite-client', '--help']):
        # Use rich.console.Console.print instead of builtins.print
        with patch('rich.console.Console.print') as mock_print:
            with pytest.raises(SystemExit):
                client.main()
            mock_print.assert_called()

def test_main_version():
    # Test version display
    with patch('sys.argv', ['sqlite-client', '--version']):
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                client.main()
            assert __version__ in mock_stdout.getvalue()

def test_execute_query():
    # Test query execution
    with patch('sys.argv', ['sqlite-client', 'exec', 'SELECT 1']):
        # We need to patch at the point where the CLI imports the client
        with patch('sqlite_rx.cli.client.SQLiteClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.execute.return_value = {"items": [[1]], "error": None}
            
            # Patch sys.exit to prevent actual exit, AND run without standalone mode
            with patch('sys.exit'):
                with patch('rich.print_json'):
                    client.main(standalone_mode=False)
            
            # Verify execute was called with correct query
            mock_client.execute.assert_called_with(query='SELECT 1')