# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework.decorators import api_view
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from . utils import user_exists, do_tweet_analysis

# Create your views here.
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def get_tweet_analysis(request):
    """ View to return tweet analysis """
    response = {}
    target_user = request.GET.get('target_user', None)

    if target_user == None:
        response = {'success': False, 'message': 'Provide name of twitter handle to process'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
    if not user_exists(target_user=target_user):
        response = {'success': False, 'message': 'The request twitter handle do not exist'}
        return Response(response, status=status.HTTP_200_OK)
    try:
        response = {'success': True, 'message': 'Succes !! Targer user analysed.', 'result': None}
        response['result'] = do_tweet_analysis(target_user)
        return Response(response, status=status.HTTP_200_OK)
    except:
        response = {'success': False, 'message': 'Oops !! Server Error.'}
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
