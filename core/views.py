from django.shortcuts import render


def site_under_construction(request):
    return render(request, "site_under_construction.html")


def error_404(request, exception):
    return render(request, "error404.html", status=404)


def error_500(request):
    return render(request, "error500.html", status=500)
