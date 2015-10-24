'''
import os
import json
import uuid
import datetime
from time import strftime, sleep
from random import randint
import hashlib
from random import randint

import transaction

#from geoalchemy2 import *

from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    DateTime,
    Date,
    Boolean,
    Float,
    CHAR,
    BLOB,
    UnicodeText,
    )

from sqlalchemy import ForeignKey

from sqlalchemy import (
    update,
    desc,
    func,
    text,
    distinct,
    cast,
    or_,
    and_,
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
)

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(
    extension=ZopeTransactionExtension(keep_session=True),
    expire_on_commit=False))
Base = declarative_base()
'''

from uuid import uuid4
import hashlib

from time import sleep
from random import randint
import datetime

from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType
from sqlalchemy import (
    Column,
    cast,
    Date,
    CHAR,
    ForeignKey,
    Integer,
    Float,
    Boolean,
    UnicodeText,
    DateTime,
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    relationship,
    scoped_session,
    sessionmaker,
)

from zope.sqlalchemy import ZopeTransactionExtension
import transaction

DBSession = scoped_session(sessionmaker(
    extension=ZopeTransactionExtension(keep_session=True),
    expire_on_commit=False))
Base = declarative_base()


class TimeStampMixin(object):
    creation_datetime = Column(DateTime, server_default=func.now())
    modified_datetime = Column(DateTime, server_default=func.now())

class CreationMixin():

    id = Column(CHAR(32), primary_key=True)

    @classmethod
    def add(cls, **kwargs):
        with transaction.manager:
            thing = cls(**kwargs)
            if thing.id is None:
                thing.id = str(uuid4())
            DBSession.add(thing)
            transaction.commit()
        return thing

    @classmethod
    def get_all(cls):
        with transaction.manager:
            things = DBSession.query(
                cls,
            ).all()
        return things

    @classmethod
    def get_paged(cls, start=0, count=50):
        with transaction.manager:
            things = DBSession.query(
                cls,
            ).slice(start, count).all()
        return things

    @classmethod
    def get_by_id(cls, id):
        with transaction.manager:
            thing = DBSession.query(
                cls,
            ).filter(
                cls.id == id,
            ).first()
        return thing

    @classmethod
    def delete_by_id(cls, id):
        with transaction.manager:
            thing = cls.get_by_id(id)
            if thing is not None:
                DBSession.delete(thing)
            transaction.commit()
        return thing

    @classmethod
    def update_by_id(cls, id, **kwargs):
        with transaction.manager:
            keys = set(cls.__dict__)
            thing = cls.get_by_id(id)
            if thing is not None:
                for k in kwargs:
                    if k in keys:
                        setattr(thing, k, kwargs[k])
                DBSession.add(thing)
                transaction.commit()
        return thing

    @classmethod
    def reqkeys(cls):
        keys = []
        for key in cls.__table__.columns:
            if '__required__' in type(key).__dict__:
                keys.append(str(key).split('.')[1])
        return keys

    def to_dict(self):
        return {
            'id': str(self.id),
            'creation_datetime': str(self.creation_datetime),
        }


class UserTypes(Base, CreationMixin, TimeStampMixin):

    """
    Different types of users.  Administrators have the most access/privs,
    Moderators have the next leve, Subscribers the next, and then users only
    have the ability to post and view.
    """

    __tablename__ = 'usertypes'
    #user_type_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText, nullable=False)

    @classmethod
    def get_from_name(cls, session, name):
        with transaction.manager:
            user_type = DBSession.query(
                UserTypes
            ).filter(
                UserTypes.name == name
            ).first()
        return user_type

    '''
    @classmethod
    def add_user_type(cls, session, name, description):
        with transaction.manager:
            user_type = UserTypes(
                name = name,
                description = description,
            )
            session.add(user_type)
            transaction.commit()
        return user_type
    '''

    def to_dict(self):
        resp = super.to_dict(UserTypes, self).to_dict()
        resp.update(
            name = self.name,
            description = self.description,
        )
        return resp

class Users(Base, CreationMixin, TimeStampMixin):

    """
    This is the user table.  It holds information for administrators, moderators,
    subscribers, and users.  If the type is a user, than a uniqueid is used to
    idenfity them.  if the user wants to be verified then, then the rest of the
    information is used.  All fields are used for admins, mods, and subs.
    """

    __tablename__ = 'users'
    #user_id = Column(Integer, primary_key=True)
    #user_type_id = Column(Integer, ForeignKey('usertypes.id'))
    user_type = Column(UnicodeText, nullable=False)

    #client_id = Column(UnicodeText)

    username = Column(UnicodeText, nullable=False)
    first = Column(UnicodeText, nullable=False)
    last = Column(UnicodeText, nullable=False)
    #organization = Column(UnicodeText)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    email = Column(UnicodeText, nullable=False)
    pass_salt = Column(UnicodeText, nullable=False)
    pass_hash = Column(UnicodeText, nullable=False)
    user_geo_fence_id = Column(Integer,
        ForeignKey('user_geo_fences.id'), nullable=True)
    token = Column(UnicodeText, nullable=True)
    token_expire_datetime = Column(DateTime, nullable=True)

    assignments = relationship('Assignments', backref='author', lazy='joined')


    @classmethod
    def create_new_user(cls, user_type, user_geo_fence_id, \
            username, password, first, last, email, organization_id):
        user = None
        with transaction.manager:
            salt_bytes = str(uuid4()).encode('utf-8')
            pass_bytes = password.encode('utf-8')
            pass_hash = hashlib.sha256(pass_bytes + salt_bytes).hexdigest()
            user = Users.add(
                user_type = user_type,
                user_geo_fence_id = user_geo_fence_id,
                first = first,
                last = last,
                #organization = organization,
                organization_id = organization_id,
                email = email,
                username = username,
                pass_salt = salt_bytes,
                pass_hash = pass_hash,
                token = None,
                token_expire_datetime = None,
            )
        return user

    
    @classmethod
    def get_by_username(cls, username):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).filter(
                Users.username == username,
            ).first()
        return euser
    

    '''
    @classmethod
    def get_organization_from_user_id(cls, session, user_id):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).filter(
                Users.user_id == user_id,
            ).first()
        return user.organization
    '''

    '''
    @classmethod
    def get_from_user_type_name(cls, session, user_type_name):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).join(
                UserTypes,
            ).filter(
                Users.user_type_id == UserTypes.user_type_id,
                UserTypes.name == user_type_name,
            ).first()
        return user
    '''

    '''
    @classmethod
    def get_from_user_id(cls, session, user_id):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).filter(
                Users.user_id == user_id,
            ).first()
        return user
    '''

    @classmethod
    def get_from_token(cls, token):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).filter(
                Users.token == token,
                Users.token != None,
                Users.token != "",
            ).first()
        return user

    '''
    @classmethod
    def get_all(cls, session):
        with transaction.manager:
            users = DBSession.query(
                Users.user_id,
                Users.user_type_id,
                Users.user_geo_fence_id,
                Users.verified,
                Users.client_id,
                Users.first_name,
                Users.last_name,
                Users.organization,
                Users.email,
                UserTypes.name,
                UserTypes.description,
            ).join(
                UserTypes,
            ).filter(
                Users.user_type_id == UserTypes.user_type_id,
            ).all()
        return users
    '''

    
    @classmethod
    def authenticate(cls, username, password):
        with transaction.manager:
            user = DBSession.query(
                Users,
            ).filter(
                Users.username == username,
            ).first()
            org = None
            token = None
            if user is not None:
                pass_bytes = password.encode('utf-8')
                salt_bytes = user.pass_salt
                pass_hash = hashlib.sha256(pass_bytes + salt_bytes).hexdigest()
                if (user.pass_hash == pass_hash):
                    token = str(uuid4())
                    user.token = token
                    user.token_expire_datetime = datetime.datetime.now() + \
                        datetime.timedelta(hours=24)
                    DBSession.add(user)
                    transaction.commit()
                    #org = Organizations.get_from_id(session, user.organization_id)
        return user


    @classmethod
    def validate_token(cls, token):
        user = Users.get_from_token(token)
        valid = False
        if user != None:
            if user.token_expire_datetime > datetime.datetime.now():
                valid = True
        return valid, user


    @classmethod
    def invalidate_token(cls, token):
        with transaction.manager:
            user = Users.get_from_token(token)
            if user != None:
                user.token = None
                DBSession.add(user)
                transaction.commit()
        return user


    @classmethod
    def change_password(cls, user, old_password, new_password):
        with transaction.manager:
            #user = DBSession.query(
            #    Users,
            #).filter(
            #    Users.user_name == username,
            #).first()
            old_pass_bytes = old_password.encode('utf-8')
            old_salt_bytes = user.pass_salt.encode('utf-8')
            old_pass_hash = hashlib.sha256(
                old_pass_bytes + old_salt_bytes
            ).hexdigest()
            success = False
            if old_pass_hash == user.pass_hash:
                pass_salt = str(uuid4())
                pass_hash = hashlib.sha256('{0}{1}'.format(
                    new_password,
                    pass_salt
                )).hexdigest()
                user.pass_salt = pass_salt
                user.pass_hash = pass_hash
                DBSession.add(user)
                transaction.commit()
                success = True
        return user, success


    def to_dict(self):
        resp = super(Users, self).to_dict()
        resp.update(
            #user_id = self.user_id,
            username = self.username,
            first = self.first,
            last = self.last,
            organization = self.organization.to_dict() if self.organization != None else None,
            email = self.email, 
            #pass_salt = 
            #pass_hash = 
            user_geo_fence = self.geo_fence.to_dict() if self.geo_fence != None else None,
            token = self.token, 
            token_expire_datetime = str(self.token_expire_datetime),
        )
        return resp

