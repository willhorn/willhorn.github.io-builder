#!/usr/bin/python

import datetime
import os
import shutil
import subprocess
import sys

import jinja2
import markdown

from mdchecklistext import ChecklistExtension
from iopagebuilder import IOAboutBuilder, IOGoalsBuilder, IOBlogBuilder


def dir_check(dir):
    if not os.path.isdir(dir):
        raise Exception('directory not found: {0}'.format(dir))


class iobuilder:

    def __init__(self, base_dir):
        self.source_dir = os.path.join(base_dir, 'willhorn.github.io-builder')
        dir_check(self.source_dir)
        self.destination_dir = os.path.join(base_dir, 'willhorn.github.io')
        dir_check(self.destination_dir)
        self.md = markdown.Markdown(extensions=[ChecklistExtension()])
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(self.source_dir, 'templates'))
        )
        self.page_builder_classes = {
            'about': IOAboutBuilder,
            'goals': IOGoalsBuilder,
            'blog': IOBlogBuilder
        }
        self.page_builders = {}  # only create one builder per class and cache them here

    def get_content_from_dir(self, dir_path):
        content = {}
        os.chdir(dir_path)
        dir_contents = os.listdir(dir_path)
        for i in dir_contents:
            path = os.path.join(dir_path, i)
            if os.path.isdir(path) and not path.startswith('.'):
                content[i] = self.get_content_from_dir(path)
            elif i.endswith('.md'):
                name = i[:-3]
                content[name] = self.get_content_from_md(path)
                content[name]['name'] = name
        return content

    def get_content_from_md(self, path):
        with open(path, 'r') as f:
            md = f.read()
        publish_date = self.get_commit_date(path, -1)
        last_edit_date = self.get_commit_date(path, 0)
        return {
            'markdown': md,
            'markdown_line_count': len(md.splitlines()),
            'html': self.md.convert(md),
            'publish_date': publish_date,
            'publish_date_string': self._date_to_string(publish_date),
            'last_edit_date': last_edit_date,
            'last_edit_date_string': self._date_to_string(last_edit_date),
            'path': path
        }

    def _date_to_string(self, date):
        return date.strftime('%b %d, %Y %X %Z')

    def get_commit_date(self, path, pos):
        (dir_path, file_name) = os.path.split(path)
        os.chdir(dir_path)
        timestamps_str = subprocess.check_output(['git', 'log', '--format=%at', file_name]).decode('utf-8')
        timestamp_str = timestamps_str.splitlines()[pos]
        timestamp = int(timestamp_str)
        return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)

    def _clean_destination_dir(self):
        dir_contents = os.listdir(self.destination_dir)
        for i in dir_contents:
            path = os.path.join(self.destination_dir, i)
            if path.endswith('.html'):
                os.remove(path)
            elif os.path.isdir(path) and i == 'images':
                shutil.rmtree(path)

    def build_io(self):
        self._clean_destination_dir()
        content = self.get_content_from_dir(os.path.join(self.source_dir, 'content'))
        shutil.copytree(
            os.path.join(self.source_dir, 'content', 'images'),
            os.path.join(self.destination_dir, 'images')
        )
        for i in content:
            if content[i]:
                page_builder_class = self.page_builder_classes[i]
                page_builder = self._get_page_builder(page_builder_class)
                page_builder.build_page(i, content[i])
        return self.destination_dir

    def _get_page_builder(self, page_builder_class):
        if page_builder_class not in self.page_builders:
            self.page_builders[page_builder_class] = page_builder_class(
                self.template_env,
                self.destination_dir
            )
        return self.page_builders[page_builder_class]


if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        dir_check(base_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    b = iobuilder(base_dir)
    b.build_io()
