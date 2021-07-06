from django import forms
from photo.models import Tag
from django.contrib.admin.widgets import FilteredSelectMultiple

class AddTagForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), widget=FilteredSelectMultiple('tags', False))
    act = forms.ChoiceField(choices = (('add', 'add'), ('remove', 'remove')), label = 'Action')
    class Media:
        extend = False
        css = { 'all':[
              'admin/css/forms.css',
              'admin/css/widgets.css',
              ]
              }
        js = [
             'admin/js/core.js',
             '/static/admin/js/admin/RelatedObjectLookups.js',
             'admin/js/jquery.js',
             'admin/js/jquery.init.js',
             'admin/js/SelectBox.js',
             'admin/js/SelectFilter2.js',
             '/admin/jsi18n/',
             ]

class RenameForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    find = forms.CharField(label='Find string', required=True)
    replace = forms.CharField(label='Replace with', required=False)
    only_name = forms.BooleanField(label='Change only name (preserves URL, JSON description, etc.)', required = False)

class AddAlbumForm(forms.Form):
    path = forms.CharField(label='From path', required=True)
    url = forms.CharField(label='From url', required=False)

class ContactForm(forms.Form):
    name = forms.CharField(label='Your name', required=True, max_length=32, widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(label='Your e-mail', required=True, max_length=32, widget=forms.TextInput(attrs={'class':'form-control'}))
    subject = forms.CharField(label='Subject', required=True, max_length=128, widget=forms.TextInput(attrs={'class':'form-control'}))
    message = forms.CharField(label='Message', required=True, max_length=2048, widget=forms.Textarea(attrs={'class':'form-control'}))
