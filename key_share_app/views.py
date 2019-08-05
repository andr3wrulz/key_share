from enum import Enum
import requests
import re
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Key
from .forms import KeyForm

# From https://api-docs.igdb.com/#website
websiteTypes = [
    'official','wikia','wikipedia','facebook','twitter', # 1 - 5
    'twitch','','instagram','youtube','iphone', # 6 - 10
    'ipad','android','steam','reddit','discord', # 11 - 15
    'googleplus','tumblr','linkedin','pinterest','soundcloud' # 16 - 20
]

# From https://api-docs.igdb.com/#game
game_categories = ['Main Game', 'DLC', 'Expansion', 'Bundle', 'Standalone Expansion']
game_statuses = ['Released', 'Alpha', 'Beta', 'Early Access', 'Offline', 'Cancelled']

def key_list(request):
    # Determine if the show_redeemed parameter was set
    show_redeemed = request.GET.get('show_redeemed')
    
    if show_redeemed is None or show_redeemed == "no":
        # Filter out redeemed keys
        keys = Key.objects.filter(redeemed__isnull=True)
    else:
        # Query the database for all keys
        keys = Key.objects.all()
    
    # Pass the key list to the key_list template
    return render(request, 'key_list.html', {'key_list': keys, 'show_redeemed': show_redeemed})

def key_detail(request, pk):
    # Try to retrieve key from the database
    key = get_object_or_404(Key, pk=pk) # Get requested key from db

    game_info = {}

    # ===== Initial Game query =====
    game = requests.get(
        'https://api-v3.igdb.com/games/',
        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
        data='search "' + key.name + '"; fields name,total_rating,total_rating_count,summary,url,time_to_beat,cover,category,genres,websites,first_release_date,involved_companies,keywords,multiplayer_modes,similar_games,storyline,screenshots,videos; limit 1;'
    ).json()
    print(game)

    if len(game) == 1:
        # ===== Directly available data
        game_info["name"] = game[0].get("name")
        game_info["summary"] = game[0].get("summary")
        game_info["storyline"] = game[0].get("storyline")
        game_info["igdbLink"] = game[0].get("url")
        game_info["rating"] = game[0].get("total_rating")
        game_info["rating_count"] = game[0].get("total_rating_count")
        game_info["release_date"] = datetime.datetime.fromtimestamp(game[0].get("first_release_date"))
        game_info["type"] = game_categories[game[0].get("category")]

        # ===== Cover lookup =====
        cover = requests.get(
            'https://api-v3.igdb.com/covers',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = {}; fields url,height,width; limit 1;'.format(game[0].get("cover"))
        ).json()
        #print(cover)

        if len(cover) == 1:
            game_info["cover"] = cover[0]
            # Grab the full size cover instead of the thumbnail they try to give us
            # //images.igdb.com/igdb/image/upload/t_thumb/qx1e1miroreqtlv6ndt2.jpg -> //images.igdb.com/igdb/image/upload/t_cover_big/qx1e1miroreqtlv6ndt2.jpg
            game_info["cover"]["url"] = re.sub(r't_thumb','t_cover_big',game_info["cover"].get("url"))

        # ===== Genre lookup =====
        genre_id_string = ', '.join(map(str, game[0].get("genres"))).strip('[]') # Join ids together like '7, 8, 31, 32'
        genres = requests.get(
            'https://api-v3.igdb.com/genres',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = ({}); fields name;'.format(genre_id_string)
        ).json()
        #print(genres)

        # Extract genre names from list of dicts like:
        # [{'id': 31, 'name': 'Adventure'}, {'id': 7, 'name': 'Music'}, {'id': 32, 'name': 'Indie'}, {'id': 8, 'name': 'Platform'}]
        game_info["genres"] = [genre.get("name") for genre in genres]

        # ===== Involved company lookup =====
        involved_companies_string = ', '.join(map(str, game[0].get("involved_companies"))).strip('[]') # Join ids together like '7, 8, 31, 32'
        involved_companies = requests.get(
            'https://api-v3.igdb.com/involved_companies',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = ({}) & developer = true; fields company; limit 1;'.format(involved_companies_string)
        ).json()
        if len(involved_companies) == 1:
            developer = requests.get(
                'https://api-v3.igdb.com/companies',
                headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
                data='where id = {}; fields name; limit 1;'.format(involved_companies[0].get("id"))
            ).json()
            if len(developer) == 1:
                game_info["developer"] = developer[0].get("name")

        # ===== Keyword lookup =====
        keyword_string = ', '.join(map(str, game[0].get("keywords"))).strip('[]') # Join ids together like '7, 8, 31, 32'
        keywords = requests.get(
            'https://api-v3.igdb.com/keywords',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = ({}); fields name;'.format(keyword_string)
        ).json()

        # Extract keywords from list of dicts like:
        # [{"id": 386,"name": "platformers"},{"id": 117,"name": "indie"}, {"id": 4702,"name": "bards"},{"id": 1687,"name": "music based"}]
        game_info["keywords"] = [kw.get("name") for kw in keywords]

        # ===== Multiplayer mode lookup =====
        # TODO

        # ===== Screenshot lookup =====
        screenshot_string = ', '.join(map(str, game[0].get("screenshots"))).strip('[]') # Join ids together like '7, 8, 31, 32'
        screenshot = requests.get(
            'https://api-v3.igdb.com/screenshots',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = ({}); fields url;'.format(screenshot_string)
        ).json()

        # Extract image urls from list of dicts like:
        # [ {"id": 123973,"url": "//images.igdb.com/igdb/image/upload/t_thumb/qt39h1bbio87yijaylyq.jpg"},{"id": 123974,"url": "//images.igdb.com/igdb/image/upload/t_thumb/f1jlivj9zipslgmrapik.jpg"}]
        # Grab the full size cover instead of the thumbnail they try to give us
        # //images.igdb.com/igdb/image/upload/t_thumb/qx1e1miroreqtlv6ndt2.jpg -> //images.igdb.com/igdb/image/upload/t_1080p/qx1e1miroreqtlv6ndt2.jpg
        game_info["screenshots"] = [re.sub(r't_thumb','t_1080p',ss.get("url")) for ss in screenshot]

        # ===== Similar game lookup =====

        # ===== Time to beat lookup =====

        # ===== Video lookup =====
        
        # ===== Website lookup =====
        website_id_string = ', '.join(map(str, game[0].get("websites"))).strip('[]') # Join ids together like '7, 8, 31, 32'
        websites = requests.get(
            'https://api-v3.igdb.com/websites',
            headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
            data='where id = ({}); fields category,url;'.format(website_id_string)
        ).json()
        #print(websites)

        # Rip website data from following format based on category:
        # [{'id': 56823, 'category': 1, 'url': 'http://wanderso.ng'}, {'id': 56824, 'category': 13, 'url': 'https://store.steampowered.com/app/530320'}]
        game_info["websites"] = {}
        for w in websites:
            game_info["websites"][ websiteTypes[w.get("category") - 1] ] = w.get("url")
    
    # End if len(game) == 1

    # ===== Return response =====
    print(game_info)

    # If we found the key, pass it to the detail page
    return render(request, 'key_detail.html', {'key': key, 'game_info': game_info})

