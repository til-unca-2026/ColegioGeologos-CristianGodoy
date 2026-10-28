from django.shortcuts import redirect
from django.urls import reverse


class MustChangePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            allowed_paths = {
                reverse("accounts:password_change"),
                reverse("accounts:logout"),
            }
            if request.path not in allowed_paths:
                return redirect("accounts:password_change")

        return self.get_response(request)
