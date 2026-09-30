
# ⚡ API Testing Client

A strong Postman-style API testing client built with Python and Streamlit.

## Features

- GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- URL + query parameter builder
- Custom headers
- JSON / raw / form request bodies
- Bearer token, Basic Auth and API Key authentication
- Environment variables using `{{VARIABLE}}`
- Response status, timing, size and headers
- JSON response viewer
- Request history with replay
- Collections for reusable requests
- Environment manager
- JSON request import/export
- Local JSON persistence
- Responsive Streamlit UI
- Friendly error handling

## Requirements

- Python 3.10+
- Internet access for testing public APIs

## Windows Setup

```powershell
cd "API Testing Client"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open:

http://localhost:8501

## Recommended Demo APIs

GET:
`https://jsonplaceholder.typicode.com/posts/1`

POST:
`https://jsonplaceholder.typicode.com/posts`

## Project Structure

```text
API Testing Client/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── history.json
│   ├── collections.json
│   └── environments.json
└── exports/
```

## Security Notes

This is a local development/testing client. Avoid committing real API keys, passwords, bearer tokens, cookies, or production credentials. The included environment file contains demo values only.
