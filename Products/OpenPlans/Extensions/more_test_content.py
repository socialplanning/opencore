from Products.OpenPlans.Extensions.create_test_content import create_test_content

projects_map = {}

members_map = {'m5':{'fullname': 'Member Five',
                     'password': 'testy',
                     'email': 'notreal5@example.com',
                     'projects': {'p3': tuple()},
                     },
               'm6':{'fullname': 'Member Six',
                     'password': 'testy',
                     'email': 'notreal6@example.com',
                     'projects': {'p3': tuple()},
                     },
               'm7':{'fullname': 'Member Seven',
                     'password': 'testy',
                     'email': 'notreal7@example.com',
                     'projects': {'p3': tuple()},
                     },
               'm8':{'fullname': 'Member Eight',
                     'password': 'testy',
                     'email': 'notreal8@example.com',
                     'projects': {'p3': tuple()},
                     },
               'm9':{'fullname': 'Member Nine',
                     'password': 'testy',
                     'email': 'notreal9@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mA':{'fullname': 'Member Ten',
                     'password': 'testy',
                     'email': 'notrealA@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mB':{'fullname': 'Member Eleven',
                     'password': 'testy',
                     'email': 'notrealB@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mC':{'fullname': 'Member Twelve',
                     'password': 'testy',
                     'email': 'notrealC@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mD':{'fullname': 'Member Thirteen',
                     'password': 'testy',
                     'email': 'notrealD@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mE':{'fullname': 'Member Fourteen',
                     'password': 'testy',
                     'email': 'notrealE@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mF':{'fullname': 'Member Fifteen',
                     'password': 'testy',
                     'email': 'notrealF@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mG':{'fullname': 'Member Sixteen',
                     'password': 'testy',
                     'email': 'notrealG@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mH':{'fullname': 'Member Seventeen',
                     'password': 'testy',
                     'email': 'notrealH@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mI':{'fullname': 'Member Eighteen',
                     'password': 'testy',
                     'email': 'notrealI@example.com',
                     'projects': {'p3': tuple()},
                     },
               'mJ':{'fullname': 'Member Nineteen',
                     'password': 'testy',
                     'email': 'notrealJ@example.com',
                     'projects': {'p3': tuple()},
                     },
               }


def more_test_content(self):
    return create_test_content(self, projects_map, members_map)
