# Scalable Image Upload Server - Step-by-Step Plan

This README is a process-by-process plan for building a scalable image upload backend without using any database. The final system will use Python backend servers, AWS S3 for image storage, NGINX for load balancing, and GitHub Actions for CI.

## 1. Project Goal

Build a backend system that:

- Accepts image uploads using `POST /upload`
- Allows only JPG and PNG image files
- Rejects files larger than 2 MB
- Uploads valid images to AWS S3
- Runs multiple backend instances
- Uses NGINX round-robin load balancing
- Includes a GitHub Actions CI pipeline
- Does not use any database

## 2. Suggested Project Structure

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
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 3. Backend API Setup

### Step 1: Create Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

Use FastAPI, Uvicorn, Boto3, and testing tools.

```bash
pip install fastapi uvicorn boto3 python-multipart pillow pytest
pip freeze > requirements.txt
```

### Step 3: Create Upload Endpoint

Create a Python server with:

- Endpoint: `POST /upload`
- Request type: `multipart/form-data`
- File field name: `file`
- Accepted image types: JPG, JPEG, PNG
- Maximum file size: 2 MB

Validation rules:

- Reject missing files
- Reject non-image files
- Reject unsupported extensions
- Reject files larger than 2 MB
- Return clear error messages with proper HTTP status codes

Expected success response:

```json
{
  "url": "https://<bucket-name>.s3.amazonaws.com/<image-name>"
}
```

## 4. AWS S3 Integration

### Step 1: Create S3 Bucket

In AWS Console:

1. Open S3.
2. Create a bucket.
3. Choose a unique bucket name.
4. Select the nearest AWS region.
5. Configure permissions according to assignment needs.

### Step 2: Create IAM User

Create an IAM user with permissions to upload files to the S3 bucket.

