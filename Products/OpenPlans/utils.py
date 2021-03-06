import sys
from StringIO import StringIO

from TAL.TALInterpreter import TALInterpreter

from Products.CMFCore.utils import getToolByName

def macro_render(macro, aq_ob, context, **kwargs):
    buffer = StringIO()
    TALInterpreter(macro, {}, context, buffer)(**kwargs)
    return buffer.getvalue()

def superMethod(*args, **kwargs):
    """When invoked calls the first baseclass occurance of the calling
    method with args.
    """
    try:
        frame = sys._getframe().f_back
        methodname = frame.f_code.co_name
        instance = frame.f_locals['self']
        caller = frame.f_code
    finally:
        del frame

    for cls in instance.__class__.__bases__:
        method = getattr(cls, methodname, None)
        if method:
            if method.func_code is caller: continue
            return method(instance, *args, **kwargs)

    raise AttributeError, methodname

def add_form_controller_overrides(portal, actions):
    fc = getToolByName(portal, 'portal_form_controller', None)
    if fc is not None:
        for action in actions:
            fc.addFormAction(action['template'],
                             action['status'],
                             action['context'],
                             action['button'],
                             action['action'],
                             action['expression'])


def remove_form_controller_overrides(portal, actions):
    fc = getToolByName(portal, 'portal_form_controller', None)
    # Fake a request because form controller needs one to delete actions
    fake_req = DummyRequest()
    i = 0
    for fc_act in fc.listFormActions(1):
        for action in actions:
            if (action['template'] == fc_act.getObjectId() and
                action['status'] == fc_act.getStatus() and
                action['context'] == fc_act.getContextType() and
                action['button'] == fc_act.getButton() and
                action['action'] == fc_act.getActionType() and
                action['expression'] == fc_act.getActionArg()):
                fake_req.form['del_id_%s'%i]=True
                fake_req.form['old_object_id_%s'%i]=action['template'] or ''
                fake_req.form['old_context_type_%s'%i]=action['context'] or ''
                fake_req.form['old_button_%s'%i]=action['button'] or ''
                fake_req.form['old_status_%s'%i]=action['status'] or ''
        i = i+1
    # Use the private method because the public one does a redirect
    fc._delFormActions(fc.actions,fake_req)

def get_project(context):  #XXX unused??
    """Given a context, return the nearest/parent openplans project
    """
    from opencore.interfaces import IProject
    chain = context.aq_chain
    for item in chain:
        if IProject.providedBy(item):
            return item
    raise LookupError(
        "No project could be found starting from the context %r"
        % context)

# Fake request class to satisfy formcontroller removal policy
class DummyRequest(dict):
    def __init__(self):
        self.form = {}
