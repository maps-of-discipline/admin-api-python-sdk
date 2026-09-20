from werkzeug.local import LocalProxy

from admin_api.integrations.flask.request_auth import get_request_auth

current_auth = LocalProxy(lambda: get_request_auth().context)
current_api = LocalProxy(lambda: get_request_auth().api)
