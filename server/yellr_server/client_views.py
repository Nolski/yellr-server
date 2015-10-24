from pyramid.response import Response
from pyramid.view import view_defaults
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from .models import (
    #DBSession,
    #MyModel,
    Assignments,
    Posts,
    MediaObjects,
    Clients,
    )

import subprocess

def get_payload(request):
    try:
        payload = request.json_body
    except:
        payload = None
    return payload

def build_paging(request):
    start = 0
    count = 50
    if 'start' in request.GET and 'count' in request.GET:
        try:
            start = int(float(request.GET['start']))
            count = int(float(request.GET['count']))
            if count > 50:
                count = 50
        except:
            start = 0
            count = 50
    return start, count


def check_in(request):
    req = (
        'cuid',
        'lat',
        'lng',
        'language_code',
        'platform',
    )
    client = None
    if all(r in request.GET for r in req):
        try:
            cuid = request.GET['cuid']
            lat = float(request.GET['lat'])
            lng = float(request.GET['lng'])
            language_code = request.GET['language_code']
            platform = request.GET['platform'] 
            client = Clients.check_in(
                cuid=cuid, 
                lat=lat,
                lng=lng,
                language_code=language_code,
                platform=platform,
            )
        except:
            pass
    return client


def save_input_file(input_file):

    # generate a unique file name to store the file to
    unique = str(uuid.uuid4())
    filename = os.path.join(system_config['upload_dir'], unique)

    with open(filename, 'wb') as f:
        input_file.seek(0)
        while True:
            data = input_file.read(2<<16)
            if not data:
                break
            f.write(data)

    return filename


def process_image(base_filename):

    image_filename = ""
    preview_filename = ""

    try:

        image_filename = '{0}.jpg'.format(base_filename)
        preview_filename = '{0}p.jpg'.format(base_filename)

        # type incoming file
        mime_type = magic.from_file(base_filename, mime=True)
        allowed_image_types = [
            'image/jpeg',
            'image/png',
            'image/x-ms-bmp',
            'image/tiff',
        ]

        if not mime_type.lower() in allowed_image_types:
            raise Exception("Unsupported Image Type: %s" % mime_type)

        # convert to jpeg from whatever format it was
        try:
            subprocess.call(['convert', base_filename, image_filename])
        except Exception, ex:
            raise Exception("Error converting image: {0}".format(ex))

        #strip metadata from images with ImageMagick's mogrify
        try:
            subprocess.call(['mogrify', '-strip', image_filename])
        except Exception, ex:
            raise Exception("Error removing metadata: {0}".format(ex))

        # create preview image
        try:
            subprocess.call(['convert', image_filename, '-resize', '450', \
                '-size', '450', preview_filename])
        except Exception, ex:
            raise Exception("Error generating preview image: {0}".format(ex))

    except Exception, e:
        raise Exception(e)

    return image_filename, preview_filename


def process_video(base_filename):

    video_filename = ""
    preview_filename = ""

    try:

        # type incoming file
        mime_type = magic.from_file(base_filename, mime=True)
        allowed_image_types = [
            'video/mpeg',
            'video/mp4',
            'video/quicktime',
            'video/3gpp',
        ]

        if not mime_type.lower() in allowed_image_types:
            raise Exception("Unsupported Image Type: %s" % mime_type)

        video_filename = '{0}.mp4'.format(base_filename)

        cmd = [
            'ffmpeg',
            '-i',
            base_filename,
            '-map_metadata',
            '-1',
            '-c:v',
            'copy',
            '-c:a',
            'copy',
            video_filename,
        ]
        resp = subprocess.call(cmd)
       
        #print "\n\nCMD: {0}\n\n".format(' '.join(cmd)) 
	#print "\n\nRESP: {0}\n\n".format(resp)
 
        #
        # TODO: create preview image for video
        #

    except Exception, e:
        raise Exception(e)

    return video_filename, preview_filename


def process_audio(base_filename):

    audio_filename = ""
    preview_filename = ""

    try:

        mime_type = magic.from_file(base_filename, mime=True)
        allowed_audio_types = [
            'audio/mpeg',
            'audio/ogg',
            'audio/x-wav',
            'audio/mp4',
            'video/3gpp',
        ]

        if not mime_type.lower() in allowed_audio_types:
            raise Exception("Unsupported Audio Type: %s" % mime_type)

        audio_filename = '{0}.mp3'.format(base_filename)

        cmd = [
            'ffmpeg',
            '-i',
            base_filename,
            '-f',
            'mp3',
            '-map_metadata',
            '-1',
            #'-c:v',
            #'copy',
            #'-c:a',
            #'copy',
            audio_filename,
        ]
        resp = subprocess.call(cmd)

        print "\n\nCMD: {0}\n\n".format(' '.join(cmd))

        print "\n\nbase_filename: {0}\n\nRESP: {1}\n\n".format(base_filename, resp)
      
        #
        # TODO: generic audio picture for preview name??
        #

    except Exception, e:
        raise Exception(e)

    return audio_filename, preview_filename


