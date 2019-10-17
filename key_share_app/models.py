import requests
import re
import datetime
from enum import Enum

from django.db import models
from django.contrib.auth.models import User

# From https://api-docs.igdb.com/#website
class WebsiteTypes(Enum):
    OFFICIAL = 1
    WIKIA = 2
    WIKIPEDIA = 3
    FACEBOOK = 4
    TWITTER = 5
    TWITCH = 6
    INSTAGRAM = 8
    YOUTUBE = 9
    IPHONE = 10
    IPAD = 11
    ANDROID = 12
    STEAM = 13
    REDDIT = 14
    DISCORD = 15
    GOOGLEPLUS = 16
    TUMBLR = 17
    LINKEDIN = 18
    PINTEREST = 19
    SOUNDCLOUD = 20

# From https://api-docs.igdb.com/#game
game_categories = ['Main Game', 'DLC', 'Expansion', 'Bundle', 'Standalone Expansion']
game_statuses = ['Released', 'Alpha', 'Beta', 'Early Access', 'Offline', 'Cancelled']

class Key(models.Model):
    # Data fields
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=100)
    notes = models.CharField(max_length=500, null=True, blank=True)
    created = models.DateTimeField('created timestamp', auto_now_add=True, editable=False)
    last_updated = models.DateTimeField('last updated timestamp', auto_now=True, editable=False)
    redeemed = models.DateTimeField('redeemed timestamp', null=True, blank=True)

    # Relationship fields
    parent_key = models.ForeignKey(
        'Key', # Another instance of this object
        related_name='child_key',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        User, # Django User model
        related_name='submitted_keys',
        on_delete=models.CASCADE
    )
    updated_by = models.ForeignKey(
        User, # Django User model
        related_name='updated_keys',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )
    redeemed_by = models.ForeignKey(
        User, # Django User model
        related_name='redeemed_keys',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )

    # Game info fields
    game_info_name = models.CharField(max_length=100, null=True, blank=True)
    game_info_summary = models.TextField(null=True, blank=True)
    game_info_storyline = models.TextField(null=True, blank=True)
    game_info_cover_url = models.URLField(max_length=200, null=True, blank=True)
    game_info_release_date = models.DateTimeField('released timestamp', null=True, blank=True)
    game_info_type = models.CharField(max_length=100, null=True, blank=True)
    game_info_developer = models.CharField(max_length=100, null=True, blank=True)
    game_info_igdb_url = models.URLField(max_length=200, null=True, blank=True)
    game_info_official_url = models.URLField(max_length=200, null=True, blank=True)
    game_info_steam_url = models.URLField(max_length=200, null=True, blank=True)
    game_info_genres = models.CharField(max_length=500, null=True, blank=True)
    game_info_keywords = models.CharField(max_length=500, null=True, blank=True)
    game_info_similar_games = models.CharField(max_length=500, null=True, blank=True)
    game_info_rating = models.DecimalField(decimal_places=2, max_digits=5, null=True, blank=True)
    game_info_rating_count = models.IntegerField(null=True, blank=True)
    game_info_screenshots = models.TextField(null=True, blank=True)
    game_info_time_to_beat = models.CharField(max_length=100, null=True, blank=True)
    # Videos
    # Multiplayer modes

    def __str__(self):
        return self.name
    
    def populate_game_info(self):
        # ===== Initial Game query =====
        game = requests.get(
            'https://api-v3.igdb.com/games/',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='search "' + self.name + '"; fields name,total_rating,total_rating_count,summary,url,time_to_beat,cover,category,genres,websites,first_release_date,involved_companies,keywords,multiplayer_modes,similar_games,storyline,screenshots,videos; limit 1;'
        ).json()
        print(game)

        # If we got something from igdb
        if len(game) == 1:
            # ===== Direct Data (no subqueries) =====
            self.game_info_name = game[0].get("name")
            if game[0].get("category") is not None:
                self.game_info_type = game_categories[game[0].get("category")]
            if game[0].get("first_release_date") is not None:
                self.game_info_release_date = datetime.datetime.fromtimestamp(game[0].get("first_release_date"))
            self.game_info_summary = game[0].get("summary")
            self.game_info_storyline = game[0].get("storyline")
            self.game_info_igdb_url = game[0].get("url")
            self.game_info_rating = game[0].get("total_rating")
            self.game_info_rating_count = game[0].get("total_rating_count")

            # ===== Cover lookup =====
            if game[0].get("cover") is not None:
                cover = requests.get(
                    'https://api-v3.igdb.com/covers',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = {}; fields url,height,width; limit 1;'.format(game[0].get("cover"))
                ).json()
                #print(cover)

                if len(cover) == 1:
                    self.game_info_cover_url = cover[0].get("url")
                    # Grab the full size cover instead of the thumbnail they try to give us
                    # //images.igdb.com/igdb/image/upload/t_thumb/qx1e1miroreqtlv6ndt2.jpg -> //images.igdb.com/igdb/image/upload/t_cover_big/qx1e1miroreqtlv6ndt2.jpg
                    self.game_info_cover_url = re.sub(r't_thumb','t_cover_big',self.game_info_cover_url)

            # ===== Genre lookup =====
            if game[0].get("genres") is not None:
                genre_id_string = ', '.join(map(str, game[0].get("genres")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                genres = requests.get(
                    'https://api-v3.igdb.com/genres',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}); fields name;'.format(genre_id_string)
                ).json()
                #print(genres)

                # Extract genre names from list of dicts like:
                # [{'id': 31, 'name': 'Adventure'}, {'id': 7, 'name': 'Music'}, {'id': 32, 'name': 'Indie'}, {'id': 8, 'name': 'Platform'}] ->
                # 'Adventure, Music, Indie, Platform'
                self.game_info_genres = ', '.join([genre.get("name") for genre in genres])

            # ===== Involved company lookup =====
            if game[0].get("involved_companies") is not None:
                involved_companies_string = ', '.join(map(str, game[0].get("involved_companies")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                involved_companies = requests.get(
                    'https://api-v3.igdb.com/involved_companies',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}) & developer = true; fields company; limit 1;'.format(involved_companies_string)
                ).json()
                # If we found a involved company with the developer flag
                if len(involved_companies) == 1:
                    developer = requests.get(
                        'https://api-v3.igdb.com/companies',
                        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                        data='where id = {}; fields name; limit 1;'.format(involved_companies[0].get("id"))
                    ).json()
                    # If we found the company that developed the game
                    if len(developer) == 1:
                        self.game_info_developer = developer[0].get("name")

            # ===== Keyword lookup =====
            if game[0].get("keywords") is not None:
                keyword_string = ', '.join(map(str, game[0].get("keywords")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                keywords = requests.get(
                    'https://api-v3.igdb.com/keywords',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}); fields name;'.format(keyword_string)
                ).json()

                # Extract keywords from list of dicts like:
                # [{"id": 386,"name": "platformers"},{"id": 117,"name": "indie"}, {"id": 4702,"name": "bards"},{"id": 1687,"name": "music based"}] ->
                # 'platformers, indie, bards, music based'
                self.game_info_keywords  = ', '.join([kw.get("name") for kw in keywords])

            # ===== Multiplayer mode lookup =====

            # ===== Screenshot lookup =====
            if game[0].get("screenshots") is not None:
                screenshot_string = ', '.join(map(str, game[0].get("screenshots")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                screenshot = requests.get(
                    'https://api-v3.igdb.com/screenshots',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}); fields url;'.format(screenshot_string)
                ).json()

                # Extract image urls from list of dicts like:
                # [ {"id": 123973,"url": "//images.igdb.com/igdb/image/upload/t_thumb/qt39h1bbio87yijaylyq.jpg"},{"id": 123974,"url": "//images.igdb.com/igdb/image/upload/t_thumb/f1jlivj9zipslgmrapik.jpg"}]
                # Grab the full size cover instead of the thumbnail they try to give us
                # //images.igdb.com/igdb/image/upload/t_thumb/qx1e1miroreqtlv6ndt2.jpg -> //images.igdb.com/igdb/image/upload/t_1080p/qx1e1miroreqtlv6ndt2.jpg
                self.game_info_screenshots = ' '.join([re.sub(r't_thumb','t_1080p',ss.get("url")) for ss in screenshot])

            # ===== Similar game lookup =====
            if game[0].get("similar_games") is not None:
                similar_games_string = ', '.join(map(str, game[0].get("similar_games")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                similar_games = requests.get(
                    'https://api-v3.igdb.com/games',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}); fields name;'.format(similar_games_string)
                ).json()

                # Build the string to display consisting of the names of similar games
                self.game_info_similar_games = ', '.join([sg.get("name") for sg in similar_games])

            # ===== Time to beat lookup =====
            if game[0].get("time_to_beat") is not None:
                time_to_beat = requests.get(
                    'https://api-v3.igdb.com/time_to_beats',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = {}; fields completely,hastly,normally; limit 1;'.format(game[0].get("time_to_beat"))
                ).json()

                # If we found it
                if len(time_to_beat) != 0:
                    times = []
                    if time_to_beat[0].get("normally") is not None:
                        times.append( "Normal: {0:.1f} hours".format( int(time_to_beat[0].get("normally")) / 3600.0) ) # Convert seconds to int and then convert to hours
                    if time_to_beat[0].get("hastly") is not None:
                        times.append( "Hasty: {0:.1f} hours".format( int(time_to_beat[0].get("hastly")) / 3600.0) ) # Convert seconds to int and then convert to hours
                    if time_to_beat[0].get("completely") is not None:
                        times.append( "Completely: {0:.1f} hours".format( int(time_to_beat[0].get("completely")) / 3600.0) ) # Convert seconds to int and then convert to hours

                    self.game_info_time_to_beat = ', '.join(times)

            # ===== Video lookup =====

            # ===== Website lookup =====
            if game[0].get("websites") is not None:
                website_id_string = ', '.join(map(str, game[0].get("websites")[:10])).strip('[]') # Join ids together like '7, 8, 31, 32', limit to 10 entries
                websites = requests.get(
                    'https://api-v3.igdb.com/websites',
                    headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                    data='where id = ({}); fields category,url;'.format(website_id_string)
                ).json()
                #print(websites)

                # Rip website data from following format based on category:
                # [{'id': 56823, 'category': 1, 'url': 'http://wanderso.ng'}, {'id': 56824, 'category': 13, 'url': 'https://store.steampowered.com/app/530320'}]
                for w in websites:
                    if w.get("category") == WebsiteTypes.OFFICIAL.value:
                        self.game_info_official_url = w.get("url")
                    elif w.get("category") == WebsiteTypes.STEAM.value:
                        self.game_info_steam_url = w.get("url")

        # Commit the changes
        self.save()
    
    def get_screenshots(self):
        if self.game_info_screenshots is None:
            return None
        return self.game_info_screenshots.split(' ')