from __future__ import unicode_literals

from django.conf.urls import patterns, url

from .api_views import DocumentVersionOCRView

urlpatterns = patterns(
    'ocr.views',
    url(r'^(?P<document_id>\d+)/content/$', 'document_content', name='document_content'),
    url(r'^document/(?P<pk>\d+)/submit/$', 'document_submit', name='document_submit'),
    url(r'^document/multiple/submit/$', 'document_submit_multiple', name='document_submit_multiple'),

    url(r'^all/$', 'entry_list', name='entry_list'),
    url(r'^(?P<pk>\d+)/delete/$', 'entry_delete', name='entry_delete'),
    url(r'^multiple/delete/$', 'entry_delete_multiple', name='entry_delete_multiple'),
    url(r'^(?P<pk>\d+)/re-queue/$', 'entry_re_queue', name='entry_re_queue'),
    url(r'^multiple/re-queue/$', 'entry_re_queue_multiple', name='entry_re_queue_multiple'),
)

api_urls = patterns(
    '',
    url(r'^submit/$', DocumentVersionOCRView.as_view(), name='document-version-ocr-submit-view'),
)
