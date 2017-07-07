#!/usr/bin/python

import os
import subprocess
import sys

import jinja2
import markdown

from mdchecklistext import ChecklistExtension


def dir_check(dir):
    if not os.path.isdir(dir):
        raise Exception('directory not found: {0}'.format(dir))


class iobuilder:

    def __init__(self, base_dir):
        self.source_dir = os.path.join(base_dir, 'willhorn.github.io-builder')
        dir_check(self.source_dir)
        self.source_content_dir = os.path.join(self.source_dir, 'content')
        dir_check(self.source_content_dir)
        self.destination_dir = os.path.join(base_dir, 'willhorn.github.io')
        dir_check(self.destination_dir)
        self.md = markdown.Markdown(extensions=[ChecklistExtension()])
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(self.source_dir, 'templates'))
        )

    def build_io(self):
        self.build_about_page()
        self.build_goals_page()
        return self.destination_dir

    # COMMON
    def write_html(self, html, file):
        destination_path = os.path.join(self.destination_dir, file)
        with open(destination_path, 'w') as f:
            f.write(html)
        # clean up with https://github.com/htacg/tidy-html5
        subprocess.check_call(['tidy', '-imq', '-w', '132', destination_path])
        return destination_path

    def md_convert(self, file):
        with open(file, 'r') as f:
            text = f.read()
        html = self.md.convert(text)
        return html

    # ABOUT
    def build_about_page(self):
        template = self.template_env.get_template('about.html')
        md_file = os.path.join(self.source_content_dir, 'about.md')
        html = self.md_convert(md_file)
        html = template.render(html=html)
        return self.write_html(html, 'index.html')

    # GOALS
    def build_goals_page(self):
        template = self.template_env.get_template('goals.html')
        goals_dir = os.path.join(self.source_content_dir, 'goals')
        dir_check(goals_dir)
        goal_groups = []
        for file in os.listdir(goals_dir):
            if file.endswith('.md'):
                path = os.path.join(goals_dir, file)
                goal_group = {
                    'id': file.split('.')[0],
                    'html': self.md_convert(path)
                }
                goal_groups.append(goal_group)
        html = template.render(goal_groups=goal_groups)
        return self.write_html(html, 'goals.html')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        dir_check(base_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    b = iobuilder(base_dir)
    b.build_io()
