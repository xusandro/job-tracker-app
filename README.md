# Job Tracker Split App

This version of Job Tracker is split into a React frontend and a Flask API backend.

## Project structure

- `frontend/`: React + Vite client
- `backend/`: Flask JSON API
- `database/schema.sql`: MySQL schema
- `.env`: shared backend environment variables

## Backend setup

1. Create a virtual environment.
2. Install dependencies from `backend/requirements.txt`.
3. Make sure MySQL is running and create the schema with `database/schema.sql`.
4. Keep the `.env` values updated for your local database.
5. Run `python app.py` from the `backend/` directory.

The backend runs on `http://127.0.0.1:5001`.

## Frontend setup

1. Run `npm install` inside `frontend/`.
2. Run `npm run dev`.

The frontend runs on `http://127.0.0.1:5173` and proxies `/api` requests to the Flask backend.

## New features

- Job application status with these values: `in_progress`, `interview`, `offer`, `rejected`
- Password reset using `username + birth_date + new password`
- Dashboard list shows `title + company`
- Status can be updated directly from the detail panel

## Notes

- Backend registration bug in `backend/app.py` has already been fixed
- `.env` contains backend environment variables and should not be committed

## Suggested project direction

This repo is being turned into a DevOps portfolio project. Current priority:

1. Docker
2. ECS / Fargate
3. Terraform
4. CI/CD
5. EKS later if it adds clear value

## Database update for an existing local setup

If you already created the old schema, run these statements once:

```sql
USE job_tracker;

ALTER TABLE users
ADD COLUMN birth_date DATE NOT NULL DEFAULT '2000-01-01';

ALTER TABLE jobs
ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'in_progress';
```

## Available API endpoints

- `GET /api/health`
- `GET /api/session`
- `POST /api/register`
- `POST /api/login`
- `POST /api/reset-password`
- `POST /api/logout`
- `GET /api/jobs?q=keyword`
- `POST /api/jobs`
- `GET /api/jobs/<id>`
- `PUT /api/jobs/<id>`
- `DELETE /api/jobs/<id>`
