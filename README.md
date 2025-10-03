Got it 👍 — thanks for pasting your endpoints. I’ll prepare two things for you:

1. **README.md** — clear setup/run guide, sample credentials, endpoints overview, how to run tests.
2. **Dockerfile** — production-ready containerization of your Django + DRF + JWT backend.

---

# 🎬 Django Movies API

A Django REST Framework (DRF) backend that provides authentication (JWT) and movie management (CRUD + ratings).
Frontend (React/Vite) can consume these APIs.

---

## 🚀 Features

* User authentication: register, login, logout
* JWT support with refresh tokens (`rest_framework_simplejwt`)
* CRUD operations for movies
* Rate movies and fetch ratings
* Per-user ratings view

---

## 🛠 Setup & Run

### 1. Clone the repository

```bash
git clone https://github.com/your-username/movies-api.git
cd movies-api
```

### 2. Create & activate virtual environment

```bash
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

Create `.env` file in the project root:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=*
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Start development server

```bash
python manage.py runserver
```

API will be available at:
👉 `http://127.0.0.1:8000/`

---

## 🐳 Run with Docker

Build the image:

```bash
docker build -t movies-api .
```

Run container:

```bash
docker run -d -p 8000:8000 movies-api
```

---

## 🔑 Sample Credentials

For quick testing, you can register or use:

```
email: testuser@example.com
password: TestPass123
```

---

## 📡 API Endpoints

### Health

* `GET /` → Health check

### Auth

* `POST /auth/register/` → Register new user
* `POST /auth/login/` → Login user (returns access + refresh token)
* `POST /auth/logout/` → Logout user
* `POST /auth/token/` → Obtain token pair (JWT)
* `POST /auth/token/refresh/` → Refresh token

### Movies

* `POST /movies/add/` → Add movie (auth required)
* `GET /movies/` → List all movies
* `GET /movies/{id}/` → Get movie details
* `DELETE /movies/{id}/` → Delete movie (auth required)

### Ratings

* `POST /movies/{id}/ratings/` → Rate a movie
* `GET /movies/{id}/ratings/` → Get ratings for a movie
* `GET /user/ratings/` → Get current user’s ratings

---

## 🧪 Run Tests

```bash
python manage.py test
```

---

## 📂 Project Structure

```
movies-api/
├── movies/              # Movies app
├── users/               # User app
├── requirements.txt
├── Dockerfile
├── manage.py
└── README.md
```
