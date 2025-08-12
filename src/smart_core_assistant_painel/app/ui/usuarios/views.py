from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from rolepermissions.roles import assign_role

# Create your views here.


def cadastro(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "cadastro.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if not senha == confirmar_senha:
            messages.add_message(
                request, constants.ERROR, "Senha e confirmar senha devem ser iguais."
            )
            return redirect("/usuarios/cadastro/")

        if len(senha or "") < 6:
            messages.add_message(
                request, constants.ERROR, "A senha deve ter 6 ou mais caracteres."
            )
            return redirect("/usuarios/cadastro/")

        users = User.objects.filter(username=username)
        if users.exists():
            messages.add_message(
                request, constants.ERROR, "Já existe um usuário com esse username."
            )
            return redirect("/usuarios/cadastro/")

        if username is None or senha is None:
            messages.add_message(
                request, constants.ERROR, "Username e senha são obrigatórios."
            )
            return redirect("/usuarios/cadastro/")

        User.objects.create_user(username=username, password=senha)

        return redirect("/usuarios/login")

    return redirect("/usuarios/cadastro/")


def login(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "login.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")

        user = authenticate(request, username=username or "", password=senha or "")

        if user:
            auth.login(request, user)
            return redirect("treinar_ia")

        messages.add_message(request, constants.ERROR, "Username ou senha inválidos.")
        return redirect("login")

    return redirect("login")


# @user_passes_test(lambda u: u.is_superuser)
def permissoes(request: HttpRequest) -> HttpResponse:
    users = User.objects.filter(is_superuser=False)
    return render(request, "permissoes.html", {"users": users})


def tornar_gerente(request: HttpRequest, id: int) -> HttpResponseRedirect:
    # if not request.user.is_superuser:
    #    raise Http404()
    user = User.objects.get(id=id)
    assign_role(user, "gerente")
    return redirect("permissoes")
