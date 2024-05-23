# Coffee Map

Welcome to my project!  
Coffee Map is a website that made in Python and Flask framework. It provides users to search for cafes by location and tags.

WEBSITE: <https://www.goforacoffee.site>

## Architecture

![architecture](/README_required/coffee_map_framework.png)

## Data Pipeline

**Extract:**

- Web crawling from Google Maps using Selenium to get reviews.
- Get shop detail information from Google Map Api.
- Get mrt staions information and location from Taipei Metro.
- Backing up data to AWS S3.

**Transfrom:**

- Use Python for data cleaning and preprocessing.

**Load:**

- Load the processed data to MongoDB Atlas.

## Technologies

**Programming Language:** Python  
**Database:** MongoDB Atlas  
**Data Pipeline:** Apache Airflow  
**Cloud Services:** AWS EC2, AWS CloudWatch, AWS S3  
**Others:** GitHub Actions, Docker, Nginx, Leaflet, Plotly

## Feature

1. Searching by shop name or filters  
   ![search by shop name](/README_required/search_by_name.mov)
2. Tags for Coffee Shops
3. Historical Popular Times Information
4. Route Scheduling
