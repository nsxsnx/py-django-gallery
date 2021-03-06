# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-31 20:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import mptt.fields
import photo.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, max_length=128)),
                ('url', models.SlugField(blank=True, editable=False, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('public', models.BooleanField(db_index=True, default=False)),
                ('featured', models.BooleanField(db_index=True, default=False)),
                ('no_watermark', models.BooleanField(default=False)),
                ('counter', models.PositiveSmallIntegerField(default=0, editable=False, null=True, verbose_name=b'#')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, db_index=True, max_length=128)),
                ('image', models.ImageField(blank=True, max_length=255, upload_to=photo.models.upload_path_i)),
                ('thumbnail', models.ImageField(blank=True, max_length=255, upload_to=photo.models.upload_path_t)),
                ('album', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='photo.Album')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=50, unique=True)),
                ('public', models.BooleanField(default=False)),
                ('menu', models.BooleanField(db_index=True, default=False, verbose_name=b'Show in menu')),
                ('counter', models.PositiveIntegerField(default=0, editable=False, null=True, verbose_name=b'#')),
                ('featured', models.BooleanField(db_index=True, default=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('cover', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='photo.Image')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='photo.Tag')),
            ],
            managers=[
                ('_default_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='album',
            name='cover',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='photo.Image'),
        ),
        migrations.AddField(
            model_name='album',
            name='tags',
            field=models.ManyToManyField(blank=True, to='photo.Tag'),
        ),
        migrations.AlterIndexTogether(
            name='tag',
            index_together=set([('public', 'menu'), ('public', 'featured')]),
        ),
    ]
