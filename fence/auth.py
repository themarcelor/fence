from functools import reduce, wraps
import urllib

from authutils.errors import JWTError
from authutils.token.validate import (
    current_token,
    set_current_token,
    validate_request,
)
import flask
from flask_sqlalchemy_session import current_session
from sqlalchemy import func

from fence.errors import Unauthorized
from fence.jwt.validate import validate_jwt
from fence.models import IdentityProvider
from fence.utils import clear_cookies


def get_user_from_claims(claims):
    return (
        current_session
        .query(User)
        .filter(User.id == claims['sub'])
        .first()
    )


def current_user_id():
    return current_token['sub']


def build_redirect_url(hostname, path):
    """
    Compute a redirect given a hostname and next path where

    Args:
        hostname (str): may be empty string or a bare hostname or
               a hostname with a protocal attached (https?://...)
        path (int): is a path to attach to hostname

    Return:
        string url suitable for flask.redirect
    """
    redirect_base = hostname
    # BASE_URL may be empty or a bare hostname or a hostname with a protocol
    if bool(redirect_base) and not redirect_base.startswith("http"):
        redirect_base = "https://" + redirect_base
    return redirect_base + path



def logout(next_url):
    """
    Return a redirect which another logout from IDP or the provided redirect.

    Depending on the IDP, this logout will propogate. For example, if using
    another fence as an IDP, this will hit that fence's logout endpoint.

    Args:
        next_url (str): Final redirect desired after logout
    """
    flask.current_app.logger.debug(
        'IN AUTH LOGOUT, next_url = {0}'.format(next_url))

    # propogate logout to IDP
    provider_logout = None
    provider = flask.session.get('provider')
    if provider == IdentityProvider.itrust:
        safe_url = urllib.quote_plus(next_url)
        provider_logout = (
            flask.current_app.config['ITRUST_GLOBAL_LOGOUT'] + safe_url
        )
    elif provider == IdentityProvider.fence:
        base = (
            flask.current_app.config['OPENID_CONNECT']['fence']['api_base_url']
        )
        safe_url = urllib.quote_plus(next_url)
        provider_logout = (
            base + '/logout?' + urllib.urlencode({'next': safe_url})
        )

    flask.session.clear()
    redirect_response = flask.make_response(
        flask.redirect(provider_logout or urllib.unquote(next_url))
    )
    clear_cookies(redirect_response)
    return redirect_response


def set_validated_token(*args, **kwargs):
    mocked_token = flask.current_app.config.get('MOCK_AUTH')
    if mocked_token:
        set_current_token(mocked_token)
    else:
        set_current_token(validate_jwt(*args, **kwargs))


def _get_claims_field(claims, fields, default=None):
    """
    Recursively look up a sequence of fields from a dictionary (such as claims
    from a user's JWT).

    Example:

        >>> claims = {'a': {'b': {'c': 1}}}
        >>> _get_claims_field(claims, ['a', 'b', 'c'])
        1
        >>> _get_claims_field(claims, ['a', 'x', 'y'], default='default')
        'default'

    Args:
        claims (dict): dictionary of claims from a token
        fields (List[str]): sequence of fields to look up
        default (Any): value to return if field is not found

    Return:
        Any: the field if it was found, else default
    """
    value = reduce(lambda acc, field: acc.get(field, {}), fields, claims)
    return value or default


def require_auth(*args, **kwargs):
    """
    Decorate a function to require a JWT in the request headers.

    The args/kwargs will get passed down through to
    ``fence.jwt.validate.validate_jwt``. See ``fence/jwt/validate.py`` for docs
    on that function. It also accepts additional kwargs, to
    ``authutils.token.validate.validate_jwt``.
    """

    def decorator(f):

        @wraps(f)
        def wrapper(*f_args, **f_kwargs):
            set_validated_token(*args, **kwargs)
            flask.session['username'] = _get_claims_field(
                current_token, ['context', 'user', 'name'] 
            )
            flask.session['provider'] = _get_claims_field(
                current_token, ['context', 'user', 'provider'] 
            )
            flask.session['user_id'] = current_token['sub']
            return f(*f_args, **f_kwargs)

        return wrapper

    return decorator


def require_admin(f):
    """
    Decorate a function to require that the current user has admin privileges.
    Should be used as a decorator following ``require_auth``, for example:

    .. code-block:: python

        @blueprint.route('/admin-only')
        @require_admin
        @require_auth(aud={'openid'}, purpose='access')
        def admin_endpoint():
            return 'user is admin'

    (This is because of the use of ``current_token``, which is set by
    ``require_auth``.)

    Args:
        f (Callable): a function already be decorated with ``require_auth``

    Return:
        Callable: the wrapped function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        """Wrap ``f`` to raise error if user is not authorized as admin."""
        try:
            is_admin = current_token['context']['user']['is_admin']
        except KeyError as e:
            raise JWTError('missing field in current token: {}'.format(str(e)))
        if not is_admin:
            raise Unauthorized('user is not admin')
        return f(*args, **kwargs)

    return wrapper


def admin_login_required(function):
    """Compose the login required and admin required decorators."""
    return require_auth({'admin'})(admin_required(function))
