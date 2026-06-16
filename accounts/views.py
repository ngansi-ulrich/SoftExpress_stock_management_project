from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from logs.models import ActivityLog
from django.contrib import messages

def Login(request):
    
    print("VIEW REACHED")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action="LOGIN",
                description="User logged into system"
            )
            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password"
        )

        return redirect("Login")
    return render(request, "accounts/Login.html")
    
def Logout(request):
    logout(request)
    return redirect("Login")