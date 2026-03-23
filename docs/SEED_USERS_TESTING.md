# Seed Users Script - Testing & Verification

This document provides testing instructions and verification for the `flask seed-users` command.

---

## Quick Test

To verify the seed-users command is working:

```bash
# Test with 5 users
flask seed-users 5

# Check output for:
# - "Successfully added 5 fake users"
# - User summary showing counts
```

---

## Comprehensive Testing

### 1. Test Default Behavior

```bash
flask seed-users
```

**Expected:**
- Creates 30 users
- All approved
- Mixed roles (managers and employees)

### 2. Test Custom Quantity

```bash
flask seed-users 50
```

**Expected:**
- Creates exactly 50 users

### 3. Test Pending Users

```bash
flask seed-users 20 --pending
```

**Expected:**
- Creates 20 users with `is_approved=False`

### 4. Test Role Filters

```bash
# Managers only
flask seed-users 15 --role=manager

# Employees only
flask seed-users 15 --role=employee

# Mixed (default)
flask seed-users 15 --role=mixed
```

**Expected:**
- Creates users with specified roles

### 5. Test Combined Options

```bash
flask seed-users 10 --pending --role=manager
```

**Expected:**
- Creates 10 pending manager accounts

---

## Verification Script

Run this Python script to verify users were added:

```python
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    total = User.query.count()
    approved = User.query.filter_by(is_approved=True).count()
    pending = User.query.filter_by(is_approved=False).count()

    print(f"Total users: {total}")
    print(f"Approved: {approved}")
    print(f"Pending: {pending}")

    # Test password
    user = User.query.filter(User.id > 5).first()
    if user:
        can_login = user.check_password("password123")
        print(f"Password test: {'PASS' if can_login else 'FAIL'}")
```

---

## Expected Behavior

### Success Output

```
Seeding 30 users...
Successfully added 30 fake users.

User Summary:
  - Total users in DB: 31
  - Approved: 30
  - Pending: 1
  - Managers: 14
  - Employees: 17
```

### Duplicate Email Skipping

```
Seeding 10 users...
Skipped 2 users (duplicate emails).
Successfully added 8 fake users.
```

---

## Troubleshooting

### Issue: "No module named 'faker'"

**Solution:**
```bash
pip install faker
```

### Issue: Users not appearing in database

**Solution:**
Check database connection in `.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:port/database
```

Verify with:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(User.query.count())"
```

### Issue: Import errors

**Solution:**
Ensure project root is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Common Use Cases

### Development Setup
```bash
# Create diverse test data
flask seed-users 50 --role=employee
flask seed-users 20 --role=manager
flask seed-users 30 --pending
```

### Testing Pagination
```bash
# Create 100+ users to test pagination
flask seed-users 100
```

### Testing Approval Workflow
```bash
# Create pending users to test approval
flask seed-users 25 --pending
```

---

## Notes

- All seeded users have password: `password123`
- Usernames and emails are generated using Faker library
- Users are created as active (not blacklisted)
- Duplicate emails are automatically skipped
- Command respects `DATABASE_URL` from `.env` file

---

## Integration with Admin Panel

After seeding users, verify in admin panel:

1. Navigate to `http://localhost:5010/admin/users`
2. Check pagination works with many users
3. Test filtering by role
4. Verify search functionality
5. Test bulk actions on seeded users

---

## Automated Testing

The seed-users command is tested in:
- Unit tests: `testing/unit/test_admin.py`
- Integration tests: `testing/integration/test_integration.py`

Run tests:
```bash
pytest testing/ -v
```
