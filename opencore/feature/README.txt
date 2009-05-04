Add the ability to feature a project, and retrieve the metadata for the latest
featured project.

    >>> from opencore.feature import feature_project, get_featured_project_metadata

First querying for a featured project should not return any results, but it
shouldn't blow up either::

    >>> get_featured_project_metadata() is None
    True


After featuring a project, we are able to retrieve the metadata

    >>> feature_project(project_id='p1')
    >>> from pprint import pprint
    >>> pprint(get_featured_project_metadata())
    {'project_id': 'p1',
     'timestamp': datetime.datetime(...)}

When we feature a new project, the metadata changes:

    >>> feature_project(project_id='p2')
    >>> pprint(get_featured_project_metadata())
    {'project_id': 'p2',
     'timestamp': datetime.datetime(...)}

You can even feature a project that doesn't exist. Higher level code (like view
code) will have to ensure that only valid project ids get stored, or to make
sure to handle invalid project ids gracefully. Both is probably best, so that
if a featured project gets deleted there are no explosions.

    >>> feature_project(project_id='this project id does not exist')
    >>> pprint(get_featured_project_metadata())
    {'project_id': 'this project id does not exist',
     'timestamp': datetime.datetime(...)}
