from fiscallizeon.accounts.models import User
from fiscallizeon.clients.models import Client
from django.contrib.sessions.models import Session

user = User.objects.first()
user.set_password('123456')
password = user.password


User.objects.update(password=password, must_change_password=False, can_access_app=True)
Client.objects.all().update(allow_login_only_google=False, two_factor_enabled=False)
Session.objects.all().delete()