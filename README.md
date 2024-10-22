# Setup Guide

## Prerequisites

- Python 3.x installed
- `pip` package manager

## Installation Steps

### 1. Create and Activate a Virtual Environment

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

- **On Windows:**

  ```bash
  venv\Scripts\activate
  ```

- **On macOS/Linux:**

  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies

Install the required packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Running the Application

Navigate to the `/app` directory:

```bash
cd app
```

Start the application:

```bash
fastapi run main.py
```

## Accessing the Application

- **API Endpoint:** [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Running Tests

Ensure you're in the root directory of the project, then run:

```bash
pytest
```
