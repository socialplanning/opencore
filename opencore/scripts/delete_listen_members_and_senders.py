from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from Testing.makerequest import makerequest
from zope.app.component.hooks import setSite
from Products.listen.content import WriteMembershipList

def delete_listen_members(app, users_or_emails, delete_member=True):
    """
    Use this at the `zopectl debug` prompt to remove a list of
    usernames or email addresses from ALL Listen subscriber and
    allowed_sender lists.  Useful for eg. nuking spammers.

    If delete_member==True (default yes), then also delete any
    matching member from the portal too.

    DOES NOT AUTOMATICALLY COMMIT, you have to do that yourself
    """
    emails = set([m for m in users_or_emails if m.count('@')])
    mem_ids = set([m for m in users_or_emails if not m.count('@')])

    app=makerequest(app)
    portal = app.openplans
    setSite(portal)
    newSecurityManager(app.REQUEST, UnrestrictedUser('root', '', [], []).__of__(app))
    mship = portal.portal_membership
    mdata = portal.portal_memberdata

    # First get member ids for all the emails, and vice versa.  This
    # way we're sure to clean up as much as possible regardless of which way
    # the input is specified.
    for e in sorted(emails):
        results = mdata.searchMemberDataContents('email', e)
        mem_ids.update([r['username'] for r in results])
    for i in sorted(mem_ids):
        results = mdata.searchMemberDataContents('id', i)
        emails.update([r['email'] for r in results])
    
    users_or_emails = sorted(mem_ids.union(emails))
    print "=" * 50
    print "Removing list subscriptions for %r" % users_or_emails
    cat = portal.portal_catalog
    brains = cat.unrestrictedSearchResults(portal_type = 'Open Mailing List')
    lists = [(b.getPath(), b.getObject()) for b in brains]
    for path, ml in sorted(lists):
        ml =  WriteMembershipList(ml)
        for astring in users_or_emails:
            if ml.is_allowed_sender(astring):
                print "Removing sender %s from %s" % (astring, path)
                ml.remove_allowed_sender(astring)
            if ml.is_subscribed(astring):
                print "Removing subscriber %s from %s" % (astring, path)
                ml.unsubscribe(astring)

    if delete_member:
        # I believe that our project memberships get cleaned up
        # automatically when the member gets deleted; this may just be
        # because TeamSpace looks up the member object before looking
        # up memberships, or it may actually do some cleanup, don't
        # know.

        # BUT... we also want to know about any projects that had no
        # other members. Those are likely junk.
        # SO, let's find all relevant projects; code copied from
        # opencore.browser.base
        teamtool = portal.portal_teams
        default_states = teamtool.getDefaultActiveStates()
        mship_brains = cat(id=list(mem_ids), portal_type='OpenMembership',
                           review_state=default_states)

        teams = [i.getPath().split('/')[-2] for i in mship_brains]
        project_brains = cat(portal_type='OpenProject', id=teams)
        print "=" * 50
        print "Searching for newly orphaned projects..."

        for pb in project_brains:
            proj = pb.getObject()
            other_members = [m for m in proj.projectMemberIds() if (not m in mem_ids)]
            if not other_members:
                print "Project %r has no other members! Might want to kill it." % proj.getId()


        # Delete the member.
        print "=" * 50
        print "Removing members %r from the site" % mem_ids
        mship.deleteMembers(mem_ids, delete_memberareas=True,
                            delete_localroles=False)
        # Crawl the entire site cleaning up local roles, whee.
        print "=" * 50
        print "Removing local roles %s from the site (can take a long time)" % mem_ids
        mship.deleteLocalRoles(portal, mem_ids,
                               reindex=True, recursive=True)

        
    print "-" * 50
    print "Done!"


import transaction
# This is not much of a CLI. Oh well, hack it as you like.
import sys
members = sys.argv[1:]
if not members:
    sys.stderr.write("No members specified")
    sys.exit(1)
delete_listen_members(app, sys.argv[1:], delete_member=True)
transaction.commit()

