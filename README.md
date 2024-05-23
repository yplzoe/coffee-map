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



https://github.com/yplzoe/coffee-map/assets/103309763/a2943b35-0eb4-43b3-bb30-8b3906a39352



2. Tags for Coffee Shops





https://github.com/yplzoe/coffee-map/assets/103309763/cfbdb87d-6aa3-495a-a6ae-1b49fd674444





3. Historical Popular Times Information





https://github.com/yplzoe/coffee-map/assets/103309763/cdd6a327-000e-4a49-a653-b62c9386ddbc




4. Route Scheduling



https://github.com/yplzoe/coffee-map/assets/103309763/059890e5-588d-4cbf-823e-1ed09a6b35d2


