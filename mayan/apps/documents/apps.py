from __future__ import absolute_import, unicode_literals

import tempfile

from django import apps
from django.utils.translation import ugettext_lazy as _

from actstream import registry

from acls.api import class_permissions
from acls.permissions import ACLS_VIEW_ACL, ACLS_EDIT_ACL
from common import (
    MissingItem, menu_facet, menu_front_page, menu_object, menu_secondary,
    menu_setup, menu_sidebar, menu_multi_item
)
from common.api import register_maintenance_links
from common.classes import ModelAttribute
from common.signals import post_initial_setup
from common.utils import encapsulate, validate_path
from converter.links import link_transformation_list
from converter.permissions import (
    PERMISSION_TRANSFORMATION_CREATE,
    PERMISSION_TRANSFORMATION_DELETE, PERMISSION_TRANSFORMATION_EDIT,
    PERMISSION_TRANSFORMATION_VIEW,
)
from dynamic_search.classes import SearchModel
from events.permissions import PERMISSION_EVENTS_VIEW
from navigation.api import register_model_list_columns
from rest_api.classes import APIEndPoint
from statistics.classes import StatisticNamespace

from documents import settings as document_settings
from .handlers import create_default_document_type
from .links import (
    link_clear_image_cache, link_document_acl_list,
    link_document_clear_transformations, link_document_delete,
    link_document_document_type_edit, link_document_events_view,
    link_document_multiple_document_type_edit, link_document_download,
    link_document_edit, link_document_list, link_document_list_recent,
    link_document_multiple_delete,
    link_document_multiple_clear_transformations,
    link_document_multiple_download, link_document_multiple_update_page_count,
    link_document_page_navigation_first, link_document_page_navigation_last,
    link_document_page_navigation_next,
    link_document_page_navigation_previous, link_document_page_return,
    link_document_page_rotate_left, link_document_page_rotate_right,
    link_document_page_view, link_document_page_view_reset,
    link_document_page_zoom_in, link_document_page_zoom_out,
    link_document_pages, link_document_preview, link_document_print,
    link_document_properties, link_document_type_create,
    link_document_type_delete, link_document_type_edit,
    link_document_type_filename_create, link_document_type_filename_delete,
    link_document_type_filename_edit, link_document_type_filename_list,
    link_document_type_list, link_document_type_setup,
    link_document_update_page_count, link_document_version_download,
    link_document_version_list, link_document_version_revert
)
from .models import (
    Document, DocumentPage, DocumentType, DocumentTypeFilename,
    DocumentVersion
)
from .permissions import (
    PERMISSION_DOCUMENT_DELETE, PERMISSION_DOCUMENT_DOWNLOAD,
    PERMISSION_DOCUMENT_EDIT, PERMISSION_DOCUMENT_NEW_VERSION,
    PERMISSION_DOCUMENT_PRINT, PERMISSION_DOCUMENT_PROPERTIES_EDIT,
    PERMISSION_DOCUMENT_VERSION_REVERT, PERMISSION_DOCUMENT_VIEW
)
from .settings import THUMBNAIL_SIZE
from .statistics import DocumentStatistics, DocumentUsageStatistics
from .widgets import document_thumbnail


