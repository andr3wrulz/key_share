from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Key
from .forms import KeyForm

def key_list(request):
    # Determine if the show_redeemed parameter was set
    show_redeemed = request.GET.get('show_redeemed')
    print(show_redeemed)
    
    if show_redeemed is None or show_redeemed == "no":
        # Filter out redeemed keys
        keys = Key.objects.filter(redeemed__isnull=True)
    else:
        # Query the database for all keys
        keys = Key.objects.all()
    
    # Pass the key list to the key_list template
    return render(request, 'key_list.html', {'key_list': keys, 'show_redeemed': show_redeemed})

def key_detail(request, pk):
    # Try to retrieve key from database
    key = get_object_or_404(Key, pk=pk) # Get requested key from db
    # If we found the key, pass it to the detail page
    return render(request, 'key_detail.html', {'key': key})

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
    # Try to retrieve key from database
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