@view_defaults(route_name='/api/assignments', renderer='json')
class AssignmentsAPI(object):

    def __init__(self, request):
        self.request = request
        start, count = build_paging(request)
        self.client = check_in(request)

    # [ GET ] - get local assignments
    @view_config(request_method='GET')
    def get(self):
        resp = {'assignments': []}
        if self.client:
            start, count = build_paging(self.request)
            resp = Assignments.get_all_open(client.last_lat, client.last_lng)
        else:
            self.request.response.status = 400
        return resp


@view_defaults(route_name='/api/posts', renderer='json')
class PostsAPI(object):

    post_req = (
        'assignment_id',
        'contents',
    )

    def __init__(self, request):
        self.request = request
        self.start, self.count = build_paging(request)
        self.client = check_in(request)

    # [ GET ] - get local posts
    @view_config(request_method='GET')
    def get(self):
        resp = {'posts': []}
        if self.client:
            start, count = build_paging(self.request)
            _posts = Posts.get_approved_posts(
                lat=self.client.last_lat,
                lng=self.client.last_lng,
                start=self.start,
                count=self.count,
            )
            posts = [p.to_dict(self.client.id) for p in _posts]
            resp = {'posts': posts}
        else:
            self.request.response.status = 400
        return resp

    # [ POST ] - create new post
    @view_config(request_method='POST')
    def post(self):
        resp = {'post': None}
        payload = get_payload(self.request)
        if payload and all(r in payload for r in self.post_req) and self.client:
            try:
                assignment_id = int(float(payload['assignment_id']))
            except:
                assignment_id = None
            print(self.client.id)
            print(self.client.cuid)
            post = Posts.add(
                client_id=self.client.id,
                assignment_id=assignment_id,
                lat=self.client.last_lat,
                lng=self.client.last_lng,
                language_code=self.client.language_code,
                contents=payload['contents'],
                deleted=False,
                approved=False,
                flagged=False,
            )
            resp = {'post': post.to_dict(self.client.id)}
        else:
            self.request.response.status = 400
        return resp


@view_defaults(route_name='/api/media_objects', renderer='json')
class MediaObjectsAPI(object):

    post_req = (
        'media_type',
        'post_id',
        'media_file',
    )

    def __init__(self, request):
        self.request = request

    # [ POST ] - creates media object against a post
    @view_config(request_method='POST')
    def post(self):
        resp = {'media_object': None}
        if payload and all(r in payload for r in self.post_req) and self.client:
            try:
                #filename = request.POST['media_file'].filename
                input_file = request.POST['media_file']
                base_filename = save_input_file(input_file)
                if payload['media_type'] == 'image':
                    object_file, prev_file = process_image(base_filename)
                elif payload['media_type'] == 'video':
                    object_file, prev_file = process_video(base_filename)
                elif payload['media_type'] = 'audio':
                    object_file, prev_file = process_audio(base_filename)
                else:
                    raise Exception('Invalid Media Type')
            except Exception as ex:
                self.request.response.status = 400
                resp.update('error': str(ex))
        else:
            resl.request.response.status = 400
        return resp


@view_defaults(route_name='/api/posts/{id}/vote', renderer='json')
class VoteAPI(object):

    post_req = (
        'post_id',
        'is_up_vote',
    )

    def __init__(self, request):
        self.request = request

    # [ POST ] - votes on a post
    @view_config(request_method='POST')
    def post(self):
        resp = {'vote': None}
        if payload and all(r in payload for r in self.post_req) and self.client:
            vote = Votes.register_vote(
                post_id=payload['post_id'],
                client_id=self.client.id,
                is_up_vote=payload['is_up_vote']
            )
        else:
            self.request.response.status = 400
        return resp


@view_defaults(route_name='/api/posts/{id}/flag')
class FlagAPI(object):

    post_req = (
        'post_id',
    )

    def __init__(self, request):
        self.request = request
        self.client = check_in(request)

    # [ POST ] - flags a post
    @view_config(request_method='POST')
    def post(self):
        resp = {'post': None}
        if payload and all(r in payload for r in self.post_req) and self.client:
            post = Posts.flag_post(
                post_id=payload['post_id'],
            )
            resp = {'post': post.to_dict()}
        else:
            self.request.response.status = 400
        return resp


@view_defaults(route_name='/api/clients')
class ClientsAPI(object):

    def __init__(self, request):
        self.request = request
    
    # [ GET ] - get clients profile
    @view_config(request_method='GET')
    def get(self):
        resp = {}
        return resp

    # [ PUT ] - updates a clients profile
    @view_config(request_method='PUT')
    def put(self):
        resp = {}
        return resp

    # [ DELETE ] - marks the client as deleted ( forgotten )
    @view_config(request_method='DELETE')
    def delete(self):
        resp = {}
        
        return resp
