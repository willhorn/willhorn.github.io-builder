#!/usr/bin/python

import lxml.html
import os, sys, subprocess
from copy import deepcopy
from mdchecklistext import ChecklistExtension
import markdown

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
        self.md = markdown.Markdown(extensions=[ChecklistExtension()])

    def build_io(self):
        self.build_about_page()
        self.build_goals_page()
        return self.destination_dir

    ### COMMON ###
    def set_selected_nav(self, root, nav_id):
        nav_button = root.find(".//li[@id='{0}']".format(nav_id))
        nav_button.set('class', 'nav_selected')
        
    def write_html(self, html, file):
        destination_path = os.path.join(self.destination_dir, file)
        with open(destination_path, 'w') as f:
            html_string = lxml.html.tostring(html, pretty_print=True, encoding="unicode")
            f.write(html_string)
        # it's not really pretty printed, so clean up with https://github.com/htacg/tidy-html5
        subprocess.check_call(['tidy', '-imq', '-w', '132', destination_path])
        return destination_path

    def md_convert(self, file):
        with open(file, 'r') as f:
            text = f.read()
        html = self.md.convert(text)
        return html

    ### ABOUT ###
    def build_about_page(self):
        template = deepcopy(self.template)
        root = template.getroot()
        self.set_selected_nav(root, 'nav_about')
        main_content = root.find(".//section[@id='main_content']")
        file = os.path.join(self.source_content_dir, 'about.md')
        main_content.append(lxml.html.fromstring(self.md_convert(file)))
        return self.write_html(template, 'index.html')

    ### GOALS ###
    def build_goals_page(self):
        template = deepcopy(self.template)
        root = template.getroot()
        self.set_selected_nav(root, 'nav_goals')
        main_content = root.find(".//section[@id='main_content']")
        main_content.set('class', 'goals_content flex_container')
        goals_dir = os.path.join(self.source_content_dir, 'goals')
        dir_check(goals_dir)
        article_template = '<article class="goals_group" id="{0}">{1}</article>'
        for file in os.listdir(goals_dir):
            if file.endswith('.md'):
                id = file.split('.')[0]
                path = os.path.join(goals_dir, file)
                article = article_template.format(id, self.md_convert(path))
                main_content.append(lxml.html.fromstring(article))
                # html.set('class', 'goals_group_title')
        return self.write_html(template, 'goals.html')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        dir_check(base_dir)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    b = iobuilder(base_dir)
    b.build_io()