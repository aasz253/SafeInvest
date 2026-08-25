# SafeInvest

Mobile-first investment platform with daily earnings, built with FastAPI (Python).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env file
cp .env.example .env

# 3. Seed database (9 packages + admin user)
python -m app.seed

# 4. Run server
uvicorn app.main:app --reload
```

**Server:** http://localhost:8000
**Swagger docs:** http://localhost:8000/docs

## Admin Login

- **Phone:** `0712345678`
- **Password:** `Admin@123`

## SMS OTP (Free)

Africa's Talking sandbox is free. Steps:

1. Register at https://africastalking.com
2. Get free sandbox API key
3. Add to `.env`:
```
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-sandbox-key
```
4. Register test numbers in the sandbox console

Without an API key, OTPs print to your terminal (mock mode).

## Investment Packages

| Package | Deposit (KSH) | Daily Bonus | Days | Total Return |
|---------|--------------|-------------|------|--------------|
| Bronze | 450 | 80 | 10 | 800 |
| Silver | 950 | 125 | 16 | 2,000 |
| Gold | 1,500 | 150 | 20 | 3,000 |
| Platinum | 2,850 | 225 | 20 | 4,500 |
| Diamond | 4,700 | 335 | 30 | 10,050 |
| VIP 1 | 9,900 | Progressive | - | Variable |
| VIP 2 | 18,000 | Progressive | - | Variable |
| VIP 3 | 45,000 | Progressive | - | Variable |
| VIP 4 | 99,000 | Progressive | - | Variable |

## Referral Bonus

- **Inviter:** 150 KSH + 100 KSH increment per additional invitee
- **Invitee:** 150 KSH on first deposit (450+)

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with phone + password |
| POST | `/api/v1/auth/verify-otp` | Verify phone OTP |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/profile` | User profile |

### Packages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/packages/list` | All packages |
| GET | `/api/v1/packages/details/{id}` | Package details |

### Deposits
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/deposits/create` | Create deposit |
| GET | `/api/v1/deposits/pending` | Pending (admin) |
| PUT | `/api/v1/deposits/approve/{id}` | Approve (admin) |
| PUT | `/api/v1/deposits/reject/{id}` | Reject (admin) |
| GET | `/api/v1/deposits/history` | My deposit history |

### Earnings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/earnings/daily` | Today's earnings |
| POST | `/api/v1/earnings/claim` | Claim daily earning |
| GET | `/api/v1/earnings/history` | Earning history |
| GET | `/api/v1/earnings/summary` | Total summary |

### Referrals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/referrals/my-team` | My invited users |
| GET | `/api/v1/referrals/bonus` | Referral bonuses |
| GET | `/api/v1/referrals/code` | My referral code |

### Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feedback/create` | Submit feedback |
| GET | `/api/v1/feedback/my-feedback` | My feedback |
| GET | `/api/v1/feedback/all` | All feedback (admin) |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | All users |
| GET | `/api/v1/admin/deposits` | All deposits |
| GET | `/api/v1/admin/earnings` | All earnings |
| GET | `/api/v1/admin/reports` | Summary reports |

## Docker

```bash
docker-compose up --build
```

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy
- **Auth:** JWT (python-jose) + bcrypt
- **SMS:** Africa's Talking (sandbox = free)
- **Database:** SQLite (Postgres-ready)
- **Docs:** Auto-generated Swagger at `/docs`
