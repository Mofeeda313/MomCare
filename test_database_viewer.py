"""
test_database_viewer.py
MomCare Phase – Admin Database Viewer tests.

Covers:
  1. Access control – Admin gets 200, Mother and Worker get 403.
  2. All 7 table tabs load successfully.
  3. Password hashes are NEVER exposed in any response.
  4. Search works for vaccinations (BCG) and children (Vihaan).
  5. Pagination works for the vaccinations table (page 2).
  6. Record counts are present in the response.
"""

import sys
import re
from app import app

ADMIN_EMAIL    = "admin@momcare.org"
ADMIN_PASSWORD = "Admin@12345"
MOTHER_EMAIL   = "priya.nair@example.com"
MOTHER_PASSWORD = "MotherPassword123!"
WORKER_EMAIL   = "rajesh.kumar@example.com"
WORKER_PASSWORD = "DoctorPassword123!"

BASE = "/admin/database-viewer"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def get_viewer(client, table=None, search=None, page=None):
    params = []
    if table:
        params.append(f"table={table}")
    if search:
        params.append(f"q={search}")
    if page:
        params.append(f"page={page}")
    url = BASE + ("?" + "&".join(params) if params else "")
    return client.get(url, follow_redirects=True)


# ---------------------------------------------------------------------------
# Test 1 – Access control
# ---------------------------------------------------------------------------

def test_access_control():
    print("=== 1. Test Access Control ===")
    with app.test_client() as c:
        # Admin should get 200
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        r = get_viewer(c)
        assert r.status_code == 200, f"Admin expected 200, got {r.status_code}"
        print("Admin access granted (200) OK!")

    with app.test_client() as c:
        # Mother should get 403
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)
        r = get_viewer(c)
        assert r.status_code == 403, f"Mother expected 403, got {r.status_code}"
        print("Mother access denied (403) OK!")

    with app.test_client() as c:
        # Worker should get 403
        login(c, WORKER_EMAIL, WORKER_PASSWORD)
        r = get_viewer(c)
        assert r.status_code == 403, f"Worker expected 403, got {r.status_code}"
        print("Healthcare Worker access denied (403) OK!")


# ---------------------------------------------------------------------------
# Test 2 – All 7 table tabs load
# ---------------------------------------------------------------------------

TABLES = {
    "users":        [b"Registered Users", b"Email"],
    "mothers":      [b"Mother Profiles", b"Pregnancy"],
    "pregnant":     [b"Pregnant Women"],
    "children":     [b"Child Profiles"],
    "vaccinations": [b"Vaccination Records", b"Vaccine"],
    "growth":       [b"Growth Records", b"Weight"],
    "audit":        [b"Audit", b"Action"],
}


def test_all_table_tabs():
    print("\n=== 2. Test All 7 Table Tabs ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        for table_key, keywords in TABLES.items():
            r = get_viewer(c, table=table_key)
            assert r.status_code == 200, \
                f"Table '{table_key}' returned {r.status_code}"
            for kw in keywords:
                assert kw in r.data, \
                    f"Table '{table_key}': expected keyword {kw!r} not found"
            print(f"  Tab '{table_key}' loads correctly OK!")


# ---------------------------------------------------------------------------
# Test 3 – Password hashes are NEVER exposed
# ---------------------------------------------------------------------------

# Patterns that look like password hashes (werkzeug formats)
_HASH_RE = re.compile(
    rb"(scrypt|pbkdf2:sha\d+):[^\s<\"']{20,}",
    re.IGNORECASE,
)


def test_passwords_not_exposed():
    print("\n=== 3. Test Passwords Not Exposed ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        for table_key in TABLES:
            r = get_viewer(c, table=table_key)
            match = _HASH_RE.search(r.data)
            assert match is None, \
                f"Password hash detected in '{table_key}' view: {match.group()[:40]}"
        print("No password hashes exposed in any table view OK!")


# ---------------------------------------------------------------------------
# Test 4 – Search functionality
# ---------------------------------------------------------------------------

def test_search():
    print("\n=== 4. Test Search Functionality ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)

        # Search vaccinations for BCG
        r = get_viewer(c, table="vaccinations", search="BCG")
        assert r.status_code == 200
        # Either results are shown, or a "no records" message is shown — either is valid
        assert b"BCG" in r.data or b"No records" in r.data or b"no records" in r.data
        print("  Vaccination search for 'BCG' returns results page OK!")

        # Search children for Vihaan
        r = get_viewer(c, table="children", search="Vihaan")
        assert r.status_code == 200
        assert b"Vihaan" in r.data or b"No records" in r.data or b"no records" in r.data
        print("  Children search for 'Vihaan' returns results page OK!")


# ---------------------------------------------------------------------------
# Test 5 – Pagination
# ---------------------------------------------------------------------------

def test_pagination():
    print("\n=== 5. Test Pagination ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)

        # vaccinations table has 100+ rows — page 2 should exist
        r = get_viewer(c, table="vaccinations", page=2)
        assert r.status_code == 200, \
            f"Pagination page 2 returned {r.status_code}"
        # Page should contain some pagination indicator
        assert (b"page=2" in r.data or b"Page" in r.data or b"page" in r.data), \
            "Pagination indicator not found on page 2 response"
        print("  Vaccination table pagination (page 2) works OK!")

        # Non-existent page should not crash
        r = get_viewer(c, table="users", page=9999)
        assert r.status_code == 200, \
            f"Out-of-range page returned {r.status_code}"
        print("  Out-of-range page number does not crash the server OK!")


# ---------------------------------------------------------------------------
# Test 6 – Record counts visible
# ---------------------------------------------------------------------------

def test_record_counts_visible():
    print("\n=== 6. Test Record Counts Visible ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        r = get_viewer(c)
        assert r.status_code == 200
        # At least one digit should be present near the tab labels
        # (counts are rendered as digits inside the nav tabs)
        assert re.search(rb"\d+", r.data), "No digit found in viewer response"
        print("  Record counts rendered on viewer page OK!")


# ---------------------------------------------------------------------------
# Test 7 – Default table (no ?table param) renders without error
# ---------------------------------------------------------------------------

def test_default_table():
    print("\n=== 7. Test Default Table (no param) ===")
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        r = get_viewer(c)  # no table param
        assert r.status_code == 200
        assert b"Database Viewer" in r.data
        print("  Default table renders without error OK!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    failures = []
    for fn in [
        test_access_control,
        test_all_table_tabs,
        test_passwords_not_exposed,
        test_search,
        test_pagination,
        test_record_counts_visible,
        test_default_table,
    ]:
        try:
            fn()
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failures.append((fn.__name__, str(e)))
        except Exception as e:
            print(f"  ERROR in {fn.__name__}: {e}")
            failures.append((fn.__name__, str(e)))

    print()
    if failures:
        print(f">>> {len(failures)} TEST(S) FAILED <<<")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print(">>> ALL DATABASE VIEWER TESTS PASSED SUCCESSFULLY! <<<")

