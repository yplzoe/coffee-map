from app_fun import search_db

query = {'name': {'text': 'starbuck'}}
print(search_db(query))
