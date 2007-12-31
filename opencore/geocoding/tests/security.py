
def test_read_anonymous():
    """Anyone should be able to read.

    >>> self.logout()
    >>> IReadGeo.providedBy(self.proj_reader)
    True
    >>> print self.proj_reader.get_geolocation()
    None
    >>> print self.proj_reader.is_geocoded()
    False
    >>> self.proj_reader.location_img_url()
    ''
    """

def test_read_private_anonymous():
    # XXX Test anon with a private project, should not be able to view.
    pass

def test_write_anonymous():
    """The write interface should be restricted to project admins.

    >>> self.logout()
    >>> IWriteGeo.providedBy(self.proj_writer)
    True
    >>> self.proj_writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'geocode_from_form' in this context
    >>> self.proj_writer.set_geolocation(())
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'set_geolocation' in this context
    """

def test_write_member():
    """
    >>> m1 = self.project.acl_users.getUser('m1')
    >>> bool(m1.has_permission('Modify portal content', self.project))
    False
    >>> bool(m1.has_permission('Modify portal content', self.proj_writer.geocode_from_form))
    False
    >>> from AccessControl.PermissionRole import rolesForPermissionOn
    >>> rolesForPermissionOn('Modify portal content', self.proj_writer.geocode_from_form)
    ('Manager',)
    >>> self.login('m1')
    >>> self.proj_writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'geocode_from_form' in this context
    >>> self.proj_writer.set_geolocation(())
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'set_geolocation' in this context
    """

def test_write_manager():
    """
    Project manager can call restricted methods.
    >>> m3 = self.project.acl_users.getUser('m3')
    >>> bool(m3.has_permission('Modify portal content', self.project))
    True
    >>> bool(m3.has_permission('Modify portal content', self.proj_writer.geocode_from_form))
    True
    >>> self.login('m3')
    >>> self.proj_writer.geocode_from_form()
    ()
    >>> self.proj_writer.set_geolocation(())
    False
    """
