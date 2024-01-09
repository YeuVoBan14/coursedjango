from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Room, Topic, Message
from .forms import RoomForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
#restrict not login user from specific function
from django.contrib.auth.decorators import login_required
#register form
from django.contrib.auth.forms import UserCreationForm



# Create your views here.
# rooms = [
#     {'id':1, 'name':'Lets learn python'},
#     {'id':2, 'name':'Design with me'},
#     {'id':3, 'name':'Frontend Developer'},
# ]

def loginPage(request):
    #to let the template know what page is this by using if else
    page = 'login'

    #restricted user from relogin
    if request.user.is_authenticated:
        messages.error(request,'You have logged in')
        return redirect('home')
        

    if request.method == "POST":
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        #Check if user exist
        try:
            username = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        #use authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password is incorrect')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            #after user was created, want to access (clean the data) the user right way, use commit false
            user = form.save(commit=False)
            #clean the data
            user.username = user.username.lower()
            user.save()
            #after registration, login the user
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')

    context = {'form':form}
    return render(request, 'base/login_register.html', context)

def home(request):
    #filter function
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # import Q give you the ability to use (and, or)
    rooms = Room.objects.filter(
        #you cant use host to search because of foreignkey, must through parent class
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
        )
    #get topics
    topics = Topic.objects.all()
    #count rooms
    room_count = rooms.count()
    context = {'rooms':rooms, 'topics': topics, 'room_count':room_count}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id = pk)
    #get messages from the model Message but using instead of M, we use m
    #give me all the messages related to this room
    room_messages = room.message_set.all().order_by('-created')
    #get participants
    participants = room.participants.all()
    #user write message
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            #get the body through name of the input
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants':participants}
    return render(request, 'base/room.html', context)

@login_required(login_url='/login')
def createRoom(request):
    form  = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html',context)

@login_required(login_url='/login')
def updateRoom(request, pk):
    #prefill form
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    #Authorize if the user is the host of the room
    if request.user != room.host:
        return HttpResponse('Your are not allowed that!!')

    #update data, like create one's
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
    context = {'form': form}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    #Authorize if the user is the host of the room
    if request.user != room.host:
        return HttpResponse('Your are not allowed to do that!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='/login')
def deleteMessage(request, pk, room_pk):
    message = Message.objects.get(id=pk)
    room = Room.objects.get(id=room_pk)
    #Authorize if the user is the host of the room
    if request.user != message.user:
        return HttpResponse('Your are not allowed to do that!!')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=room.id )
    return render(request, 'base/delete.html', {'obj': message})