class UserGeoFences(Base, CreationMixin, TimeStampMixin):

    """
    Admins, Moderators, and Subscribers all have default geo fences that they
    are set to.  That is, that they can not post of view outside of this fence.
    """

    __tablename__ = 'user_geo_fences'
    #user_geo_fence_id = Column(Integer, primary_key=True)
    top_left_lat = Column(Float)
    top_left_lng = Column(Float)
    bottom_right_lat = Column(Float)
    bottom_right_lng = Column(Float)
    center_lat = Column(Float)
    center_lng = Column(Float)

    users = relationship('Users', backref='geo_fence', lazy='joined')

    ''''
    @classmethod
    def create_fence(cls, session, top_left_lat, top_left_lng, \
            bottom_right_lat, bottom_right_lng):
        with transaction.manager:
            fence = UserGeoFences(
               top_left_lat = top_left_lat,
               top_left_lng = top_left_lng,
               bottom_right_lat = bottom_right_lat,
               bottom_right_lng = bottom_right_lng,
            )
            session.add(fence)
            transaction.commit()
        return fence
    '''

    '''
    @classmethod
    def get_fence_from_user_id(cls, session, user_id):
        with transaction.manager:
            fence = DBSession.query(
                UserGeoFences,
            ).join(
                Users, Users.user_geo_fence_id == \
                    UserGeoFences.user_geo_fence_id,
            ).filter(
                Users.user_id == user_id,
            ).first()
        return fence
    '''

    def to_dict(self):
        resp = super(UserGeoFences, self).to_dict()
        resp.update(
            #user_geo_fence_id = self.user_geo_fence_id,
            top_left_lat = self.top_left_lat,
            top_left_lng = self.top_left_lng,
            bottom_right_lat = self.bottom_right_lat,
            bottom_right_lng = self.bottom_right_lng,
            center_lat = self.center_lat,
            center_lng = self.center_lng,
        )
        return resp

class Clients(Base, CreationMixin, TimeStampMixin):

    """
    Clients are users of the mobile app(s)
    """

    __tablename__ = 'clients'
    #client_id = Column(Integer, primary_key=True)
    cuid = Column(UnicodeText, nullable=False)

    first = Column(UnicodeText, nullable=True)
    last = Column(UnicodeText, nullable=True)
    email = Column(UnicodeText, nullable=True)
    pass_hash = Column(UnicodeText, nullable=True)
    pass_salt = Column(UnicodeText, nullable=True)
    verified = Column(Boolean, nullable=False)
    verified_datetime = Column(DateTime, nullable=True)

    #creation_datetime = Column(DateTime)
    #last_check_in_datetime = Column(DateTime, nullable=False)

    #home_zipcode_id = Column(Integer, ForeignKey('zipcodes.id'))

    last_lat = Column(Float, nullable=False)
    last_lng = Column(Float, nullable=False)

    #post_view_count = Column(Integer)
    #post_used_count = Column(Integer)

    language_code = Column(UnicodeText, nullable=False)
    platform = Column(UnicodeText, nullable=False)

    deleted = Column(Boolean, nullable=False)

    '''
    @classmethod
    def create_new_client(cls, session, cuid, lat, lng):
        with transaction.manager:
            client = Clients(
                cuid = cuid,
                first_name = None,
                last_name = None,
                email = None,
                passhash = None,
                passsalt = None,
                verified = False,
                verified_datetime = None,
                creation_datetime = datetime.datetime.now(),
                last_check_in_datetime = datetime.datetime.now(),
                last_lat = lat,
                last_lng = lng,
                post_view_count = 0,
                post_used_count = 0,
            )
            session.add(client)
            transaction.commit()
        return client
    '''

    
    @classmethod
    def check_in(cls, cuid, lat, lng, language_code, platform):
        with transaction.manager:
            #print "check_in(): cuid: {0}".format(cuid)
            #client = DBSession.query(
            #    Clients,
            #).filter(
            #    Clients.cuid == cuid,
            #).first()
            #print "check_in(): client.cuid: {0}, client.client_id: {1}".format(client.cuid, client.client_id)
            client = Clients.get_by_cuid(cuid, lat, lng, language_code, platform)
            client.last_lat = lat
            client.last_lng = lng
            client.modified_datetime = datetime.datetime.now()
            client.platform = platform
            DBSession.add(client)
            transaction.commit()
        return client

    @classmethod
    def get_by_cuid(cls, cuid, lat, lng, language_code, platform, create=True):
        client = None
        with transaction.manager:
            client = DBSession.query(
                Clients,
            ).filter(
                Clients.cuid == cuid,
            ).first()
            transaction.commit()

        if not client and create == True:

            #
            # This is max gross, and is terrible.  Was done because when a
            # client first comes on line, the android app hammers the server
            # with lots of requests all in a row.  SQLAlchemy serves these up
            # in some kind of queue, which causes SELECT INSERT SELECT INSERT
            # rather than SELECT INSERT SELECT <none>
            #
            # we wait some random amount of time, in hopes that any other
            # 'first' time request, creates the user before we do, so we 
            # don't double create it.
            #
            # possible solutions in the future are to use a store proc that
            # locks the table.
            sleep_time = float(float(randint(1000,2000))/float(1000.0))
            sleep(sleep_time)

            # we do this SELECT again to see if the client has been created in
            # the random hold-off time.
            client = DBSession.query(
                Clients,
            ).filter(
                Clients.cuid == cuid,
            ).first()
            if not client:
                client = Clients.add(
                    cuid=cuid,
                    first='',
                    last='',
                    email='',
                    pass_hash='',
                    pass_salt='',
                    verified=False,
                    verified_datetime=None,
                    last_lat=lat,
                    last_lng=lng,
                    language_code=language_code,
                    platform=platform,
                    deleted=False,
                )
        return client

    @classmethod
    def verify_client(cls, cuid, first_name, last_name, email, \
            password):
        with transaction.manager:
            client = DBSession.query(
                Clients,
            ).filter(
                Clients.cuid,
            ).first()
            client.first_name = first_name
            client.last_name = last_name
            client.email = email
            pass_bytes = password.encode('utf-8')
            salt_bytes =hashlib.sha256(str(uuid4()).encode('utf-8'))
            client.passhash = hashlib.sha256('{0}{1}'.format(
                pass_bytes,
                salt_bytes
            )).hexdigest()
            client.pass_salt = salt_bytes
            client.verified = True
            client.verified_datetime = datetime.datetime.now()
            DBSession.add(client)
            transaction.commit()
        return client

    '''
    @classmethod
    def increment_view_count(cls, session, client_id):
        with transaction.manager:
            client = DBSession.query(
                Clients,
            ).filter(
                Clients.client_id == client_id,
            ).first()
            client.post_view_count += 1
            session.add(client)
            transaction.commit()
        return client
    '''

    '''
    @classmethod
    def increment_used_count(cls, session, cuid):
        with transaction.manager:
            client = DBSession.query(
                Clients,
            ).filter(
                Clients.cuid == cuid,
            ).first()
            client.post_used_count += 1
            session.add(client)
            transaction.commit()
        return client
    '''

    def to_dict(self):
        resp = super(Clients, self).to_dict()
        resp.update(
            cuid = self.cuid,
            first = self.first,
            last = self.last,
            email = self.email,
            #passhash =
            #passsalt =
            verified = self.verified,
            verified_datetime = str(self.verified_datetime),
            creation_datetime = str(self.creation_datetime),
            #last_check_in_datetime = str(self.last_checking_datetime),
            #home_zipcode_id = self.home_zipcode_id,
            last_lat = self.last_lat,
            last_lng = self.last_lng,
            #post_view_count = self.post_view_count,
            #post_used_count = self.post_used_count,
            platform = self.platform,
        )
        return resp

