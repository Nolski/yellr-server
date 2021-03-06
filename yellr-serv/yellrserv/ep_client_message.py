from pyramid.view import view_config

import client_utils
import utils

@view_config(route_name='get_messages.json')
def get_messages(request):

    result = {'success': False}
    status_code = 200

    try:

        success, error_text, language_code, lat, lng, \
            client = client_utils.register_client(request)
        if success == False:
            raise Exception(error_text)

        messages = client_utils.get_messages(
            client_id = client.client_id,
            language_code = language_code,
            lat = lat,
            lng = lng,
        )

        result['messages'] = messages
        result['success'] = True

    except Exception, e:
        status_code = 400
        result['error_text'] = str(e)

    client_utils.log_client_action(
        client = client,
        url = 'get_messages.json',
        lat = lat,
        lng = lng,
        request = request,
        result = result,
        success = success,
    )

    return utils.make_response(result, status_code)

@view_config(route_name='create_response_message.json')
def create_response_message(request):

    result = {'success': False}

    try:

        success, error_text, language_code, lat, lng, \
            client = client_utils.register_client(request)
        if success == False:
            raise Exception(error_text)

        message = client_utils.create_response_message(
            client_id = client.client_id,
            parent_message_id = parent_message_id,
            subject = subject,
            text = text,
        )

        if message != None:
            result['message_id'] = message.message_id
            result['success'] = True
        else:
            Exception("Message already has posted response.")

    except Exception, e:
        status_code = 400
        response['error_text'] = str(e)

    client_utils.log_client_action(
        client = client,
        url = 'create_response_message.json',
        lat = lat,
        lng = lng,
        request = request,
        result = result,
        success = success,
    )

    return utils.make_response(result, status_code)

