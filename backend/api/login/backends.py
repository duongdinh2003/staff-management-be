import re
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            if self.is_valid_email(username_or_email=username):
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        # Verify the passsword and ensure user is active
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
        
    def is_valid_email(self, username_or_email):
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.match(email_regex, username_or_email) is not None
