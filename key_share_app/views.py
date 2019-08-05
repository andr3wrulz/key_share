from enum import Enum
import requests
import re
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

    # ===== Initial Game query =====
    game = requests.get(
        'https://api-v3.igdb.com/games/',
        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
        data='search "' + key.name + '"; fields name,total_rating,total_rating_count,summary,url,time_to_beat,cover,category,genres,websites,first_release_date,involved_companies,keywords,multiplayer_modes,similar_games,storyline,videos; limit 1;'
    ).json()
    #print(game)

    game_info = {}
    game_info["name"] = game[0].get("name")
    game_info["summary"] = game[0].get("summary")
    game_info["storyline"] = game[0].get("storyline")
    game_info["igdbLink"] = game[0].get("url")
    game_info["rating"] = game[0].get("total_rating")
    game_info["release_date"] = game_info.get("first_release_date")
    game_info["rating_count"] = game[0].get("total_rating_count")
    game_info["type"] = game_categories[game[0].get("category")]

    # ===== Genre lookup =====
    genreIdString = ', '.join(map(str, game[0].get("genres"))).strip('[]') # Join ids together like '7, 8, 31, 32'
    genres = requests.get(
        'https://api-v3.igdb.com/genres',
        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
        data='where id = ({}); fields name;'.format(genreIdString)
    ).json()
    #print(genres)

    # Extract genre names from list of dicts like:
    # [{'id': 31, 'name': 'Adventure'}, {'id': 7, 'name': 'Music'}, {'id': 32, 'name': 'Indie'}, {'id': 8, 'name': 'Platform'}]
    game_info["genres"] = [genre.get("name") for genre in genres]

    # ===== Cover lookup =====
    cover = requests.get(
        'https://api-v3.igdb.com/covers',
        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
        data='where id = {}; fields url,height,width; limit 1;'.format(game[0].get("cover"))
    ).json()
    #print(cover)

    game_info["cover"] = cover[0]
    # Grab the full size cover instead of the thumbnail they try to give us
    # //images.igdb.com/igdb/image/upload/t_thumb/qx1e1miroreqtlv6ndt2.jpg -> //images.igdb.com/igdb/image/upload/t_cover_big/qx1e1miroreqtlv6ndt2.jpg
    game_info["cover"]["url"] = re.sub(r't_thumb','t_cover_big',game_info["cover"].get("url"))

    # ===== Website lookup =====
    websiteIdString = ', '.join(map(str, game[0].get("websites"))).strip('[]') # Join ids together like '7, 8, 31, 32'
    websites = requests.get(
        'https://api-v3.igdb.com/websites',
        headers={'user-key':'2ba120e8696301c4263b2b19e68e59e6'},
        data='where id = ({}); fields category,url;'.format(websiteIdString)
    ).json()
    #print(websites)

    # Rip website data from following format based on category:
    # [{'id': 56823, 'category': 1, 'url': 'http://wanderso.ng'}, {'id': 56824, 'category': 13, 'url': 'https://store.steampowered.com/app/530320'}]
    game_info["websites"] = {}
    for w in websites:
        game_info["websites"][ websiteTypes[w.get("category") - 1] ] = w.get("url")

    # ===== Time to beat lookup =====

    # ===== Involved company lookup =====

    # ===== Keyword lookup =====

    # ===== Multiplayer mode lookup =====

    # ===== Screenshot lookup =====

    # ===== Similar game lookup =====

    # ===== Video lookup =====

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

