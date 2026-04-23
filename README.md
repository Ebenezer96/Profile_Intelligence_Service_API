Profile Intelligence Service API

A backend service that provides intelligent profile insights using stored data, filtering, and natural-language search capabilities.

Built with Django and Django REST Framework.

Overview

This API allows users to:

- Retrieve stored profile data
- Filter and sort profiles
- Perform natural-language search queries on profiles

The service focuses on data retrieval and intelligent querying.

Features

- Retrieve all profiles with pagination
- Advanced filtering and sorting
- Natural-language search (e.g., “female adults in US”)
- Efficient query handling
- JSON-based API responses
- Input validation and error handling



Tech Stack

- Django 6.x
- Django REST Framework
- SQLite (default) / PostgreSQL (production)
- Python 3.x

Project Structure

Profile_Intelligence_Service_API/

    profiles/
        models.py
        views.py
        serializers.py
        urls.py

    config/
        settings.py
        urls.py

    manage.py
    db.sqlite3
    requirements.txt

Setup Instructions

1. Clone Repository

git clone https://github.com/Ebenezer96/Profile_Intelligence_Service_API.git
cd Profile_Intelligence_Service_API

2. Create Virtual Environment

python -m venv venv
venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Run Migrations

python manage.py migrate

5. Start Server

python manage.py runserver

 API Endpoints

Health Check

GET /

Response:

{
  "status": "success",
  "message": "Profile Intelligence Service is running"
}

 Get Profiles

GET /api/profiles/

Query Parameters:

- gender
- age_group
- country_id
- sort_by
- order (asc or desc)
- page

Example:

GET /api/profiles/?gender=female&country_id=US&sort_by=age&order=desc

 Search Profiles

GET /api/profiles/search/?q={query}

Examples:

/api/profiles/search/?q=female adults in US
/api/profiles/search/?q=male teenagers

Description:

The API parses the query and extracts:
- gender
- age group
- country

 Data Model

- id (UUID)
- name (string)
- gender (string)
- gender_probability (float)
- sample_size (integer)
- age (integer)
- age_group (string)
- country_id (string)
- country_probability (float)
- created_at (datetime)

 Pagination

Example response:

{
  "count": 100,
  "next": "...",
  "previous": "...",
  "results": [...]
}

Error Handling

- Invalid query → 400
- Server error → 500

Example:

{
  "error": "Invalid query parameter"
}

 Testing

You can test using:

- Postman
- cURL
- Browser

Example:

curl http://127.0.0.1:8000/api/profiles/

 Deployment

- Use PostgreSQL
- Set DEBUG=False
- Configure environment variables
- Use Gunicorn

Procfile:

web: gunicorn config.wsgi


Future Improvements

- Add POST endpoint
- Add DELETE endpoint
- Add external API integration
- Add authentication (JWT)
- Add caching

 Author

Ebenezer Amakato  
Backend Developer | ICT Officer

 License

This project is for educational and backend practice purposes.
