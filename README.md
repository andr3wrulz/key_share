# Game Key Share
This project was created with an abundance of hatred for managing extra game keys from a spreadsheet. I had tons of game keys and it was a pain to manage because there wasn't a good way to sort them or find out information about which indie game was which.

The basic idea is a web application where you can view/search posted game keys. You can learn more about a game by clicking on it in the list (assuming it has an entry in IGDB). All of this is built on the Django framework so user authentication and database migrations are super easy.

Built with [Django](https://www.djangoproject.com/) and [Bootstrap](https://getbootstrap.com). Game information from [IGDB](https://api.igdb.com/).

Shoutout to [Django Girls Tutorial](https://tutorial.djangogirls.org/en/) which helped me a lot on this project.

### Some types of information pulled from IGDB:
* Release Date
* Game Description
* Screenshots
* Genre(s)
* Ratings
* Similar Games
* Related websites (IGDB, official, steam)
* Time to Beat Statistics

## Screen Shots
List Page
![List Page](https://i.imgur.com/cMGmRKu.png)

Game Information
![Game Info](https://i.imgur.com/vqNwowb.png)

Submitting a Key
![Submit](https://i.imgur.com/dXB4WsM.png)

Login
![Login](https://i.imgur.com/e5XEiNN.png)


## Run the application
### Docker (preferred)
I have included a docker-compose file in the repository to make deployments easy. This assumes you have docker and docker compose installed.
1. Grab the compose.yml file from the repo
2. Edit the compose file as desired (you may want to change exposed ports or the location of the sqlite database file)
3. Create two files in your mounted directory django_secret.txt (generate a django key with ```python -c 'import random; print("".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)]))'```) and igdb_api.txt (put your api key from https://api.igdb.com/ here)
4. Start the container ```docker-compose -f compose.yml up -d```
5. Create a super user account in the database ```docker exec -it key_share python /usr/src/app/manage.py createsuperuser```
![Create Super User](https://i.imgur.com/71TvUek.png)
6. Browse to the web interface at ```http://[docker-host-ip]:[port]``` ex: ```http://localhost:8000```
7. You can access the admin page at /admin ex: ```http://localhost:8000/admin```

### Command line
Todo, full step by step
1. Set virtual environment
2. Install dependencies ```pip install --no-cache-dir -r requirements.txt```
3. Create migration paths ```python manage.py makemigrations key_share_app```
4. Apply migrations ```python manage.py migrate```
5. Create a super user ```python manage.py createsuperuser```
6. Run the server ```python manage.py runserver```
7. Check it out ```http://localhost:8000```

## Technical Information
### Database
The current implementation only uses the built in sqlite database so it wont scale but I don't think a simple database of game keys warrants a full database instance. Feel free to override if you have a spare database lying around.

### API
To limit the number of API calls (IGDB only gives 10k/month for the free tier), I moved the API calls to the insertion/update of the key. This means that I had to store the API information in the database (hurts db space utilization and, to some extent, retrieval times) but the pages load faster as you don't have to wait for several round trip API calls between the application and IGDB.