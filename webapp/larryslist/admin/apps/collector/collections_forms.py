from jsonclient.backend import DBException
from larryslist.admin.apps.collector.models import CreateCollectionProc, EditCollectionBaseProc, EditCollectionArtistsProc, EditCollectionPublicationsProc
from larryslist.lib.formlib.formfields import BaseForm, IntField, CheckboxField, IMPORTANT, StringField, MultiConfigChoiceField, ApproxField, HiddenField, MultipleFormField, TypeAheadField, PlainHeadingField, ConfigChoiceField, URLField

__author__ = 'Martin'


class RegionOfInterest(MultipleFormField):
    fields = [
        StringField('name', "Region")
    ]

class BaseCollectionForm(BaseForm):
    id = 'basic'
    label = 'Basic'
    fields = [
        ApproxField('totalWorks', 'totalWorksAprx', "Total number of artworks in collection", IMPORTANT, label_classes="double")
        , ApproxField('totalArtists', 'totalArtistsAprx', "Total number of artists in collection", IMPORTANT, label_classes="double")
        , StringField("name", "Name of collection", IMPORTANT)
        , StringField("foundation", "Name of foundation")
        , IntField('started', "Started collecting in year")
        , PlainHeadingField("Art Genre / Movemment")
        , MultiConfigChoiceField('name', 'Genre', "Genre", "Genre")
        , PlainHeadingField("Medium of artworks")
        , MultiConfigChoiceField('name', 'Medium', "Medium", "Medium")
        , PlainHeadingField("Region of interest")
        , RegionOfInterest('Region', '')
    ]

    @classmethod
    def on_success(cls, request, values):
        values = {'id': request.matchdict['collectorId'], 'Collection':values}
        try:
            collection = CreateCollectionProc(request, {'Collector':values})
        except DBException, e:
            return {'success':False, 'message': e.message}
        return {'redirect': request.fwd_url("admin_collection_edit", collectionId = collection.id, stage='basic')}


class CollectionEditForm(BaseCollectionForm):
    fields = BaseCollectionForm.fields  + [
            HiddenField('id')
        ]
    @classmethod
    def on_success(cls, request, values):
        values = {'id': request.matchdict['collectorId'], 'Collection':values}
        try:
            collection = EditCollectionBaseProc(request, {'Collector':values})
        except DBException, e:
            return {'success':False, 'message': e.message}
        return {'success': True, 'message':"Changes saved!"}

class ArtistForm(MultipleFormField):
    fields = [
        TypeAheadField('name', "Artist", "/admin/search/artist", "Artist", classes='typeahead input-xxlarge')
    ]


class CollectionArtistsForm(BaseForm):
    id = 'artist'
    label = 'Artists'
    fields = [
        HiddenField('id')
        , PlainHeadingField("Artists in Collection")
        , ArtistForm('Artist', "Artist")
    ]

    @classmethod
    def on_success(cls, request, values):
        values = {'id': request.matchdict['collectorId'], 'Collection':values}
        try:
            collection = EditCollectionArtistsProc(request, {'Collector':values})
        except DBException, e:
            return {'success':False, 'message': e.message}
        return {'success': True, 'message':"Changes saved!"}

class PublicationsForm(MultipleFormField):
    fields = [
        StringField('title', "Title")
        , ConfigChoiceField('publisher', 'Publisher', 'Publisher')
        , IntField('year', "Year")
    ]


class CollectionWebsiteForm(BaseForm):
    id = 'website'
    label = 'Communication Platforms'
    fields = [
        HiddenField('id')
        , PlainHeadingField("Website")
        , URLField('website', "Webpage", attrs = IMPORTANT)
        , PlainHeadingField("Publications")
        , PublicationsForm('Publication', "", classes = "form-embedded-wrapper form-inline")
    ]

    @classmethod
    def on_success(cls, request, values):
        values = {'id': request.matchdict['collectorId'], 'Collection':values}
        try:
            collection = EditCollectionPublicationsProc(request, {'Collector':values})
        except DBException, e:
            return {'success':False, 'message': e.message}
        return {'success': True, 'message':"Changes saved!"}