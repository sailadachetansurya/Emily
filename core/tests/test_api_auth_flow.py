import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class TestApiAuthFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp_dir = tempfile.TemporaryDirectory()
        cls._tmp_dir = tmp_dir
        db_path = Path(tmp_dir.name) / "test_echo.db"
        os.environ["ECHO_DB_PATH"] = str(db_path)
        os.environ["ECHO_SKIP_PIPELINE_PRELOAD"] = "1"

        from pipeline.api.main import app
        from pipeline.api.persistence import init_db

        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls._tmp_dir.cleanup()

    def test_register_login_and_data_flow(self):
        register = self.client.post(
            "/api/auth/register",
            json={"username": "alice", "password": "secret123"},
        )
        self.assertEqual(register.status_code, 200)
        token = register.json()["token"]
        auth_header = {"Authorization": f"Bearer {token}"}

        me = self.client.get("/api/auth/me", headers=auth_header)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["username"], "alice")

        save_draft = self.client.post(
            "/api/data/drafts",
            headers=auth_header,
            json={"text": "draft text", "mood": "Sad"},
        )
        self.assertEqual(save_draft.status_code, 200)

        drafts = self.client.get("/api/data/drafts", headers=auth_header)
        self.assertEqual(drafts.status_code, 200)
        self.assertGreaterEqual(len(drafts.json()), 1)

        reset_req = self.client.post("/api/auth/password-reset/request", json={"username": "alice"})
        self.assertEqual(reset_req.status_code, 200)
        reset_token = reset_req.json()["reset_token"]
        self.assertTrue(reset_token)

        reset_confirm = self.client.post(
            "/api/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpass123"},
        )
        self.assertEqual(reset_confirm.status_code, 200)

        login = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "newpass123"},
        )
        self.assertEqual(login.status_code, 200)


if __name__ == "__main__":
    unittest.main()