class Assignments(Base, CreationMixin, TimeStampMixin):

    """
    An assignment is created by a moderator and available for users to pull down.
    Assignments hold a publish date, an experation date, and a geofence
    within them, as well as a user id to tie it to a specific user.
    """

    __tablename__ = 'assignments'
    #assignment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    #publish_datetime = Column(DateTime)
    expire_datetime = Column(DateTime)
    name = Column(UnicodeText)
    #assignment_unique_id = Column(UnicodeText)
    top_left_lat = Column(Float)
    top_left_lng = Column(Float)
    bottom_right_lat = Column(Float)
    bottom_right_lng = Column(Float)
    use_fence = Column(Boolean)
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=True)

    questions = relationship('Questions', backref='assignment', lazy='joined')

    #posts = relationship('Posts', backref='assignment', lazy='joined')

    '''
    @classmethod
    def get_by_assignment_id(cls, session, assignment_id):
        assignment = DBSession.query(
            QuestionAssignments
        ).filter(
            QuestionAssignments.assignment_id == assignment_id
        ).first()
        return assignment
    '''

    '''
    @classmethod
    def get_with_question(cls, session, assignment_id, language_id):
        assignment = Assignments.get_by_assignment_id(session,assignment_id)
        question = DBSession.query(
            Questions
        ).join(
            QuestionAssignments,QuestionAssignments.question_id == \
                Questions.question_id,
        ).filter(
            QuestionAssignments.assignment_id == assignment_id,
            Questions.language_id == language_id
        ).filter().first()
        return (assignment,question)
    '''

    '''
    @classmethod
    def get_all_open(cls, lat, lng):
        with transaction.manager:
            assignments = DBSession.query(
                Assignments,
            ).filter(
                Assignments.top_left_lat + 90 > lat + 90,
                Assignments.top_left_lng + 180 < lng + 180,
                Assignments.bottom_right_lat + 90 < lat + 90,
                Assignments.bottom_right_lng + 180 > lng + 180,
                cast(Assignments.expire_datetime,Date) >= \
                    cast(datetime.datetime.now(),Date),
            ).all()
        return assignments
    '''

    @classmethod
    def get_all_open(cls, lat, lng):
        with transaction.manager:
           assignments = DBSession.query(
               Assignments,
               #func.count(Posts.post_id),
           ).outerjoin(
               Posts,Posts.assignment_id == Assignments.id,
           ).filter(
                # we add offsets so we can do simple comparisons
                Assignments.top_left_lat + 90 > lat + 90,
                Assignments.top_left_lng + 180 < lng + 180,
                Assignments.bottom_right_lat + 90 < lat + 90,
                Assignments.bottom_right_lng + 180 > lng + 180,
                cast(Assignments.expire_datetime, Date) >= \
                        cast(datetime.datetime.now(), Date),
            ).group_by(
                Assignments.id

            ).all()
        return assignments

    '''
    @classmethod
    def _build_assignments_query(cls, session, client_id=0):
        if True:

            #dialect = query.session.bind.dialect
            #q =  session.query(
            #    func.count(Posts),
            #).filter(
            #    Posts.assignment_id == Assignments.assignment_id,
            #)
            #count_sql = "(%s) as count_1" % str(q.statement.compile(dialect=q.session.bind.dialect))

            #count_sql = "(SELECT Count(*) FROM posts WHERE posts.assignment_id = assignments.assignment_id) AS count_1"

            assignments_query = DBSession.query(
                Assignments.assignment_id,
                Assignments.publish_datetime,
                Assignments.expire_datetime,
                Assignments.name,
                Assignments.top_left_lat,
                Assignments.top_left_lng,
                Assignments.bottom_right_lat,
                Assignments.bottom_right_lng,
                Assignments.use_fence,
                Assignments.collection_id,
                Users.organization_id,
                Organizations.name,
                Organizations.description,
                Questions.question_text,
                Questions.question_type_id,
                Questions.description,
                Questions.answer0,
                Questions.answer1,
                Questions.answer2,
                Questions.answer3,
                Questions.answer4,
                Questions.answer5,
                Questions.answer6,
                Questions.answer7,
                Questions.answer8,
                Questions.answer9,
                Languages.language_id,
                Languages.language_code,
                func.count(distinct(Posts.post_id)),
                session.query(
                    distinct(Posts),
                ).filter(
                    Assignments.assignment_id == Posts.assignment_id,
                    Posts.client_id == client_id,
                ).correlate(
                    Assignments,
                ).exists().label('has_responded'), 
            ).join(
                Users, Users.user_id == Assignments.user_id,
            ).join(
                Organizations, Users.organization_id == \
                    Organizations.organization_id,
            ).join(
                QuestionAssignments,
                QuestionAssignments.assignment_id == \
                    Assignments.assignment_id,
            ).join(
                Questions,Questions.question_id == \
                    QuestionAssignments.question_id,
            ).join(
                Languages,Languages.language_id == \
                    Questions.language_id,
            ).outerjoin(
                Posts, Posts.assignment_id == \
                    Assignments.assignment_id,
            ).group_by(
                Assignments.assignment_id,
                #Users.user_id,
                #Questions.question_id,
                #Languages.language_id,
            #).outerjoin(
            #    Posts, Posts.assignment_id == \
            #        Assignments.assignment_id,
            #).filter(
            #    Posts.assignment_id == \
            #)       Assignments.assignment_id
            #).filter(
            #    Posts.deleted == False,
            ).order_by(
                desc(Assignments.assignment_id),
            )

            #print "\n\nAssignments SQL:\n\n"
            #print str(assignments_query)
            #print "\n\n"

        return assignments_query
    '''

    '''
    @classmethod
    def get_all_with_questions(cls, session, expired=False, \
            start=0, count=0):
        with transaction.manager:
            assignments_query = Assignments._build_assignments_query(
                session = DBSession.
            )
            if expired:
               assignments_query = assignments_query.filter(
                    cast(Assignments.expire_datetime,Date) < \
                        cast(datetime.datetime.now(),Date),
                )
            else:
                assignments_query = assignments_query.filter(
                    cast(Assignments.expire_datetime,Date) >= \
                        cast(datetime.datetime.now(),Date),
                )
            assignments = assignments_query.slice(
                start, 
                start+count
            ).all()
        return assignments #, total_assignment_count
    '''

    '''
    @classmethod
    def get_all_open_with_questions(cls, session, language_code, lat, lng, client_id=0):
        with transaction.manager:
            assignments = Assignments._build_assignments_query(
                session = DBSession.
                client_id = client_id
            ).filter(
                # we add offsets so we can do simple comparisons
                Assignments.top_left_lat + 90 > lat + 90,
                Assignments.top_left_lng + 180 < lng + 180,
                Assignments.bottom_right_lat + 90 < lat + 90,
                Assignments.bottom_right_lng + 180 > lng + 180,
                Languages.language_code == language_code,
                cast(Assignments.expire_datetime,Date) >= cast(datetime.datetime.now(),Date),
            ).all() #.slice(start, start+count).all()
        return assignments
    '''

    '''
    @classmethod
    def create_from_http(cls, session, user_id, name, life_time, top_left_lat, \
            top_left_lng, bottom_right_lat, bottom_right_lng, use_fence=True):
        with transaction.manager:
            #user = Users.get_from_token(session, token)
            assignment = None
            #if user != None:
            if True:
                assignment = Assignments(
                    user_id = user_id,
                    publish_datetime = datetime.datetime.now(),
                    expire_datetime = datetime.datetime.now() + \
                        datetime.timedelta(hours=life_time),
                    name = name,
                    #assignment_unique_id = str(uuid4()),
                    top_left_lat = top_left_lat,
                    top_left_lng = top_left_lng,
                    bottom_right_lat = bottom_right_lat,
                    bottom_right_lng = bottom_right_lng,
                    use_fence = use_fence,
                )
                session.add(assignment)
                transaction.commit()
        return assignment
    '''

    
    @classmethod
    def set_collection(cls, assignment_id, collection_id):
        with transaction.manager:
            assignment = DBSession.query(
                Assignments,
            ).filter(
                Assignments.assignment_id == assignment_id,
            ).first()
            assignment.collection_id = collection_id

            DBSession.add(assignment)
            transaction.commit()

        return assignment

    '''
    @classmethod
    def update_assignment(cls, session, assignment_id, name, life_time, \
            top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, \
            use_fence=True):
        with transaction.manager:
            assignment = DBSession.query(
                Assignments,
            ).filter(
                Assignments.assignment_id == assignment_id,
            ).first()
            assignment.name = name
            expire_datetime = assignment.publish_datetime + \
                datetime.timedelta(hours=life_time)
            assignment.expire_datetime = expire_datetime
            assignment.top_left_lat = top_left_lat
            assignment.top_left_lng = top_left_lng
            assignment.bottom_right_lat = bottom_right_lat
            assignment.bottom_right_lng = bottom_right_lng
            assignment.use_fence = use_fence
            session.add(assignment)
            transaction.commit()
        return assignment
    '''

    '''
    @classmethod
    def get_poll_results(self, session, assignment_id):
        results = DBSession.query(
            Assignments,
            session.query(
                Posts,
                #distinct(Posts),
            ).join(
                PostMediaObjects, PostMediaObjects.post_id == \
                    Posts.post_id,
            ).join(
                Questions, QuestionAssignments.question_id == \
                    Questions.question_id,
            ).filter(
                Assignments.assignment_id == Posts.assignment_id,
                #Posts.client_id == client_id,
                MediaObjects.media_text == Questions.answer0,
            #).correlate(
            #    Assignments,
            ).count().label('answer0_count'),
        )
        #print results
        return results 
    '''

    def to_dict(self, client_id=None, simple=False):
        resp = super(Assignments, self).to_dict()
        resp.update(
            #assignment_id = self.assignment_id,
            #user_id = self.user_id,
            author = self.author.to_dict() if not simple else {},
            #publish_datetime = str(self.publish_datetime),
            expire_datetime = str(self.expire_datetime),
            name = self.name,
            top_left_lat = self.top_left_lat,
            top_left_lng = self.top_left_lng,
            bottom_right_lat = self.bottom_right_lat,
            bottom_right_lng = self.bottom_right_lng,
            #use_fence = self.use_fence,
            collection_id = self.collection_id if not simple else 0,
            questions = [q.to_dict() for q in self.questions],
            response_count = len(self.posts),
        )
        if client_id != None:
            resp.update(
                has_responded = any(p.client_id == client_id for p in self.posts),
            )
        return resp 

