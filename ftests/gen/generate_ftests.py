#!/usr/bin/python

from csv import reader
import os.path

def cartesian (lists, prefix=[]):
    if len(lists) == 1:
        return [prefix + [x] for x in lists[0]]
    else:
        return sum([cartesian(lists[1:], prefix=prefix+[x]) for x in lists[0]], [])

def array_from_csv(csv):
    data = []
    for line in csv:
        if line[0].startswith("#"):
            continue #header
        if not line[0]:
            continue #blank line

        last = None
        for i in range(len(line)):
            value = line[i]
            if not value:
                line[i] = last
            else:
                last = value

        line[0] = line[0].lower().replace(" ", "_")
        data.append(line)
    return data

def as_admin(user, test):
    tests = []
    if user:
        tests.append("logout")                
    tests.append("login(user=${u1_name})")
    tests.append(test)
    tests.append("logout")                
    if user:
        tests.append("login(user=${%s_name})" % user)
    return tests

def test_exists(test):
    return os.path.exists(test + ".tsuite") or os.path.exists(test + ".twill")

def generate_test_suite(data, test_file_name, statuses):
    test_file = open(test_file_name, "w")

    print >>test_file, "setup_gen"

    preludes = []
    tests = []
    users = {'anon' : None, 'auth' : 'u3', 'pm' : 'u2', 'pa': 'u1'}
    for i in range(len(statuses)):
        status = statuses[i]
        #generate status prelude
        for prelude in status:
            tests.append("prelude_%s" % prelude)

        user = users[status[1]]
        
            
        nonce="the_nonce_is_%d" % i

        for row in data:
            test_title = row[0]
            if i == 0:
                #first time only, run per-action preludes
                prelude_name = "prelude_%s"  % test_title
                if test_exists(prelude_name):
                    preludes.append(prelude_name)

            #repeated preludes are executed per-test as admin
            prelude_name = "repeated_prelude_%s"  % test_title
            if test_exists(prelude_name):            
                tests += as_admin(user, prelude_name)

            if not test_exists(test_title + "_yes"):
                continue #no such test

            expected = row[i + 1]
            if expected == "*":
                #impossible test
                continue
            elif expected == "y":
                tests.append(test_title + '_yes(nonce="%s")' % (nonce))
            elif expected == "n":
                tests.append(test_title + '_no(nonce="%s")' % (nonce))
            else:
                tests.append("#No test generated for %s" % test_title)

            postlude_name = "repeated_postlude_%s"  % test_title
            if test_exists(postlude_name):            
                tests += as_admin(user, postlude_name)


        for prelude in status:
            tests.append("postlude_%s" % prelude)


    for prelude in preludes:
        print >>test_file, prelude

    print >>test_file, "after_preludes"
    for test in tests:
        print >>test_file, test

csv = reader(open("per_project.csv"))
per_project_data = array_from_csv(csv)
statuses = cartesian([["open", "medium", "closed"], ["anon", "auth", "pm", "pa"]])
generate_test_suite(per_project_data, "per_project.tsuite", statuses)
