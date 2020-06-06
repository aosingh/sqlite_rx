import os
import socket
import tempfile

from sqlite_rx.auth import KeyGenerator

def test_generation_of_curve_keys():
    with tempfile.TemporaryDirectory() as destination_dir:
        key_id = "id_client_{}_curve".format(socket.gethostname())
        key_generator = KeyGenerator(destination_dir=destination_dir, key_id=key_id)
        key_generator.generate()
        public_key = os.path.join(destination_dir, "{}.key".format(key_id))
        private_key = os.path.join(destination_dir, "{}.key_secret".format(key_id))
        assert os.path.exists(public_key) == True
        assert os.path.exists(private_key) == True