'''
class QuestionTypes(Base):

    """
    A collection of different types of questions.  This can be free text,
    multiple choice, etc.
    """

    __tablename__ = 'questiontypes'
    #question_type_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    questions = relationship('Questions', backref='question_type', lazy='joined')

    @classmethod
    def get_from_type(cls, name):
        with transaction.manager:
            question_type = DBSession.query(
                QuestionTypes,
            ).filter(
                QuestionTypes.name == name,
            ).first()
        return question_type

    """
    @classmethod
    def get_all(cls, session):
        with transaction.manager:
            question_types = DBSession.query(
                QuestionTypes.question_type_id,
                QuestionTypes.question_type,
                QuestionTypes.question_type_description,
            ).all()
        return question_types
    """

    """
    @classmethod
    def add_question_type(cls, session, question_type, question_type_description):
        with transaction.manager:
            question_type = QuestionTypes(
                question_type = question_type,
                question_type_description = question_type_description,
            )
            session.add(question_type)
            transaction.commit()
        return question_type
    """

    def to_dict(self):
        resp = super(QuestionTypes, self).to_dict()
        resp = dict(
            name = self.name,
            description = self.description,
        )
        return resp
'''


class Questions(Base, CreationMixin, TimeStampMixin):

    """
    A list of questions that assignments are tied to.  Each question has a language with
    it, thus the same question in multiple languages may exist.  There are 10 possible
    answer fields as to keep our options open.  Question type is used by the client
    on how to display the answer fields.
    """

    __tablename__ = 'questions'
    #question_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    #language_id = Column(Integer, ForeignKey('languages.language_id'))
    language_code = Column(UnicodeText)
    question_text = Column(UnicodeText)
    description = Column(UnicodeText)
    #question_type_id = Column(Integer, ForeignKey('questiontypes.question_type_id'))
    question_type = Column(UnicodeText)
    answer0 = Column(UnicodeText)
    answer1 = Column(UnicodeText)
    answer2 = Column(UnicodeText)
    answer3 = Column(UnicodeText)
    answer4 = Column(UnicodeText)
    answer5 = Column(UnicodeText)
    answer6 = Column(UnicodeText)
    answer7 = Column(UnicodeText)
    answer8 = Column(UnicodeText)
    answer9 = Column(UnicodeText)

    assignment_id = Column(Integer, ForeignKey('assignments.id'))

    '''
    @classmethod
    def add_question(cls, session, user_id, language_code, question_text,
            description, question_type, answers):
        with transaction.manager:
            #user = Users.get_from_token(session, token)
            question = None
            if len(answers) == 10:
                language = Languages.get_from_code(session, language_code)
                question_type = QuestionTypes.get_from_type(
                    session,
                    question_type
                )
                question = Questions(
                    user_id = user_id,
                    language_id = language.language_id,
                    question_text = question_text,
                    description = description,
                    question_type_id = question_type.question_type_id,
                    answer0 = answers[0],
                    answer1 = answers[1],
                    answer2 = answers[2],
                    answer3 = answers[3],
                    answer4 = answers[4],
                    answer5 = answers[5],
                    answer6 = answers[6],
                    answer7 = answers[7],
                    answer8 = answers[8],
                    answer9 = answers[9],
                )
                session.add(question)
                transaction.commit()
        return question
    '''

    '''
    @classmethod
    def update_question(cls, session, question_id, language_id, \
            question_text, description, question_type_id, answers):
        with transaction.manager:
            question = DBSession.query(
                Questions,
            ).filter(
                Questions.question_id == question_id,
            ).first()
            question.language_id = language_id
            question.question_text = question_text
            question.description = description
            question.question_type_id = question_type_id
            question.answer0 = answers[0]
            question.answer1 = answers[1]
            question.answer2 = answers[2]
            question.answer3 = answers[3]
            question.answer4 = answers[4]
            question.answer5 = answers[5]
            question.answer6 = answers[6]
            question.answer7 = answers[7]
            question.answer8 = answers[8]
            question.answer9 = answers[9]
            session.add(question)
            transaction.commit()
        return question
    '''

    def to_dict(self):
        resp = super(Questions, self).to_dict()
        resp.update(
            user_id = self.user_id,
            language_code = self.language_code,
            question_text = self.question_text,
            description = self.description,
            question_type = self.question_type,
        )
        return resp

'''
class QuestionAssignments(Base):

    """
    This table holds the connection between assignments and questions.  There can be
    multiple questions per assignment due to naturalization (multiple languages, same
    question).
    """

    __tablename__ = 'questionassignments'
    question_assignment_id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey('assignments.assignment_id'))
    question_id = Column(Integer, ForeignKey('questions.question_id'))

    @classmethod
    def create(cls, session, assignment_id, question_id):
        with transaction.manager:
            question_assignment = QuestionAssignments(
                assignment_id = assignment_id,
                question_id = question_id,
            )
            session.add(question_assignment)
            transaction.commit()
        return question_assignment
'''


class Languages(Base, CreationMixin, TimeStampMixin):

    """
    List of available languages.  The client is responciple for picking whicg language
    it wants.
    """

    __tablename__ = 'languages'
    #language_id = Column(Integer, primary_key=True)
    language_code = Column(UnicodeText)
    name = Column(UnicodeText)

    #questions = relationship('Questions', backref='language', lazy='joined')
    #posts = relationship('Posts', backref='language', lazy='joined')

    @classmethod
    def get_from_code(cls, session, language_code):
        with transaction.manager:
            language = DBSession.query(
                Languages
            ).filter(
                Languages.language_code == language_code
            ).first()
        return language

    '''
    @classmethod
    def get_all(cls, session):
        with transaction.manager:
            languages = DBSession.query(
                Languages.language_code,
                Languages.name,
            ).all()
        return languages
    '''

    '''
    @classmethod
    def add_language(cls, session, language_code, name):
        with transaction.manager:
            language = Languages(
                language_code = language_code,
                name = name,
            )
            session.add(language)
            transaction.commit()
        return language
    '''

    def to_dict(self):
        resp = super(Languages, self).to_dict()
        resp.update(
            language_code = self.language_code,
            name = self.name,
        )
        return resp


