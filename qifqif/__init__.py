#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

from __future__ import (print_function, unicode_literals)

import argparse
import os
import sys

from blessed import Terminal
try:
    from collections import OrderedDict
except ImportError:  # python 2.6
    from ordereddict import OrderedDict

from qifqif import tags
from qifqif.ui import diff, set_completer

term = Terminal()
CLEAR = term.move_up + term.move_x(0) + term.clear_eol


def quick_input(prompt, choices=''):
    """Reads a line from input, converts it to a string (stripping a trailing
       newline), and returns that. If no input, returns default choice.
    """

    default = [x for x in choices if x.isupper()]
    default = default[0] if default else ''
    _input = raw_input('%s%s' % (prompt,
                       (' [%s] ?' % ','.join(choices)) if choices else ':'))
    if _input in choices:
        _input = _input.upper()
    return _input or default


def query_tag(cached_cat):
    set_completer(sorted(tags.TAGS.keys()))
    tag = quick_input('Category')
    print(CLEAR, end='')

    if not tag and cached_cat:
        erase = quick_input('Remove existing tag', 'yn')
        if erase.upper() == 'N':
            tag = cached_cat
    set_completer()
    return tag


def query_match(cached_match, payee):
    while True:
        match = quick_input('Match')
        if not tags.is_match(match, payee):
            print(CLEAR + '%s Match rejected: %s' %
                  (term.red('✖'), diff(payee, match, term, as_error=True)))
        else:
            print(CLEAR + "%s Match accepted: %s" %
                  (term.green('✔'), str(match) if match else
                   term.red('<none>')))
            break
    return match


def query_save():
    return quick_input('---\nSave', 'yn') == 'Y'


def process_transaction(t, cached_tag, cached_match, options={}):
    print('Amount..: %s' % (term.green(str(t['amount'])) if
          (t['amount'] and float(t['amount']) > 0)
          else term.red(str(t['amount']))))
    print('Payee...: %s' % (diff(cached_match, t['payee'], term)
                            if cached_match
                            else t['payee'] or term.red('<none>')))
    for field in ('memo', 'number'):
        if t[field]:
            pad_width = 8
            print('%s: %s' % (field.title().ljust(pad_width, '.'), t[field]))
    tag, match = cached_tag, cached_match

    if not options.get('batch', False):
        edit = False
        print('cached %s' % cached_tag)
        if cached_tag:
            if options.get('audit', False):
                msg = "Edit '%s' category" % term.green(cached_tag)
                edit = quick_input(msg, 'yN') == 'Y'
                print('Edit ?=> %s' % edit)
        if t['payee'] and (not cached_tag or edit):
            tag = query_tag(cached_tag)
        print('Category: %s' % (term.green(tag) if tag
                                else term.red('<none>')))
        if tag and (not cached_match or edit):
            match = query_match(cached_match, t['payee'])
    return tag or cached_tag, match


def process_file(transactions, options={}):
    tag = None

    for t in transactions:
        cached_tag, cached_match = tags.find_tag_for(t['payee'])

        tag, match = process_transaction(t, cached_tag, cached_match, options)

        tags.edit(cached_tag, cached_match, tag, match, options)
        t['category'] = tag
        if 'payee' not in t:
            print('Skip transaction: no payee')
        if not options.get('batch', False):
            separator = '-' * 3
            print(separator)
    return transactions


FIELDS = {'D': 'date', 'T': 'amount', 'P': 'payee', 'L': 'category',
          'N': 'number', 'M': 'memo'}


def create_transaction(content=[]):
    return OrderedDict(content)


def parse_file(filepath, options=None):
    """Return list of transactions as ordered dicts with fields save in same
       order as they appear in input file.
    """
    res = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    transaction = create_transaction()
    for (idx, line) in enumerate(lines):
        field_id = line[0]
        if field_id == '^':
            res.append(transaction)
            transaction = create_transaction()
        elif field_id in FIELDS.keys():
            transaction[FIELDS[field_id]] = line[1:].strip()
        else:
            transaction[idx] = line
    if transaction:
        res.append(transaction)
    # post-check to not interfere with present keys order
    no_payee_count = 0
    for t in res:
        for field in FIELDS.values():
            if field not in t:
                t[field] = None
                if field == 'payee':
                    no_payee_count += 1
    if (not options or not options['batch']) and no_payee_count:
        with term.location():
            msg = ("%s of %s transactions have no 'Payee': field. "
                   "Continue")
            ok = quick_input(msg % (no_payee_count, len(res)), 'Yn')
            if ok != 'Y':
                exit(1)
            else:
                print(CLEAR)
    return res


def dump_to_file(dest, transactions, options=None):
    reverse_fields = {}
    for (k, v) in FIELDS.items():
        reverse_fields[v] = k
    lines = []
    for t in transactions:
        for key in t:
            if t[key]:
                try:
                    lines.append('%s%s\n' % (reverse_fields[key], t[key]))
                except KeyError:  # Unrecognized field
                    lines.append(t[key])
        lines.append('^\n')
    res = ''.join(lines[:-1]).strip()
    with open(dest, 'w') as f:
        f.write(res)
    if options and options['batch']:
        print(res)
    return res


def highlight_char(word, n=0):
    """Return word with n-th letter highlighted
    """
    return word[:n] + term.reverse(word[n]) + word[n + 1:]


def build_parser():
    """Build application argument parser
    """
    parser = argparse.ArgumentParser(
        description='Enrich your .QIF files with tags. '
        'See https://github.com/Kraymer/qifqif for more infos.')
    parser.add_argument('src', metavar='QIF_FILE',
                        help='.QIF file to process', default='')
    parser.add_argument('-a', '--audit-mode', dest='audit',
                        action='store_true', help=('pause after '
                                                   'each transaction'))
    parser.add_argument('-c', '--config', dest='config',
                        help='configuration filename in json format. '
                        'DEFAULT: ~/.qifqif.json',
                        default=os.path.join(os.path.expanduser('~'),
                                             '.qifqif.json'))
    parser.add_argument('-o', '--output', dest='dest',
                        help='output filename. '
                        'DEFAULT: edit input file in-place', default='')
    parser.add_argument('-b', '--batch-mode', action='store_true',
                        dest='batch', help=('skip transactions that require '
                                            'user input'))
    return parser


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = build_parser()

    args = vars(parser.parse_args())
    if not args['dest']:
        args['dest'] = args['src']
    if args['audit'] and args['batch']:
        print(('Error: cannot activate batch-mode when audit-mode is already ',
              'on'))
        exit(1)

    original_tags = tags.load(args['config'])

    transactions = parse_file(args['src'], options=args)
    save = True
    try:
        transactions = process_file(transactions, options=args)
    except KeyboardInterrupt:
        save = query_save()

    if save is True:
        dump_to_file(args['dest'], transactions, options=args)
    else:  # restore original tags
        tags.save(args['config'], original_tags)
    exit(0)


if __name__ == "__main__":
    sys.exit(main())
