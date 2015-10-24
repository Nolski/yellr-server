from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from pyramid.session import SignedCookieSessionFactory

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')

    my_session_factory = SignedCookieSessionFactory('max_secret_yellr_password')
    config.set_session_factory(my_session_factory)

    config.add_static_view('static', 'static', cache_max_age=3600)

    #config.add_route('home', '/')


    #
    # Client REST end-points
    #

    # [ GET ] - get's local assignments
    config.add_route('/api/assignments', '/api/assignments')
    
    # [ GET ] - get's local posts
    # [ POST ] - posts new post
    config.add_route('/api/posts', '/api/posts')

    # [ POST ] - creates media object against a post
    config.add_route('/api/media_objects', '/api/media_objects')

    # [ POST ] - votes on a post
    config.add_route('/api/posts/{id}/vote', '/api/posts/{id}/vote')

    # [ POST ] - flags a post
    config.add_route('/api/posts/{id}/flag', '/api/posts/{id}/flag')

    # [ GET ] - get's clients profile
    # [ PUT ] - updates a clients profile
    # [ DELETE ] - marks the client as deleted ( forgotten )
    config.add_route('/api/clients', '/api/clients')


    # 
    # Admin REST end-points
    # 
 
    config.add_route('/api/admin/login', '/api/admin/login')
    config.add_route('/api/admin/logout', '/api/admin/logout')
    config.add_route('/api/admin/posts', '/api/admin/posts')
    config.add_route('/api/admin/posts/{id}', '/api/admin/posts/{id}')


    config.scan()
    return config.make_wsgi_app()