class Posts(Base, CreationMixin, TimeStampMixin):

    """
    These are the posts by users.  They can be unsolicited, or associated with a
    assignment.  The post has the users id, the optional assignment id, date/time
    language, and the lat/lng of the post.  There is a boolean option for flagging
    the post as 'innapropreate'.
    """

    __tablename__ = 'posts'
    #post_id = Column(Integer, primary_key=True)
    #user_id = Column(Integer, ForeignKey('users.user_id'))
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=True)
    #title = Column(UnicodeText)
    #post_datetime = Column(DateTime)
    #language_id = Column(Integer, ForeignKey('languages.language_id'))
    language_code = Column(UnicodeText, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    contents = Column(UnicodeText, nullable=False)

    deleted = Column(Boolean, nullable=False)
    approved = Column(Boolean, nullable=False)
    flagged = Column(Boolean, nullable=False)

    media_objects = relationship('MediaObjects', backref='post')
    assignment = relationship('Assignments', backref='posts', lazy='joined')
    votes = relationship('Votes', backref='post', lazy='joined')

    """
    @classmethod
    def create_from_http(cls, session, client_id, assignment_id, #title,
            language_code, lat, lng, contents): #, media_objects=[]):
        # create post
        with transaction.manager:
            # todo: error check this
            #language = Languages.get_from_code(
            #    session = DBSession.
            #    language_code = language_code
            #)
            if assignment_id == None \
                   or assignment_id == '' \
                   or assignment_id <= 0:
                assignment_id = None
            post = cls(
                client_id = client_id,
                assignment_id = assignment_id,
                #title = title,
                post_datetime = datetime.datetime.now(),
                #language_id = language.language_id,
                language_code = language_code,
                deleted = False,
                lat = lat,
                lng = lng,
                approved = False,
                flagged = False,
                contents = contents,
            )
            session.add(post)
            transaction.commit()
        '''
        # assign media objects to the post
        with transaction.manager:
            for media_id in media_objects:
                media_object = MediaObjects.get_from_media_id(
                    session = DBSession.
                    media_id = media_id,
                )
                if media_object == None:
                    raise Exception("Invalid media_object_id within media_objects array")
                post_media_object = PostMediaObjects(
                    post_id = post.post_id,
                    media_object_id = media_object.media_object_id,
                )
                session.add(post_media_object)
            transaction.commit()
        '''
        return post
    """

    @classmethod
    def get_approved_posts(cls, lat, lng, start=0, count=50):
        with transaction.manager:
            posts = DBSession.query(
                Posts,
            ).outerjoin(
                Assignments,
            ).filter(
                ((Assignments.top_left_lat + 90 > lat + 90) &
                    (Assignments.top_left_lng + 180 < lng + 180) &
                    (Assignments.bottom_right_lat + 90 < lat + 90) &
                    (Assignments.bottom_right_lng + 180 > lng + 180)) |
                (((lat + 0.5) + 90 > Posts.lat + 90) &
                    ((lng + 0.5) + 180 > Posts.lng + 180) &
                    ((lat - 0.5) + 90 < Posts.lat + 90) &
                    ((lng - 0.5) + 180 < Posts.lng + 180))
            ).filter(
                Posts.deleted == False,
                Posts.flagged == False,
                Posts.approved == True,
            ).slice(start, count).all()
        return posts

    @classmethod
    def get_posts(cls, top_left_lat, top_left_lng, bottom_right_lat, bottom_right_lng, deleted=False, flagged=False, approved=True, start=0, count=50):
        with transaction.manager:
            posts = DBSession.query(
                Posts,
            #).join(
            #    Assignments,
            ).filter(
                ((top_left_lat + 90 > Posts.lat + 90) &
                    (top_left_lng + 180 > Posts.lng + 180) &
                    (bottom_right_lat + 90 < Posts.lat + 90) &
                    (bottom_right_lng + 180 < Posts.lng + 180))
            ).filter(
                #Posts.deleted == deleted,
                #Posts.flagged == flagged,
                #Posts.approved == approved,
            ).slice(start, count).all()
        return posts


    '''
    @classmethod
    def _build_posts_query(cls, session, client_id=0):
        if True:
            posts_query = DBSession.query(
                Posts.post_id.label('posts_post_id'),
                #Posts.assignment_id,
                Posts.client_id,
                #Posts.title,
                Posts.post_datetime,
                Posts.deleted,
                Posts.lat,
                Posts.lng,
                Posts.approved,
                Posts.flagged,
                MediaObjects.media_object_id,
                MediaObjects.media_id,
                MediaObjects.file_name,
                MediaObjects.caption,
                MediaObjects.media_text,
                MediaTypes.name,
                MediaTypes.description,
                Clients.verified,
                Clients.first_name,
                Clients.last_name,
                Clients.cuid,
                Languages.language_code,
                Languages.name,
                Assignments.assignment_id,
                Assignments.name,
                Questions.question_text,
                session.query(
                    func.count(distinct(Votes.vote_id)).label('up_count'),
                ).filter(
                    Votes.post_id == Posts.post_id,
                    Votes.is_up_vote == True,
                ).label('up_vote_count'),
                session.query(
                    func.count(distinct(Votes.vote_id)).label('down_count'),
                ).filter(
                    Votes.post_id == Posts.post_id,
                    Votes.is_up_vote == False,
                ).label('down_vote_count'),
                session.query(
                    func.count(distinct(Votes.vote_id)),
                ).filter(
                    Votes.client_id == client_id,
                    Votes.post_id == Posts.post_id,
                ).label('has_voted'),
                session.query(
                    func.count(distinct(Votes.vote_id))
                ).filter(
                    Votes.client_id == client_id,
                    Votes.post_id == Posts.post_id,
                    Votes.is_up_vote == True,
                ).label('is_up_vote'),
            ).join(
                PostMediaObjects, #PostMediaObjects.media_object_id == MediaObjects.media_object_id,
            ).join(
                MediaObjects, #MediaObjects.media_object_id == PostMediaObjects.media_object_id,
            ).join(
                MediaTypes,
            ).join(
                Clients, Clients.client_id == Posts.client_id,
            ).join(
                Languages,
            ).outerjoin(
                Assignments, Assignments.assignment_id == \
                    Posts.assignment_id,
            ).outerjoin(
                QuestionAssignments, QuestionAssignments.assignment_id == \
                    Assignments.assignment_id,
            ).outerjoin(
                Questions, Questions.question_id == \
                    QuestionAssignments.question_id,
            ).outerjoin(
                CollectionPosts, CollectionPosts.post_id == \
                    Posts.post_id,
            ).group_by(
                Posts.post_id,
            ).order_by(
                desc(Posts.post_id),
            )
        return posts_query
    '''

    '''
    @classmethod
    def get_from_post_id(cls, session, post_id):
        with transaction.manager:
            post = DBSession.query(
                Posts,
            ).filter(
                Posts.post_id == post_id,
            ).first()
        return post
    '''

    '''
    @classmethod
    def get_count_from_client_id(cls, session, client_id):
        with transaction.manager:
            post_count = DBSession.query(
                Posts.client_id,
            ).filter(
                Posts.client_id == client_id,
            ).count()
        return post_count
    '''
  
    '''
    @classmethod
    def get_with_media_objects_from_post_id(cls, session, post_id):
        with transaction.manager:
            posts = Posts._build_posts_query(session).filter(
                Posts.post_id == post_id,
            ).all()
        return posts
    '''

    '''
    @classmethod
    def get_posts(cls, session, deleted=False, start=0, count=0):
        with transaction.manager:
            posts = Posts._build_posts_query(session).filter(
                Posts.deleted == deleted,
            ).slice(start, start+count).all()
        return posts
    '''

    @classmethod
    def get_all_from_assignment_id(cls, session, assignment_id,
            deleted=False, start=0, count=0):
        with transaction.manager:
            posts = Posts._build_posts_query(session).filter(
                Posts.assignment_id == assignment_id,
                Posts.deleted == deleted,
            ).slice(start, start+count).all()
        return posts #, total_post_count


    @classmethod
    def get_all_from_collection_id(cls, collection_id, deleted=False, 
            start=0, count=0):
        with transaction.manager:
            posts = Posts._build_posts_query(session).filter(
                CollectionPosts.collection_id == collection_id,
            ).slice(start, start+count).all()
        return posts


    @classmethod
    def get_all_from_cuid(cls, cuid, deleted=False, start=0, count=0):
        with transaction.manager:
            posts = Posts._build_posts_query(session).filter(
                Clients.cuid == cuid,
            ).slice(start, start+count).all()
        return posts #, total_post_count


    @classmethod
    def delete_post(cls, post_id):
        with transaction.manager:
            post = DBSession.query(
                Posts,
            ).filter(
                Posts.post_id == post_id,
            ).first()
            post.deleted = True
            DBSession.add(post)
            transaction.commit()
        return post


    @classmethod
    def approve_post(cls, post_id):
        with transaction.manager:
            post = DBSession.query(
                Posts,
            ).filter(
                Posts.post_id == post_id,
            ).first()
            # change the approved state of the post (T -> F, F -> T)
            if post.approved == False:
                post.approved = True
            else:
                post.approved = False
            DBSession.add(post)
            transaction.commit()
        return post


    @classmethod
    def flag_post(cls, post_id):
        with transaction.manager:
            post = DBSession.query(
                Posts,
            ).filter(
                Posts.post_id == post_id,
            ).first()
            if post.flagged == False:
                post.flagged = True
            else:
                post.flagged = False
            DBSession.add(post)
            transaction.commit()
        return post


    '''
    @classmethod
    def get_all_approved_from_location(cls, session, client_id, language_code, \
            lat, lng, start=0, count=0):
        with transaction.manager:
            posts = Posts._build_posts_query(session, client_id).filter(
                Posts.approved == True,
            ).filter(
                ((Assignments.top_left_lat + 90 > lat + 90) &
                    (Assignments.top_left_lng + 180 < lng + 180) &
                    (Assignments.bottom_right_lat + 90 < lat + 90) &
                    (Assignments.bottom_right_lng + 180 > lng + 180)) |
                (((lat + 0.5) + 90 > Posts.lat + 90) &
                    ((lng + 0.5) + 180 > Posts.lng + 180) &
                    ((lat - 0.5) + 90 < Posts.lat + 90) &
                    ((lng - 0.5) + 180 < Posts.lng + 180))
            ).filter(
                Posts.flagged == False,
                Languages.language_code == language_code,
                #cast(Assignments.expire_datetime,Date) >= cast(datetime.datetime.now(),Date),
            ).slice(start, start+count).all()
        return posts
    '''

    def to_dict(self, client_id):
        resp = super(Posts, self).to_dict()
        resp.update(
            assignment=self.assignment.to_dict() if self.assignment_id != None and self.assignment_id != 0 else None,
            language_code=self.language_code,
            lat=self.lat,
            lng=self.lng,
            contents = self.contents, 
            deleted=self.deleted,
            approved=self.approved,
            flagged=self.approved,
            media_objects = [m.to_dict() for m in self.media_objects],
            #votes = [v.to_dict() for v in self.votes],
            up_count = sum(1 for v in self.votes if v.is_up_vote),
            down_count = sum(1 for v in self.votes if not v.is_up_vote),
        )
        if client_id:
            resp.update(
                has_voted = any(v.client_id == client_id for v in self.votes),
                is_up_vote = any(v.client_id == client_id and v.is_up_vote for v in self.votes),
            )
        return resp

# Posts indexes ... these will be important to implement soon

#Index('index_posts_post_id', Posts.post_id, unique=True)
#Index('index_posts_post_datetime', Posts.creation_datetime)
#Index('index_posts_client_id', Posts.client_id)

class Votes(Base, CreationMixin, TimeStampMixin):

    __tablename__ = 'votes'
    #vote_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    is_up_vote = Column(Boolean)
    vote_datetime = Column(DateTime)

    @classmethod
    def register_vote(cls, session, post_id, client_id, is_up_vote):
        with transaction.manager:
            _vote = DBSession.query(
                Votes,
            ).filter(
                Votes.post_id == post_id,
                Votes.client_id == client_id,
            ).first()
            vote = None
            # if the client has not voted, register vote.
            if _vote == None:
                vote = Votes(
                    post_id = post_id,
                    client_id = client_id,
                    is_up_vote = is_up_vote,
                    vote_datetime = datetime.datetime.now(),
                )
                DBSession.add(vote)
                transaction.commit()
            # if the client has voted, but wants to remove it
            # (sending the vote a second time), then delete it
            elif _vote.is_up_vote == is_up_vote:
                session.delete(_vote)
                transaction.commit()
                vote = _vote
            # the client has already voted, but wants to change
            # their vote.
            elif _vote.is_up_vote != is_up_vote:
                _vote.is_up_vote = is_up_vote
                DBSession.add(_vote)
                transaction.commit()
                vote = _vote
        return vote

    def to_dict(self):
        resp = super(Votes, self).to_dict()
        resp.update(
            post_id = self.post_id, 
            client_id = self.client_id,
            is_up_vote = self.is_up_vote,
            vote_datetime = str(self.vote_datetime),
        )
        return resp

'''
class MediaTypes(Base):

    """
    These are the differnet types of media.  Audio, Video, Image, and Text.
    """

    __tablename__ = 'mediatypes'
    media_type_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    media_objects = relationship('MediaObjects', backref='media_type', lazy='joined')

    @classmethod
    def from_value(cls, session, name):
        with transaction.manager:
            media_type = DBSession.query(
                MediaTypes,
            ).filter(
                MediaTypes.name == name,
            ).first()
        return media_type

    @classmethod
    def add_media_type(cls, session, name, description):
        with transaction.manager:
            media_type = MediaTypes(
                name = name,
                description = description,
            )
            session.add(media_type)
            transaction.commit()
        return media_type

    def to_dict(self):
        resp = dict(
            media_type_id = self.media_type_id,
            name = self.name,
            description = self.description,
        )
        return resp
'''


class MediaObjects(Base, CreationMixin, TimeStampMixin):

    """
    Media objects are attached to a post.  A post can have any number of media objects.
    valid media_types are: video, audio, image
    """

    __tablename__ = 'mediaobjects'
    #media_object_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    #user_id = Column(Integer, ForeignKey('users.id'))
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    #media_type_id = Column(Integer, ForeignKey('mediatypes.id'))
    media_type = Column(UnicodeText, nullable=False)
    #media_id = Column(UnicodeText)
    filename = Column(UnicodeText, nullable=False)
    preview_filename = Column(UnicodeText, nullable=False)
    #caption = Column(UnicodeText)
    #media_text = Column(UnicodeText)

    #post = relationship('Posts', backref='media_objects', lazy='joined')

    '''
    @classmethod
    def get_from_media_id(cls, session, media_id):
        with transaction.manager:
            media_object = DBSession.query(
                MediaObjects,
            ).filter(
                MediaObjects.media_id == media_id,
            ).first()
        return media_object
    '''

    @classmethod
    def get_from_post_id(cls, session, post_id):
        with transaction.manager:
            media_objects = DBSession.query(
                MediaObjects,
                #MediaObjects.file_name,
                #MediaObjects.caption,
                #MediaObjects.media_text,
                #MediaTypes.name,
                #MediaTypes.description,
            ).join(
                #PostMediaObjects,
                #MediaTypes,
            ).filter(
                MediaObjects.post_id == post_id,
                #PostMediaObjects.media_object_id == MediaObjects.media_object_id,
                #PostMediaObjects.post_id == post_id,
                #MediaTypes.media_type_id == MediaObjects.media_type_id,
            ).all()
        return media_objects

    '''
    @classmethod
    def create_new_media_object(cls, session, client_id, media_type_text,
            file_name, post_id): #caption, media_text):
        with transaction.manager:
            mediatype = MediaTypes.from_value(session,media_type_text)
            mediaobject = cls(
                client_id = client_id,
                media_type_id = mediatype.media_type_id,
                media_id = str(uuid4()),
                file_name = file_name,
                #caption = caption,
                #media_text = media_text,
                post_id = post_id, 
            )
            session.add(mediaobject)
            transaction.commit()
        return mediaobject
    '''

    def to_dict(self):
        resp = super(MediaObjects, self).to_dict()
        resp.update(
            #media_object_id = self.media_object_id,
            post_id = self.post_id,
            client_id = self.client_id,
            #media_type = self.media_type.to_dict(),
            media_type = self.media_type,
            filename = self.filename,
            #caption = self.caption,
            #media_text = self.media_text,
        )
        return resp

'''
class PostMediaObjects(Base):

    """
    There can be multiple media objects associated with a post, thus this table allows
    for the linking of multiple media objects to a single post id.
    """

    __tablename__ = 'postmediaobjects'
    post_media_object_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'))
    media_object_id = Column(Integer, ForeignKey('mediaobjects.media_object_id'))

    @classmethod
    def create_new_postmediaobject(cls, session, post_id, media_object_id):
        with transaction.manager:
            post_media_object = cls(
                post_id = post_id,
                media_object_id = media_objectid,
            )
'''

'''
class Stories(Base, CreationMixin, TimeStampMixin):

    """
    This is used to hold the 'store front' stories for the site.  These
    stories are writen in markdown and html, and reference media objects.
    """

    __tablename__ = 'stories'
    story_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    story_unique_id = Column(UnicodeText)
    publish_datetime = Column(DateTime)
    edited_datetime = Column(DateTime, nullable=True)
    title = Column(UnicodeText)
    tags = Column(UnicodeText)
    #top_text = Column(UnicodeText)
    #media_object_id = Column(Integer, \
    #    ForeignKey('mediaobjects.media_object_id'), nullable=True)
    contents = Column(UnicodeText)
    top_left_lat = Column(Float)
    top_left_lng = Column(Float)
    bottom_right_lat = Column(Float)
    bottom_right_lng = Column(Float)
    #use_fense = Column(Boolean)
    language_id = Column(Integer, ForeignKey('languages.language_id'))

    @classmethod
    def add_story(cls, session, user_id, title, tags, contents, top_left_lat,\
            top_left_lng, bottom_right_lat, bottom_right_lng, language_code):
        with transaction.manager:
            #user = Users.get_from_token(session, token)
            #media_object = MediaObjects.get_from_media_id(
            #    session,
            #    media_id,
            #)
            #if media_object == None:
            #    media_object_id = None
            #else:
            #    media_object_id = media_object.media_object_id
            language = Languages.get_from_code(session, language_code)
            story = cls(
                user_id = user_id,
                story_unique_id = str(uuid4()),
                publish_datetime = datetime.datetime.now(),
                edited_datetime = None,
                title = title,
                tags = tags,
                #top_text = top_text,
                #media_object_id = media_object_id,
                contents = contents,
                top_left_lat = top_left_lat,
                top_left_lng = top_left_lng,
                bottom_right_lat = bottom_right_lat,
                bottom_right_lng = bottom_right_lng,
                #use_fence = use_fence,
                language_id = language.language_id,
            )
            session.add(story)
            transaction.commit()
        return story

    @classmethod
    def get_stories(cls, session, lat, lng, language_code, start=0, count=0):
        with transaction.manager:
            stories_query = DBSession.query(
                Stories.story_unique_id,
                Stories.publish_datetime,
                Stories.edited_datetime,
                Stories.title,
                Stories.tags,
                #Stories.top_text,
                Stories.contents,
                Stories.top_left_lat,
                Stories.top_left_lng,
                Stories.bottom_right_lat,
                Stories.bottom_right_lng,
                Users.first_name,
                Users.last_name,
                #Users.organization,
                Organizations.organization_id,
                Organizations.name,
                Users.email,
                #MediaObjects.file_name,
                #MediaObjects.media_id,
            ).join(
                Users,Stories.user_id == Users.user_id,
            ).join(
                Organizations, #Organizations.organization_id == \
                    #Users.organization_id,
            #).outerjoin(
            #    MediaObjects,Stories.media_object_id == \
            #        MediaObjects.media_object_id,
            )
            stories_filter_query = stories_query
            if language_code != '':
                language = Languages.get_from_code(session, language_code)
                stories_filter_query = stories_filter_query.filter(
                    Stories.language_id == language.language_id,
                )
            stories_filter_query = stories_filter_query.filter(
                Stories.top_left_lat + 90 > lat + 90,
                Stories.top_left_lng + 180 < lng + 180,
                Stories.bottom_right_lat + 90 < lat + 90,
                Stories.bottom_right_lng + 180 > lng + 180,
                # Stories.user_fense == True,
            ).order_by(
                 desc(Stories.publish_datetime),
            )
            total_story_count = stories_filter_query.count()
            #if start == 0 and count == 0:
            #    stories = stories_filter_query.all()
            #else:
            stories = stories_filter_query.slice(start, start+count)
        return stories, total_story_count

    def to_dict(self):
        resp = dict(
            story_id = self.story_id,
            user = self.user.to_dict(),
            story_unique_id = self.story_unique_id,
            publish_datetime = str(self.publish_datetime),
            edited_datetime = str(self.publish_datetime),
            title = self.title,
            tags = self.tags,
            contents = self.contents,
            top_left_lat = self.top_left_lat,
            top_left_lng = self.top_left_lng,
            bottom_right_lat = self.bottom_right_lat,
            bottom_right_lng = self.bottom_right_lng,
            language = self.language.to_dict(),
         )
        return resp
'''

'''
class ClientLogs(Base):

    """
    This is used as a debugging tool to keep track of how the application is
    being used, and how often clients are accessing the website.
    """

    __tablename__ = 'clientlogs'
    client_log_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), \
        nullable=True)
    url = Column(UnicodeText)
    lat = Column(Float)
    lng = Column(Float)
    request = Column(UnicodeText)
    result = Column(UnicodeText)
    success = Column(Boolean)
    log_datetime = Column(DateTime)

    @classmethod
    def log(cls, session, client_id, url, lat, lng, request, result,
            success):
        print "URL: %s" % url
        with transaction.manager:
            client_log = ClientLogs(
                client_id = client_id,
                url = url,
                lat = lat,
                lng = lng,
                request = request,
                result = result,
                success = success,
                log_datetime = datetime.datetime.now(),
            )
            session.add(client_log)
            transaction.commit()
        return client_log

    @classmethod
    def get_all(cls, session):
        with transaction.manager:
            client_logs = DBSession.query(
                ClientLogs,
            ).order_by(
                ClientLogs.log_datetime,
            ).all()
        return client_logs

    @classmethod
    def get_all_by_client_id(cls, session):
        with transaction.manager:
             client_logs = DBSession.query(
                ClientLogs,
            ).filter(
                ClientLogs.client_id == client_id,
            ).order_by(
                ClientLogs.log_datetime,
            ).all()
        return client_logs
'''

class CollectionPosts(Base, CreationMixin, TimeStampMixin):

    """
    Table to link posts to a collection.
    """

    __tablename__ = 'collection_posts'
    #collection_post_id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('collections.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)

    '''
    @classmethod
    def create_new_collectionpost(cls, session, collection_id, post_id):
        with transaction.manager:
            collection_post = cls(
                collection_id = collection_id,
                post_id = post_id,
            )
        return collection_post
    '''

    def to_dict(self):
        resp = super(CollectionPosts, self).to_dict()
        resp.update(
            collection_id = self.collection_id,
            post_id = self.post_id,
        )
        return resp

class Collections(Base, CreationMixin, TimeStampMixin):

    """
    Collections are a means to organize posts, and are used by moderators and
    subscribers.
    """

    __tablename__ = 'collections'
    #collection_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    #collection_datetime = Column(DateTime)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    tags = Column(UnicodeText)
    enabled = Column(Boolean)
    #private = Column(Boolean)

    assignment = relationship(
        "Assignments",
        backref='collection',
        lazy='joined'
    )

    posts = relationship(
        "Posts",
        secondary=CollectionPosts.__table__,
        backref='collections',
        lazy='joined'
    )

    '''
    @classmethod
    def _build_collections_query(cls, session):
        if True:
            collections_query = DBSession.query(
                Collections.collection_id,
                Collections.user_id,
                Collections.collection_datetime,
                Collections.name,
                Collections.description,
                Collections.tags,
                Collections.enabled,
                Assignments.assignment_id,
                Assignments.name,
                func.count(Posts.post_id),
            ).outerjoin(
                CollectionPosts, CollectionPosts.collection_id == \
                    Collections.collection_id,
            ).outerjoin(
                Posts, Posts.post_id == \
                    CollectionPosts.post_id,
            ).outerjoin(
                Assignments, Assignments.collection_id == \
                    Collections.collection_id,
            ).group_by(
                Collections.collection_id,
                #Assignments.assignment_id,
            ).order_by(
                desc(Collections.collection_id),
            )
        return collections_query
    '''

    @classmethod
    def get_all_from_user_id(cls, user_id):
        with transaction.manager:
            collections = Collections._build_collections_query(session).filter(
                Collections.user_id == user_id,
            ).all()
        return collections

    '''
    @classmethod
    def get_from_collection_id(cls, session, collection_id):
        with transaction.manager:
            collection = DBSession.query(
                Collections,
            ).filter(
                Collections.collection_id == collection_id,
            ).first()
        return collection
    '''

    '''
    @classmethod
    def add_collection(cls, session, user_id, name,
            description='', tags=''):
        with transaction.manager:
            #user = Users.get_from_token(session, token)
            collection = cls(
                user_id = user_id, #user.user_id,
                collection_datetime = datetime.datetime.now(),
                name = name,
                description = description,
                tags = tags,
                enabled = True,
            )
            session.add(collection)
            transaction.commit()
        return collection
    '''

    
    @classmethod
    def disable_collection(cls, collection_id):
        with transaction.manager:
            collection = DBSession.query(
                Collections,
            ).filter(
                Collections.collection_id == collection_id,
            ).first()
            collection.enabled = False
            DBSession.add(collection)
            transaction.commit()
        return collection


    @classmethod
    def add_post_to_collection(cls, session, collection_id, post_id):
        with transaction.manager:
            collection_post = CollectionPosts(
                collection_id = collection_id,
                post_id = post_id,
            )
            DBSession.add(collection_post)
            transaction.commit()
        return collection_post


    @classmethod
    def remove_post_from_collection(cls, session, collection_id, post_id):
        with transaction.manager:
            collection_post = DBSession.query(
                CollectionPosts,
            ).filter(
                CollectionPosts.collection_id == collection_id,
                CollectionPosts.post_id == post_id,
            ).first()
            success = False
            if collection_post != None:
                session.delete(collection_post)
                transaction.commit()
                success = True
        return success


    def to_dict(self):
        resp = super(Collections, self).to_dict()
        resp.update(
            #user_id = self.user_id,
            collection_datetime = str(collection_datetime),
            name = self.name,
            description = self.description,
            tags = self.tags,
            enabled = self.enabled,
            #posts = [p.to_dict() for p in self.posts], 
            post_count = len(self.posts),
        )
        return resp


'''
class Notifications(Base):

    """ This table holds notifications for a client.
    """

    __tablename__ = 'notifications'
    notification_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'))
    notification_datetime = Column(DateTime)
    notification_type = Column(UnicodeText)
    payload = Column(UnicodeText)

    @classmethod
    def get_notifications_from_client_id(cls, session, client_id):
        with transaction.manager:
            notifications = DBSession.query(
                Notifications.notification_id,
                Notifications.notification_datetime,
                Notifications.notification_type,
                Notifications.payload,
            ).filter(
                Notifications.client_id == client_id,
            ).order_by(
                desc(Notifications.notification_datetime),
            ).limit(25)
        return notifications #, created

    @classmethod
    def create_notification(cls, session, client_id, notification_type, payload):
        with transaction.manager:
            notification = cls(
                client_id = client_id,
                notification_datetime = datetime.datetime.now(),
                notification_type = notification_type,
                payload = payload,
            )
            session.add(notification)
            transaction.commit()
        return notification
'''


'''
class Messages(Base):

    """
    Messages holds the messages to users from moderators and/or subscribers, as
    well as the users response messages.
    """

    __tablename__ = 'messages'
    message_id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey('users.user_id'))
    to_user_id = Column(Integer, ForeignKey('users.user_id'))
    message_datetime = Column(DateTime)
    parent_message_id = Column(Integer, \
        ForeignKey('messages.message_id'), nullable=True)
    subject = Column(UnicodeText)
    text = Column(UnicodeText)
    was_read = Column(UnicodeText)

    @classmethod
    def get_user_id_from_message_id(cls, session, message_id):
        with transaction.manager:
            message = DBSession.query(
                Messages,
            ).filter(
                Messages.message_id == message_id,
            ).first()
        return message.from_user_id

    @classmethod
    def get_from_message_id(cls, session, message_id):
        with transaction.manager:
            message = DBSession.query(
                Messages,
            ).filter(
                Messages.message_id == message_id,
            ).first()
        return message

    @classmethod
    def create_message(cls, session, from_user_id, to_user_id, subject, text,
            parent_message_id=None):
        message = None
        #with transaction.manager:
        #    message = cls(
        #        from_user_id = from_user_id,
        #        to_user_id = to_user_id,
        #        message_datetime = datetime.datetime.now(),
        #        parent_message_id = parent_message_id,
        #        subject = subject,
        #        text = text,
        #        was_read = False,
        #    )
        #    session.add(message)
        #    transaction.commit()
        #Notifications.create_notification(
        #    session,
        #    to_user_id,
        #    'new_message',
        #    json.dumps({'organization': \
        #        Users.get_organization_from_user_id(session, from_user_id)}),
        #)
        return message

    @classmethod
    def create_message_from_http(cls, session, from_token, to_client_id, subject,
            text, parent_message_id=None):
        message = None
        #from_user = Users.get_from_token(session, from_token)
        #to_user,created = Users.get_from_client_id(session, to_client_id)
        #message = None
        #if created == False:
        #    message = Messages.create_message(
        #        session = DBSession.
        #        from_user_id = from_user.user_id,
        #        to_user_id = to_user.user_id,
        #        subject = subject,
        #        text = text,
        #        parent_message_id = parent_message_id,
        #    )
        #    session.add(message)
        #    transaction.commit()
        return message

    @classmethod
    def create_response_message_from_http(cls, session, client_id,
            parent_message_id, subject, text):
        message = None
        #exists = Messages.check_if_message_has_child(session, parent_message_id)
        #parent_message = Messages.get_from_message_id(
        #    session,
        #    parent_message_id
        #)
        #message = None
        #if parent_message != None and exists == False:
        #    from_user, created = Users.get_from_client_id(session, client_id)
        #    to_user_id = Messages.get_user_id_from_message_id(
        #        session,
        #        parent_message_id
        #    )
        #    with transaction.manager:
        #        message = cls(
        #            from_user_id = from_user.user_id,
        #            to_user_id = to_user_id,
        #            message_datetime = datetime.datetime.now(),
        #            parent_message_id = parent_message_id,
        #            subject = subject,
        #            text = text,
        #            was_read = False,
        #        )
        #        session.add(message)
        #        transaction.commit()
        #    Notifications.create_notification(
        #        session,
        #        to_user_id,
        #        'new_message',
        #        json.dumps({'parent_message_id': parent_message_id}),
        #    )
        return message

    @classmethod
    def check_if_message_has_child(cls, session, parent_message_id):
        with transaction.manager:
            message = DBSession.query(
                Messages,
            ).filter(
                Messages.parent_message_id == parent_message_id,
            ).first()
            exists = False
            if message != None:
                exists = True
        return exists

    @classmethod
    def mark_as_read(cls, session, client_id, message_id):
        message = None
        #with transaction.manager:
        #    user = Users.get_from_client_id(session, client_id)
        #    message = DBSession.query(
        #        Messages,
        #    ).filter(
        #        Messages.message_id == message_id,
        #        # only the recipiant can mark as read.
        #        Messages.to_user_id == user.user_id,
        #    ).first()
        #    message.was_read = True
        #    session.add(message)
        #    transaction.commit()
        return message

    # TODO: make this not have to itterate through all the messages ...
    @classmethod
    def mark_all_as_read(cls, session, user_id):
        with transaction.manager:
            message = 0
            while message != None:
                message = DBSession.query(
                    Messages,
                ).filter(
                    Messages.to_user_id == user_id,
                    Messages.was_read == False,
                ).first()
                if message != None:
                    break
                message.was_read = True
                session.add(message)
                transaction.commit()
        return True

    @classmethod
    def get_messages_from_client_id(cls, session, client_id):
        messages = []
        #with transaction.manager:
        #    user,created = Users.get_from_client_id(
        #        session,
        #        client_id,
        #        create_if_not_exist=False,
        #    )
        #    messages = []
        #    if user != None:
        #        messages = DBSession.query(
        #            Messages.message_id,
        #            Messages.from_user_id,
        #            Messages.to_user_id,
        #            Messages.message_datetime,
        #            Messages.parent_message_id,
        #            Messages.subject,
        #            Messages.text,
        #            Messages.was_read,
        #            Users.organization,
        #            Users.first_name,
        #            Users.last_name,
        #        ).join(
        #            Users,Users.user_id == Messages.from_user_id,
        #        ).filter(
        #            Messages.to_user_id == user.user_id,
        #            Messages.was_read == False,
        #        ).all()
        #for m in messages:
        #    Messages.mark_all_as_read(session,m[2])
        return messages
'''

'''
class DebugSubmissions(Base):

    """ This class is for debug purposes, and will hold debug information
        sent from the client.
    """

    __tablename__ = 'debug_submissions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    debug_text = Column(UnicodeText)
    sumbission_datetime = Column(DateTime)

    @classmethod
    def create_new_submission(cls, session, client_id, debug_text):
        with transaction.manager:
            user = Users.get_from_client_id(session, client_id)
            submission = cls(
                id = user.id,
                debug_text = debug_text,
                submission_datetime = datetime.datetime.now(),
            )
        return submission

    @classmethod
    def get_all_submissions(cls, session):
        with transaction.manager:
            submissions = DBSession.query(
                DebugSubmissions,
            ).all()
        return submissions
'''

'''
class Subscribers(Base):

    """ This holds information about the news letter subscribers
    """

    __tablename__ = 'subscribers'
    subscriber_id = Column(Integer, primary_key=True)
    email = Column(UnicodeText)
    subscribe_datetime = Column(DateTime)
    name = Column(UnicodeText, nullable = True)
    organization = Column(UnicodeText, nullable = True)
    profession = Column(UnicodeText, nullable = True)
    receive_updates = Column(Boolean)
    receive_version_announcement = Column(Boolean)
    interested_in_partnering = Column(Boolean)
    want_to_know_more = Column(Boolean)

    @classmethod
    def add_subscriber(cls, session, email, name=None, organization=None, \
            profession=None, receive_updates=False, \
            receive_version_announcement=False,
            interested_in_partnering=False, want_to_know_more=False):
        with transaction.manager:
            subscriber = cls(
                email = email,
                subscribe_datetime = datetime.datetime.now(),
                name = name,
                organization = organization,
                profession = profession,
                receive_updates = receive_updates,
                receive_version_announcement = receive_version_announcement,
                interested_in_partnering = interested_in_partnering,
                want_to_know_more = want_to_know_more,
            )
            session.add(subscriber)
            transaction.commit()
        return subscriber

    @classmethod
    def get_all_subscribers(cls, session):
        with transaction.manager:
            subscribers = DBSession.query(
                Subscribers,
            ).filter(
            ).all()
        return subscribers

'''

class Organizations(Base, CreationMixin, TimeStampMixin):

    __tablename__ = 'organizations'
    #organization_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText, nullable=False)
    contact_name = Column(UnicodeText, nullable=False)
    contact_email = Column(UnicodeText, nullable=False)
    #creation_datetime = Column(DateTime)

    users = relationship('Users', backref='organization', lazy='joined')

    '''
    @classmethod
    def add_organization(cls, session, name, description, contact_name,\
             contact_email):
        with transaction.manager:
            organization = Organizations(
                name = name,
                description = description,
                contact_name = contact_name,
                contact_email = contact_email,
                creation_datetime = datetime.datetime.now(),
            )
            session.add(organization)
            transaction.commit()
        return organization
    '''

    '''
    @classmethod
    def get_from_id(cls, session, organization_id):
        with transaction.manager:
            organization = DBSession.query(
                Organizations,
            ).filter(
                Organizations.organization_id == organization_id,
            ).first()
        return organization
    '''

    '''
    @classmethod
    def get_all(cls, session):
        with transaction.manager:
            organizations = DBSession.query(
                Organizations.organization_id,
                Organizations.name,
                Organizations.description,
                Organizations.contact_name,
                Organizations.contact_email,
                Organizations.creation_datetime,
            ).all()
        return organizations
    '''

    def to_dict(self):
        resp = super(Organizations, self).to_dict()
        resp.update(
            name = self.name,
            description = self.description,
            contact_name = self.contact_name,
            contact_email = self.contact_email,
            creation_datetime = str(self.creation_datetime),
        )
        return resp

'''
class Zipcodes(Base):

    __tablename__ = 'zipcodes'
    zipcode_id = Column(Integer, primary_key=True)
    zipcode = Column(UnicodeText)
    city = Column(UnicodeText)
    state_code = Column(UnicodeText)
    lat = Column(Float)
    lng = Column(Float)
    timezone = Column(Integer)
    #geom = Column(Geometry('POLYGON'), nullable=False)
    #geom = Column(Geometry('POLYGON'), nullable=False)

    @classmethod
    def add_zipcode(cls, session, _zipcode, city, state_code, lat, lng,
            timezone, polygon_string):
        with transaction.manager:
            zipcode = Zipcodes(
                zipcode = _zipcode,
                city = city,
                state_code = state_code,
                lat = lat,
                lng = lng,
                timezone = timezone,
                geom = polygon_string
            )
            session.add(zipcode)
            transaction.commit()
        return zipcode

    @classmethod
    def get_from_zipcode(cls, session, _zipcode):
        with transaction.manager:
            zipcode = DBSession.query(
                Zipcodes,
            ).filter(
                Zipcodes.zipcode == _zipcode,
            ).first()
        return zipcode

    @classmethod
    def get_count(cls, session):
        with transaction.manager:
            zipcodes_count = DBSession.query(
                Zipcodes,
            ).count()
        return zipcodes_count
'''
