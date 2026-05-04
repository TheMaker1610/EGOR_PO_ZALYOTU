import requests

BASE_URL = "http://127.0.0.1:8000"


class ApiClient:
    def __init__(self):
        self.token: str | None = None
        self.role: str | None = None
        self.username: str | None = None
        self.must_change_password: bool = False

    def _headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def login(self, username: str, password: str) -> dict:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            self.token = data["access_token"]
            self.role = data["role"]
            self.username = data["username"]
            self.must_change_password = data["must_change_password"]
            return {"ok": True, "data": data}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def logout(self):
        if self.token:
            try:
                requests.post(f"{BASE_URL}/auth/logout", headers=self._headers(), timeout=5)
            except Exception:
                pass
        self.token = None
        self.role = None
        self.username = None

    def change_password(self, current: str, new: str) -> dict:
        resp = requests.post(
            f"{BASE_URL}/auth/change-password",
            json={"current_password": current, "new_password": new},
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            self.must_change_password = False
            return {"ok": True}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def calculate(self, params: dict) -> dict:
        resp = requests.post(
            f"{BASE_URL}/calc/run",
            json=params,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def get_blocks_analysis(self, params: dict) -> dict:
        resp = requests.post(
            f"{BASE_URL}/calc/blocks-analysis",
            json=params,
            headers=self._headers(),
            timeout=15,
        )
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def get_history(self) -> dict:
        resp = requests.get(f"{BASE_URL}/calc/history", headers=self._headers(), timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text}

    def get_users(self) -> dict:
        resp = requests.get(f"{BASE_URL}/users/", headers=self._headers(), timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text}

    def create_user(self, username: str, password: str, role: str) -> dict:
        resp = requests.post(
            f"{BASE_URL}/users/",
            json={"username": username, "password": password, "role": role},
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def update_user(self, user_id: int, **kwargs) -> dict:
        resp = requests.patch(
            f"{BASE_URL}/users/{user_id}",
            json=kwargs,
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def reset_password(self, user_id: int, new_password: str) -> dict:
        resp = requests.post(
            f"{BASE_URL}/users/{user_id}/reset-password",
            json={"new_password": new_password},
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def unlock_user(self, user_id: int) -> dict:
        resp = requests.post(
            f"{BASE_URL}/users/{user_id}/unlock",
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def get_db_table(self, table: str) -> dict:
        resp = requests.get(f"{BASE_URL}/db/{table}", headers=self._headers(), timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text}

    def get_log_settings(self) -> dict:
        resp = requests.get(f"{BASE_URL}/log-settings/", headers=self._headers(), timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text}

    def update_log_settings(self, data: dict) -> dict:
        resp = requests.post(
            f"{BASE_URL}/log-settings/",
            json=data,
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"ok": False, "error": detail}

    def get_audit(self) -> dict:
        resp = requests.get(f"{BASE_URL}/audit/", headers=self._headers(), timeout=10)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": resp.text}
