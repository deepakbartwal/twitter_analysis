## Instruction to run the project

### setup environment and install dependency
- virutalenv env_name
- source env_name activate
- pip install -r requirements.txt
- python -m textblob.download_corpora

### go to poject folder
- cd local_path/twitter_analysis

### add twitter setting to 'twitter_analysis/settings.py' file (API_KEY, API_SECRET, ACCESS_TOKEN and ACCESS_TOKEN_SECRET)

### runserver
- python manage.py runserver host:post
- eg. of url : localhost:8000/get-tweet-analysis/?target_user=twitter_id