class DocumentsApp(apps.AppConfig):
    name = 'documents'
    verbose_name = _('Documents')

    def ready(self):
        if (not validate_path(document_settings.CACHE_PATH)) or (not document_settings.CACHE_PATH):
            setattr(document_settings, 'CACHE_PATH', tempfile.mkdtemp())

        APIEndPoint('documents')

        DocumentPage.add_to_class('get_transformation_list', lambda document_page: Transformation.objects.get_for_object(document_page))

        MissingItem(label=_('Create a document type'), description=_('Every uploaded document must be assigned a document type, it is the basic way Mayan EDMS categorizes documents.'), condition=lambda: not DocumentType.objects.exists(), view='documents:document_type_list')

        ModelAttribute(Document, label=_('Label'), name='label', type_name='field')

        class_permissions(Document, [
        ])

        class_permissions(Document, [
            ACLS_VIEW_ACL, ACLS_EDIT_ACL, PERMISSION_DOCUMENT_DELETE,
            PERMISSION_DOCUMENT_DOWNLOAD, PERMISSION_DOCUMENT_EDIT,
            PERMISSION_DOCUMENT_NEW_VERSION, PERMISSION_DOCUMENT_PRINT,
            PERMISSION_DOCUMENT_PROPERTIES_EDIT,
            PERMISSION_DOCUMENT_VERSION_REVERT, PERMISSION_DOCUMENT_VIEW,
            PERMISSION_EVENTS_VIEW, PERMISSION_TRANSFORMATION_CREATE,
            PERMISSION_TRANSFORMATION_DELETE, PERMISSION_TRANSFORMATION_EDIT,
            PERMISSION_TRANSFORMATION_VIEW,
        ])

        document_search = SearchModel('documents', 'Document', permission=PERMISSION_DOCUMENT_VIEW, serializer_string='documents.serializers.DocumentSerializer')

        # TODO: move these to their respective apps
        # Moving these to other apps cause an ImportError; circular import?
        document_search.add_model_field('document_type__name', label=_('Document type'))
        document_search.add_model_field('versions__mimetype', label=_('MIME type'))
        document_search.add_model_field('label', label=_('Label'))
        document_search.add_model_field('metadata__metadata_type__name', label=_('Metadata type'))
        document_search.add_model_field('metadata__value', label=_('Metadata value'))
        document_search.add_model_field('versions__pages__content', label=_('Content'))
        document_search.add_model_field('description', label=_('Description'))
        document_search.add_model_field('tags__label', label=_('Tags'))

        menu_front_page.bind_links(links=[link_document_list_recent, link_document_list])
        menu_setup.bind_links(links=[link_document_type_setup])

        # Document type links
        menu_object.bind_links(links=[link_document_type_edit, link_document_type_filename_list, link_document_type_delete], sources=[DocumentType])
        menu_object.bind_links(links=[link_document_type_filename_edit, link_document_type_filename_delete], sources=[DocumentTypeFilename])
        menu_secondary.bind_links(links=[link_document_type_list, link_document_type_create], sources=[DocumentType, 'documents:document_type_create', 'documents:document_type_list'])
        menu_sidebar.bind_links(links=[link_document_type_filename_create], sources=[DocumentTypeFilename, 'documents:document_type_filename_list', 'documents:document_type_filename_create'])

        # Document object links
        menu_object.bind_links(links=[link_document_edit, link_document_document_type_edit, link_document_print, link_document_delete, link_document_download, link_document_clear_transformations, link_document_update_page_count], sources=[Document])

        # Document facet links
        menu_facet.bind_links(links=[link_document_acl_list], sources=[Document])
        menu_facet.bind_links(links=[link_document_preview], sources=[Document], position=0)
        menu_facet.bind_links(links=[link_document_properties], sources=[Document], position=2)
        menu_facet.bind_links(links=[link_document_events_view, link_document_version_list], sources=[Document], position=2)
        menu_facet.bind_links(links=[link_document_pages], sources=[Document])

        # Document actions
        menu_object.bind_links(links=[link_document_version_revert, link_document_version_download], sources=[DocumentVersion])
        menu_multi_item.bind_links(links=[link_document_multiple_clear_transformations, link_document_multiple_delete, link_document_multiple_download, link_document_multiple_update_page_count, link_document_multiple_document_type_edit], sources=[Document])

        # Document pages
        menu_facet.bind_links(links=[link_document_page_rotate_left, link_document_page_rotate_right, link_document_page_zoom_in, link_document_page_zoom_out, link_document_page_view_reset], sources=['documents:document_page_view'])
        menu_facet.bind_links(links=[link_document_page_return, link_document_page_view], sources=[DocumentPage])
        menu_facet.bind_links(links=[link_document_page_navigation_first, link_document_page_navigation_previous, link_document_page_navigation_next, link_document_page_navigation_last, link_transformation_list], sources=[DocumentPage])
        menu_object.bind_links(links=[link_transformation_list], sources=[DocumentPage])

        namespace = StatisticNamespace(name='documents', label=_('Documents'))
        namespace.add_statistic(DocumentStatistics(name='document_stats', label=_('Document tendencies')))
        namespace.add_statistic(DocumentUsageStatistics(name='document_usage', label=_('Document usage')))

        post_initial_setup.connect(create_default_document_type, dispatch_uid='create_default_document_type')

        registry.register(Document)

        register_maintenance_links([link_clear_image_cache], namespace='documents', title=_('Documents'))
        register_model_list_columns(Document, [
            {
                'name': _('Thumbnail'), 'attribute':
                encapsulate(lambda x: document_thumbnail(x, gallery_name='documents:document_list', title=getattr(x, 'label', None), size=THUMBNAIL_SIZE))
            },
            {
                'name': _('Type'), 'attribute': 'document_type'
            }
        ])
