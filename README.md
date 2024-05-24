# Coffee Map

![Static Badge](https://img.shields.io/badge/license%20-%20MIT%20-%20blue)

Welcome to my project!  
Coffee Map is a website that made in Python and Flask framework. It provides users to search for coffee shops by location and feature tags.

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
**Framework:** Flask  
**Visualize Tools:** Leaflet, Plotly  
**Database:** MongoDB Atlas  
**Data Pipeline:** Apache Airflow  
**Cloud Services:** AWS EC2, AWS CloudWatch, AWS S3  
**Containerization Service:** Docker  
**Reverse Proxy:** Nginx  
**Testing:** Pytest  
**CI/CD:** GitHub Actions

## Feature

### 1. Searching by shop name

https://github.com/yplzoe/coffee-map/assets/103309763/a2943b35-0eb4-43b3-bb30-8b3906a39352

### 2. Searching by filters

Filters including geolocation and feature tags. On the results page, users can observe the distribution of each store under each feature tag.

https://github.com/yplzoe/coffee-map/assets/103309763/cfbdb87d-6aa3-495a-a6ae-1b49fd674444

### 3. Historical Popular Times Information

Provide crowd information to help users determine the best times to visit.

https://github.com/yplzoe/coffee-map/assets/103309763/cdd6a327-000e-4a49-a653-b62c9386ddbc

### 4. Route Scheduling

Provide route planning to help users visit all desired locations in the shortest possible time.

https://github.com/yplzoe/coffee-map/assets/103309763/059890e5-588d-4cbf-823e-1ed09a6b35d2
