#!/usr/bin/python

import lxml.html, lxml.etree
import os, sys, subprocess
from copy import deepcopy
import re

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
        self.template = lxml.html.parse(os.path.join(self.source_dir, 'template.html'))

    def build_io(self):
        self.build_goals_page()
        return self.destination_dir

    def build_goals_page(self):
        template = deepcopy(self.template)
        root = template.getroot()
        nav_button = root.find(".//li[@id='nav_goals']")
        nav_button.set('class', 'nav_selected')
        main_content = root.find(".//section[@id='main_content']")
        main_content.set('class', 'goals_content flex_container')
        goals_dir = os.path.join(self.source_content_dir, 'goals')
        dir_check(goals_dir)
        for file in os.listdir(goals_dir):
            if file.endswith('.txt'):
                main_content.append(self.get_goal_list_html(file))
        destination_path = os.path.join(self.destination_dir, 'index.html')
        with open(destination_path, 'w') as f:
            f.write(lxml.html.tostring(template, pretty_print=True))
        # it's not really pretty printed, so clean up with https://github.com/htacg/tidy-html5
        subprocess.check_call(['tidy', '-im', '-w', '132', destination_path])
        return destination_path
                
    def get_goal_list_html(self, file):
        path = os.path.join(self.source_content_dir, 'goals', file)
        article = lxml.html.fromstring('<article class="goals_group"></article>')
        article.set('id', os.path.splitext(file)[0])
        goals = lxml.html.fromstring('<ul class="goals_list"></ul>')
        with open(path, 'rb') as f:
            for line in f:
                html = self.text_line_to_html(line)
                if html.tag == 'li':
                    goals.append(html)
                elif re.match(r'^h[1-6]$', html.tag):
                    html.set('class', 'goals_group_title')
                    article.append(html)
                else:
                    raise Exception("unexpected tag '{0}' in goals list {1}".format(html.tag, file))
        article.append(goals)
        return article
        
    def text_line_to_html(self, line):
        prefix, content = line.split(' ', 1)
        element = 'p'
        attributes = {}
        if re.match(r'^#{1,6}$', prefix):
            element = 'h' + str(len(prefix))
        elif prefix in ('*', '-', '+'):
            element = 'li'
        elif prefix == 'o':
            element = 'li'
            attributes = {'class': 'goal'}
        elif prefix == 'x':
            element = 'li'
            attributes = {'class': 'goal completed_goal'}
        elif re.match(r'^\d+\.$', prefix):
            element = 'li'
            attributes = {'class': 'goal'}
        content = self.link_to_html(content)
        html = lxml.html.fromstring('<{0}>{1}</{0}>'.format(element, content))
        for k, v in attributes.items():
            html.set(k, v)
        return html

    def linkrepl(self, matchobj):
        return '<a href="' + matchobj.group('href') + '">' + matchobj.group('content') + '</a>'

    def link_to_html(self, content):
        return re.sub(r'\[(?P<content>[^\]]+)\]\((?P<href>[^\)]+)\)', self.linkrepl, content)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        dir_check(base_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    b = iobuilder(base_dir)
    b.build_io()