class MenuItem(object):
    """ a simple class that contains minimal info about menu items """

    title=''
    action=''
    description=''

    def __init__(self, title='', action='', description=''):
          self.title=title
          self.action=action
          self.description=description