Minimum required permission:

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::<bucket-name>/*"
}
```

### Step 3: Configure Environment Variables

Create `.env.example`:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=your-region
S3_BUCKET_NAME=your-bucket-name
```

Do not commit real AWS credentials.

### Step 4: Upload Files with Unique Names

Use a UUID or timestamp-based filename.

Example:

```text
uploads/2026-04-29-uuid-image.png
```

Recommended naming format:

```text
uploads/<uuid>.<extension>
```

## 5. Run Multiple Backend Instances

Start at least two backend servers on different ports.

Terminal 1:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 3001
```

Terminal 2:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 3002
```

Optional: Add a log message in the upload endpoint showing which port handled the request.

Example log:

```text
Upload handled by backend server on port 3001
```

This helps verify load balancing.

## 6. NGINX Load Balancer Setup

### Step 1: Install NGINX

macOS:

```bash
brew install nginx
```

Ubuntu:

```bash
sudo apt update
sudo apt install nginx
```

### Step 2: Create NGINX Configuration

Create `nginx/nginx.conf`:

```nginx
events {}

http {
    upstream image_upload_backend {
        server 127.0.0.1:3001;
        server 127.0.0.1:3002;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://image_upload_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

NGINX uses round-robin load balancing by default, so requests will alternate between backend instances.

### Step 3: Start NGINX

Example command:

```bash
nginx -c /absolute/path/to/cloud-assignment/nginx/nginx.conf
```

After NGINX starts, upload requests should go to:

```text
http://localhost/upload
```

NGINX will forward them to either:

```text
http://localhost:3001/upload
http://localhost:3002/upload
```

## 7. GitHub Actions CI Setup

Create `.github/workflows/ci.yml`.

The workflow should run on:

- `push`
- `pull_request`

Pipeline steps:

1. Check out the repository.
2. Set up Python.
3. Install dependencies.
4. Run tests.
5. Start the app briefly to confirm it can run.

Example workflow:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest

      - name: Verify app starts
        run: |
          uvicorn app.main:app --host 127.0.0.1 --port 3001 &
          sleep 5
          curl -f http://127.0.0.1:3001/docs
```

The CI workflow should fail if:

- Dependencies cannot install
- Tests fail
- The server cannot start

## 8. Postman Testing Process

### Step 1: Start Backend Instances

Start both backend servers:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 3001
uvicorn app.main:app --host 127.0.0.1 --port 3002
```

### Step 2: Start NGINX

```bash
nginx -c /absolute/path/to/cloud-assignment/nginx/nginx.conf
```

### Step 3: Create Postman Request

Use:

```text
POST http://localhost/upload
```

Body:

- Select `form-data`
- Key: `file`
- Type: `File`
- Value: choose a JPG or PNG image under 2 MB

### Step 4: Expected Response

```json
{
  "url": "https://<bucket-name>.s3.amazonaws.com/uploads/<unique-image-name>"
}
```

### Step 5: Verify S3 Upload

Open AWS S3 Console and confirm:

- The file appears in the correct bucket
- The filename is unique
- Multiple uploads create multiple objects

### Step 6: Verify Load Balancing

Upload several images through Postman and check backend logs.

Expected behavior:

```text
Request 1 -> port 3001
Request 2 -> port 3002
Request 3 -> port 3001
Request 4 -> port 3002
```

This confirms NGINX round-robin distribution.

## 9. Error Handling Checklist

The API should return useful errors for:

- No file uploaded
- File is larger than 2 MB
- File type is not JPG or PNG
- S3 upload fails
- AWS credentials are missing or invalid

Suggested status codes:

```text
400 Bad Request        Invalid or missing file
413 Payload Too Large  File exceeds 2 MB
415 Unsupported Media  Invalid file type
500 Server Error       S3 upload failure
```

## 10. Optional Bonus Features

### Image Resizing

Use Pillow to resize images before upload.

Example:

- Maximum width: 1024 px
- Maintain aspect ratio
- Upload resized version to S3

### Signed S3 URLs

Instead of returning a public S3 URL, generate a temporary signed URL using Boto3.

Example:

```python
s3_client.generate_presigned_url(...)
```

### Docker Setup

Add:

- `Dockerfile`
- `docker-compose.yml`
- NGINX container
- Two backend containers

This makes the multi-instance setup easier to run.

### EC2 Deployment

Use this checklist to deploy the same two-backend + NGINX setup on AWS EC2.

#### AWS Prerequisites

1. Create an S3 bucket in your preferred AWS region.
2. Create an IAM user (or role) with minimum upload permission:

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::<bucket-name>/uploads/*"
}
```

3. Keep credentials out of git and only place them in runtime environment variables (`.env` on server).

#### EC2 Provisioning

1. Launch an Ubuntu EC2 instance (t2.micro is enough for this assignment).
2. Create/attach a key pair and download the `.pem`.
3. Configure security group inbound rules:
   - `22` (SSH) from your IP
   - `80` (HTTP) from `0.0.0.0/0`
4. Connect:

```bash
ssh -i /path/to/key.pem ubuntu@<ec2-public-ip>
```

#### Server Setup On EC2

Install required runtime tools:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
```

Clone and prepare the app:

```bash
git clone <your-repo-url>
cd cloud-assignment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with real values for:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`

#### Run Two Backend Instances

In two separate SSH sessions (or with `tmux`), start:

```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 3001
```

```bash
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 3002
```

Both backends should listen on localhost only; NGINX will be the public entrypoint.

#### Configure NGINX Reverse Proxy

Copy project config into system NGINX config and validate:

```bash
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

#### Deployment Verification

1. Health check each local backend:

```bash
curl -f http://127.0.0.1:3001/docs
curl -f http://127.0.0.1:3002/docs
```

2. Upload through NGINX using public IP:

```bash
curl -X POST "http://<ec2-public-ip>/upload" \
  -F "file=@/absolute/path/to/test-image.png"
```

3. Confirm:
   - Response contains S3 URL
   - Object exists under `uploads/` in S3
   - Repeated requests rotate across backends (if instance-port logging is enabled)

#### Stabilization (Recommended)

To survive SSH disconnects and reboots:

1. Replace manual `uvicorn` commands with two `systemd` services (one for `3001`, one for `3002`).
2. Keep NGINX enabled with `systemctl enable nginx`.
3. Reboot once and verify upload still works end-to-end.

## 11. Final Submission Checklist

Before submitting, confirm:

- `POST /upload` works
- JPG and PNG files upload successfully
- Files larger than 2 MB are rejected
- Non-image files are rejected
- S3 returns a valid uploaded file URL
- At least two backend instances run
- NGINX forwards requests to both instances
- GitHub Actions runs on push and pull request
- README includes setup, run, NGINX, CI, and testing instructions
- No database is used
- No AWS credentials are committed

## 12. Sample Request and Response

Request:

```text
POST http://localhost/upload
Content-Type: multipart/form-data
file: image.png
```

Response:

```json
{
  "url": "https://my-image-bucket.s3.amazonaws.com/uploads/8f2d5b8e-43af-48b7-9d5e-image.png"
}
```

## 13. Recommended Build Order

Follow this order while implementing:

1. Create Python FastAPI server.
2. Add `/upload` endpoint.
3. Add file type and file size validation.
4. Add S3 upload logic with Boto3.
5. Test direct upload on port `3001`.
6. Run second backend instance on port `3002`.
7. Configure NGINX upstream servers.
8. Test uploads through `http://localhost/upload`.
9. Add tests.
10. Add GitHub Actions workflow.
11. Update README with final commands and screenshots if required.
12. Push final code to GitHub.
