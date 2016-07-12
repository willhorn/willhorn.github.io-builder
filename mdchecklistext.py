import markdown
import re

# ideally this would inherit from markdown.blockprocessors.OListProcessor
# however, I could not find a clean way to inject class attributes based on prefix
class ChecklistProcessor(markdown.blockprocessors.BlockProcessor):

    RE = re.compile(r'^[xo][ ]+.*')
    ITEM_RE = re.compile(r'^(x|o)[ ]+(.*)$')
    ITEM_CLASSES = {
        'x': ['goal', 'completed_goal'],
        'o': ['goal']
    }
    HEADER_RE = re.compile(r'^h[1-6]$')

    def test(self, parent, block):
        return bool(self.RE.match(block))

    def run(self, parent, blocks):
        header = self.lastChild(parent)
        if header is not None and self.HEADER_RE.match(header.tag) is not None:
            header.set('class', 'goals_group_title')
        goals = markdown.util.etree.SubElement(parent, 'ul', {'class': 'goals_list'})
        for prefix, content in self.get_items(blocks.pop(0)):
            classes = ' '.join(self.ITEM_CLASSES[prefix])
            goal = markdown.util.etree.SubElement(goals, 'li', {'class': classes})
            goal.text = content

    def get_items(self, block):
        items = []
        for line in block.split('\n'):
            m = self.ITEM_RE.match(line)
            if m is not None:
                items.append(list(m.groups()))
            else:
                items[-1][1] = items[-1][1] + "\n" + line
        return items

class ChecklistExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.add('checklist', ChecklistProcessor(md.parser), '<olist')