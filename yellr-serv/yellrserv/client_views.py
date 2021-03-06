import utils
import uuid

import markdown

from pyramid.response import Response
from pyramid.view import view_config

import client_utils

from .models import (
    DBSession,
    Clients,
    Assignments,
    Languages,
)

def get_client_info(request):

    #lat = 39.9500
    #lng = -75.1667

    nash_lat = 36.1667
    nash_lng = -86.7833    
    roc_lat = 43.1656
    roc_lng = -77.6114

    #lat = nash_lat
    #lng = nash_lng

    lat = roc_lat
    lng = roc_lng

    try:
        if 'lat' in request.cookies and 'lng' in request.cookies:
            lat = float(request.cookies['lat'])
            lng = float(request.cookies['lng'])
            if lat > 90 or lat < -90 or lng > 180 or lng < -180:
                #lat = 43.1656
                #lng = -77.6114
                #lat = nash_lat
                #lng = lash_lng
                lat = roc_lat
                lng = roc_lng
    except:
        pass
    

    start = 0
    count = 75;
    try:
        if 'start' in request.GET and 'count' in request.GET:
            start = int(float(request.GET['start']))
            count = int(float(request.GET['count']))
            if count > 75:
                count = 75
    except:
        pass

    language_code = 'en'
    try:
        if 'language_code' in request.GET:
            lc = request.GET['language_code']
            if lc in ['en', 'es']:
                language_code = lc
    except:
        pass

    cuid = str(uuid.uuid4())
    new_client = True
    try:
        if 'cuid' in request.cookies:
            cuid = request.cookies['cuid']
            new_client = False
    except:
        pass

    return lat, lng, start, count, language_code, cuid, new_client   

@view_config(route_name='index', renderer='templates/one-pager-index.mak')
def index(request):

    return {}

@view_config(route_name='robots')
def robots(request):

    return Response('User-agent: *\nAllow: /\n', content_type='text/plain')

@view_config(route_name='/local', renderer='templates/new/local.mak')
def local(request):

    lat, lng, start, count, language_code, cuid, new_client = get_client_info(request)

    client = Clients.get_client_by_cuid(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    Clients.check_in(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    posts = client_utils.get_approved_posts(
        client_id = client.client_id,
        language_code = language_code,
        lat = lat,
        lng = lng,
        start = start,
        count = count,
    )

    return {'new_client': new_client, 'cuid': cuid, 'client': client, 'lat': lat, 'lng': lng, 'posts': posts}

@view_config(route_name='/view', renderer='templates/new/view.mak')
def view(request):

    valid = False
    post = None

    if 'post_id' in request.GET:
        post_id = request.GET['post_id']

        post = client_utils.get_post(
            post_id,
        )

       

        if not post is None and post['approved'] and not post['deleted']:
            valid = True

    return {'valid': valid, 'post': post}

@view_config(route_name='/assignments', renderer='templates/new/assignments.mak')
def assignments(request):

    lat, lng, start, count, language_code, cuid, new_client = get_client_info(request)

    client = Clients.get_client_by_cuid(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    Clients.check_in(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    assignments = client_utils.get_assignments(
        client_id = client.client_id,
        language_code = language_code,
        lat = lat,
        lng = lng,
    )

    return {'new_client': new_client, 'cuid': cuid, 'client': client, 'lat': lat, 'lng': lng, 'assignments': assignments}

@view_config(route_name='/stories', renderer='templates/new/stories.mak')
def stories(request):

    lat, lng, start, count, language_code, cuid, new_client = get_client_info(request)

    client = Clients.get_client_by_cuid(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    Clients.check_in(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    stories = client_utils.get_stories(
        language_code = language_code,
        lat = lat,
        lng = lng,
        start = start,
        count = count,
    )

    return {'new_client': new_client, 'cuid': cuid, 'client': client, 'lat': lat, 'lng': lng, 'stories': stories}

@view_config(route_name='/post', renderer='templates/new/post.mak')
def post(request):

    lat, lng, start, count, language_code, cuid, new_client = get_client_info(request)

    is_response = False
    assignment_id = 0
    question_text = ''
    question_description = ''
    try:
        if 'assignment_id' in request.GET:
            assignment_id = int(float(request.GET['assignment_id']))
            if assignment_id < 1:
                raise Exception('Invalid Assignment ID')
            is_response = True
    except:
        is_response = False
        pass

    if is_response == True:
        language = Languages.get_from_code(
            session = DBSession,
            language_code = language_code,
        )
        assignment, question = Assignments.get_with_question(
            session = DBSession,
            assignment_id = assignment_id,
            language_id = language.language_id,
        )
        if assignment == None or question == None:
            is_response = False
        else:
            question_text = question.question_text
            question_description = question.description
            
    client = Clients.get_client_by_cuid(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    Clients.check_in(
        session = DBSession,
        cuid = cuid,
        lat = lat,
        lng = lng,
    )

    return {
        'new_client': new_client,
        'cuid': cuid,
        'client': client,
        'lat': lat,
        'lng': lng,
        'language_code': language_code,
        'is_response': is_response,
        'assignment_id': assignment_id,
        'question_text': question_text,
        'question_description': question_description,
    }

