import logging.config
import os
import socket
import tempfile
import unittest

from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import KeyGenerator

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))


class TestKeyFileGeneration(unittest.TestCase):

    def test_generation_of_curve_keys(self):
        with tempfile.TemporaryDirectory() as destination_dir:
            key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=destination_dir, key_id=key_id)
            key_generator.generate()
            public_key = os.path.join(destination_dir, "{}.key".format(key_id))
            private_key = os.path.join(
                destination_dir, "{}.key_secret".format(key_id))
            self.assertTrue(os.path.exists(public_key))
            self.assertTrue(os.path.exists(private_key))


if __name__ == '__main__':

    unittest.main()
