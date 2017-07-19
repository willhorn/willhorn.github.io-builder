import os
import subprocess


class IOPageBuilder:

    def __init__(self, template_env, destination_dir, md):
        self._template_env = template_env
        self._template_name = None
        self._destination_dir = destination_dir
        self._destination_relative_path = None
        self._md = md

    def _write_page(self, html, destination_relative_path):
        destination_path = os.path.join(self._destination_dir, destination_relative_path)
        with open(destination_path, 'w') as f:
            f.write(html)
        # clean up with https://github.com/htacg/tidy-html5
        subprocess.check_call(['tidy', '-imq', '-w', '132', destination_path])
        return destination_relative_path

    def build_page(self, name, content):
        prepared_content = self._prepare_content(content)
        template_name = self._get_template_name(name)
        template = self._template_env.get_template(template_name)
        page_html = template.render(prepared_content)
        destination_relative_path = self._get_destination_relative_path(name)
        return self._write_page(page_html, destination_relative_path)

    def _get_template_name(self, name):
        if self._template_name is None:
            self._template_name = name + '.html'
        return self._template_name

    def _get_destination_relative_path(self, name):
        if self._destination_relative_path is None:
            self._destination_relative_path = name + '.html'
        return self._destination_relative_path

    def _prepare_content(self, content):
        return content


class IOAboutBuilder(IOPageBuilder):

    def _get_destination_relative_path(self, name):
        return 'index.html'


class IOGoalsBuilder(IOPageBuilder):
    COLUMN_COUNT = 2

    def _prepare_content(self, content):
        # rev sort by length
        # place into column with smallest total length
        goal_groups = list(content.values())
        goal_groups.sort(key=lambda x: x['markdown_line_count'], reverse=True)
        columns = []
        for i in range(self.COLUMN_COUNT):
            columns.append({'names': [], 'line_count': 0})
        for goal_group in goal_groups:
            columns[0]['names'].append(goal_group['name'])
            columns[0]['line_count'] += (goal_group['markdown_line_count'] + 1)  # plus 1 for the header
            columns.sort(key=lambda x: x['line_count'])  # so we always append to the shortest column
        columns.reverse()  # looks nicer to have longer column first
        order = []
        for column in columns:
            order += column['names']
        for i in range(len(order)):
            name = order[i]
            content[name]['order'] = i
        return {'goal_groups': list(content.values())}


class IOBlogBuilder(IOPageBuilder):

    def _prepare_content(self, content):
        blog_entry_builder = IOBlogEntryBuilder(
            self._template_env,
            self._destination_dir,
            self._md
        )
        for name, entry in content.items():
            content[name]['relative_path'] = blog_entry_builder.build_page(name, entry)
            content[name]['preview_html'] = self._get_blog_preview(entry)
        blog_entries = list(content.values())
        blog_entries.sort(key=lambda x: x['publish_date'], reverse=True)  # sort previews by published date
        return {'blog_entries': blog_entries}

    def _get_blog_preview(self, entry):
        preview = entry['markdown'][:801]
        preview = preview.rsplit(maxsplit=1)[0]
        preview = preview.rstrip().rstrip('.') + '...'
        return self._md.convert(preview)


class IOBlogEntryBuilder(IOPageBuilder):

    def _get_destination_relative_path(self, name):
        base = os.path.splitext(name)[0]
        return 'blog/{}.html'.format(base)

    def _get_template_name(self, name):
        return 'blog_entry.html'

    def _prepare_content(self, content):
        content['show_last_edit_date'] = content['last_edit_date'] != content['publish_date']
        return content
