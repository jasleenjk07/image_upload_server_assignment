# Cloud Assignment: Scalable Image Upload Service

FastAPI-based backend that accepts image uploads, validates files, stores them in AWS S3, and uses NGINX round-robin load balancing across two backend instances.

## Features

- `POST /upload` accepts `multipart/form-data` with a `file` field.
- Supports only `jpg`, `jpeg`, and `png`.
- Rejects files larger than `2 MB`.
- Uploads valid files to S3 using unique keys: `uploads/<uuid>.<ext>`.
- Supports two backend instances behind NGINX.
- Includes tests and GitHub Actions CI.

## Project Structure

```text
cloud-assignment/
├── app/
│   ├── main.py
│   ├── s3_service.py
│   └── config.py
├── tests/
│   └── test_upload.py
├── nginx/
│   └── nginx.conf
├── .github/workflows/
│   └── ci.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Project_README.md
```

## Prerequisites

- Python `3.11+`
- AWS account with S3 bucket
- IAM credentials with `s3:PutObject` permission
- NGINX (for local load balancing and EC2 deployment)

## Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with valid values:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=your-region
S3_BUCKET_NAME=your-bucket
```

## Run Backend Instances

Start two FastAPI instances in separate terminals:

```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 3001
```

```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 3002
```

## NGINX Load Balancer

Use the provided config:

```bash
nginx -c /absolute/path/to/cloud-assignment/nginx/nginx.conf
```

Requests can now be sent to:

```text
POST http://localhost/upload
```

## API Contract

### Upload Endpoint

- **Method:** `POST`
- **Path:** `/upload`
- **Body:** `form-data`, key = `file`, type = file

### Success Response (`200`)

```json
{
  "url": "https://<bucket>.s3.amazonaws.com/uploads/<uuid>.<ext>"
}
```

### Common Error Responses

- `400`: missing file
- `413`: file exceeds `2 MB`
- `415`: invalid extension or content type
- `500`: S3 upload or credentials issue

## Testing

Run tests:

```bash
pytest
```

## CI

GitHub Actions workflow in `.github/workflows/ci.yml` runs:

1. Dependency installation
2. Test suite
3. App boot smoke check

## EC2 Deployment (Checklist)

1. Launch Ubuntu EC2 instance.
2. Open inbound ports: `22` (your IP), `80` (public).
3. Install `python3`, `python3-venv`, `pip`, `nginx`, `git`.
4. Clone repo and configure `.env`.
5. Start backends on `127.0.0.1:3001` and `127.0.0.1:3002`.
6. Apply NGINX config and restart NGINX.
7. Test with:

```bash
curl -X POST "http://<ec2-public-ip>/upload" -F "file=@/path/to/image.png"
```

For full step-by-step deployment details, see `Project_README.md`.
