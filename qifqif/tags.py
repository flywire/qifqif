#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

"""Cache mapping categories with associated keywords"""

import json
import os
import re

TAGS = dict()


def rulify(line, fields):
    """Make a rule from a line containing tag markers and matching tokens
    """
    print('ya')
    tokens = re.split(r'(\b%s\b)' % '|'.join(
                      [x. lower() for x in fields.keys()]), line)
    curr_field = 'payee'  # use payee if no field marker in line
    rule = dict()
    rule[curr_field] = []
    for tok in tokens:
        tok = tok.upper()
        if tok in fields.keys():
            if not len(rule[curr_field]):
                print('del %s' % curr_field)
                del rule[curr_field]
            print ('> %s %s' % (rule, curr_field))
            curr_field = fields[tok]
            rule[curr_field] = []
        elif tok:
            rule[curr_field].append(tok.strip())
    return rule


def is_match(t, rule):
    """Returns (True, None) if line matches given rule or (False, field) if no
       match with field being the field that fails matching.
    """
    for field in rule:
        if rule[field]:
            pattern = r'%s.*' % '.*'.join([re.escape(x) for x in rule[field]])
            m = re.search(pattern, t[field])
            if not m:
                return False, field
    return True, None


def find_tag_for(t):
    """If payee satisfies a matching rule, returns corresponding tuple
       (tag, keyword).
    """
    res = []
    if t:
        print(TAGS)
        for (tag, matchers) in TAGS.items():
            for matcher in matchers:
                if is_match(t, matcher):
                    res.append((tag, matcher))
    if res:
        return max(res, key=lambda x: len(x[1]))
    return None, None


def load(filepath):
    """Load tags dictionary.
    """
    global TAGS
    if os.path.isfile(filepath):
        with open(filepath, 'r') as cfg:
            try:
                TAGS = json.load(cfg)
            except Exception as e:
                print("Error loading '%s'.\n%s" % (filepath, e))
                exit(1)
    else:
        TAGS = {}
    return TAGS


def save(filepath, tags=None):
    """Save tags dictionary on disk
    """
    if not tags:
        tags = TAGS
    with open(filepath, 'w+') as cfg:
        cfg.write(json.dumps(tags,
                  sort_keys=True, indent=4, separators=(',', ': ')))


def edit(cached_tag, cached_match, tag, match, options):
    """Save a tag modification into dictionary and save the latter on file.
    """
    global TAGS
    match = match.upper()
    tags = TAGS.copy()
    if tag and tag != cached_tag:
        if cached_tag:
            tags[cached_tag].remove(cached_match)
            if not tags[cached_tag]:
                del tags[cached_tag]
        if tag and match:
            if tag not in tags:
                tags[tag] = [match]
            else:
                tags[tag].append(match)
    elif match and match != cached_match:
        if cached_match:
            tags[tag].remove(cached_match)
        tags[tag].append(match)
    else:  # no diff
        return

    TAGS = tags
    if not options.get('dry-run', False):
        save(options['config'])
