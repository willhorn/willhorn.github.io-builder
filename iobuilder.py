#!/usr/bin/python

import datetime
import os
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
        self.page_builders = {
            'about': IOAboutBuilder(self.template_env, self.destination_dir),
            'goals': IOGoalsBuilder(self.template_env, self.destination_dir),
            'blog': IOBlogBuilder(self.template_env, self.destination_dir)
        }

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
        # TODO: append publish/edit dates to end of blog entries
        # if they're the same only include publish
        # markdown, html, publish_date, last_edit_date
        with open(path, 'r') as f:
            md = f.read()
        return {
            'markdown': md,
            'markdown_line_count': len(md.splitlines()),
            'html': self.md.convert(md),
            'publish_date': self.get_commit_date(path, -1),
            'last_edit_date': self.get_commit_date(path, 0),
            'path': path
        }

    def get_commit_date(self, path, pos):
        (dir_path, file_name) = os.path.split(path)
        os.chdir(dir_path)
        timestamps_str = subprocess.check_output(['git', 'log', '--format=%at', file_name]).decode('utf-8')
        timestamp_str = timestamps_str.splitlines()[pos]
        timestamp = int(timestamp_str)
        # dt.strftime('%b %d, %Y %X %Z')
        return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)

    def build_io(self):
        content = self.get_content_from_dir(os.path.join(self.source_dir, 'content'))
        for i in content:
            page_builder = self.page_builders[i]
            page_builder.build_page(i, content[i])
        return self.destination_dir


if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        dir_check(base_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    b = iobuilder(base_dir)
    b.build_io()