@login_required
def key_new(request):
    # If the user just filled out the submit form
    if request.method == "POST":
        # Get their entry
        form = KeyForm(request.POST)
        if form.is_valid():
            # Prep the update but don't save
            key = form.save(commit=False)
            # Attach the user to the request
            key.created_by = request.user
            # created timestamp is set automatically by the model
            key.save()
            # Redirect to their key's detail page
            return redirect('key_detail', pk=key.pk)
    
    # If they haven't filled out the form, display it
    else:
        form = KeyForm()
        return render(request, 'key_edit.html', {'form': form})

@login_required
def key_edit(request, pk):
    # Try to retrieve key from the database
    key = get_object_or_404(Key, pk=pk)

    # If the user is submitting their edit
    if request.method == "POST":
        # Load the submitted form
        form = KeyForm(request.POST, instance=key)
        if form.is_valid():
            # Prep the update but don't save
            key = form.save(commit=False)
            # Save this user
            key.updated_by = request.user
            # last_updated is updated automatically by the model
            key.save()
            # Redirect user to the detail page for the edited key
            return redirect('key_detail', pk=key.pk)
    # If the user is just loading the edit page
    else:
        # Load the key form with the key info populated
        form = KeyForm(instance=key)
        return render(request, 'key_edit.html', {'form': form})

@login_required
def key_delete(request, pk):
    # Try to retrieve key from database
    key = get_object_or_404(Key, pk=pk)
    # Delete the key
    key.delete()
    # Redirect to home page
    return redirect('key_list')

@login_required
def key_redeem(request, pk):
    # Try to retrieve the key from the database
    key = get_object_or_404(Key, pk=pk)

    # If the user redeemed the key
    if request.method == "POST":
        # Add the user and timestamp to the redeem fields
        key.redeemed = timezone.now()
        key.redeemed_by = request.user
        # Save the info
        key.save()
        # Redirect to key list
        return redirect('key_list')
    # User hasn't redeemed the key
    else:
        # Display the key and "Mark Redeemed" button
        return render(request, 'key_redeem.html', {'key': key})

