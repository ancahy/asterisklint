# AsteriskLint -- an Asterisk PBX config syntax checker
# Copyright (C) 2015-2016  Walter Doekes, OSSO B.V.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from unittest import expectedFailure

from asterisklint import FileDialplanParser
from asterisklint.alinttest import ALintTestCase, ignoreLinted


@ignoreLinted('H_DP_GENERAL_MISPLACED', 'H_DP_GLOBALS_MISPLACED')
class SamePrioTest(ALintTestCase):
    def check_values(self, reader):
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.general), 0)
        self.assertEqual(len(dialplan.globals), 0)
        self.assertEqual(len(dialplan.contexts), 1)

        context = dialplan.contexts[0]
        self.assertEqual(len(context), 3)
        self.assertEqual(set(i.pattern.raw for i in context), set(['pattern']))
        self.assertEqual([i.prio for i in context], [1, 2, 3])
        self.assertEqual([i.app.raw for i in context],
                         ['NoOp({})'.format(i) for i in range(1, 4)])

    def test_exten_num_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
exten => pattern,2,NoOp(2)
exten => pattern,3,NoOp(3)
''')
        self.check_values(reader)

    def test_exten_n_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
exten => pattern,n,NoOp(2)
exten => pattern,n,NoOp(3)
''')
        self.check_values(reader)

    def test_same_n_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
 same => n,NoOp(2)
 same => n,NoOp(3)
''')
        self.check_values(reader)


@ignoreLinted('H_DP_GENERAL_MISPLACED', 'H_DP_GLOBALS_MISPLACED')
class BadPrioTest(ALintTestCase):
    def test_invalid_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,0,NoOp(1)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 0)
        self.assertLinted({'E_DP_PRIO_INVALID': 1})

    def test_dupe_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
exten => pattern,2,NoOp(2)
exten => pattern,2,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 2)
        self.assertLinted({'E_DP_PRIO_DUPE': 1})

    def test_missing_prio_1(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,n,NoOp(1)
exten => pattern,n,NoOp(2)
exten => pattern,n,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 0)
        self.assertLinted({'E_DP_PRIO_MISSING': 3})

    def test_prio_bad_start(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,2,NoOp(1)
exten => pattern,n,NoOp(2)
exten => pattern,n,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 3)
        self.assertLinted({'W_DP_PRIO_BADORDER': 1})

    def test_prio_missing(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
exten => pattern,NoOp(2)
exten => pattern,n,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 2)
        self.assertLinted({'E_DP_PRIO_INVALID': 1})

    def test_prio_missing_app(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => pattern,1,NoOp(1)
exten => pattern,n
exten => pattern,n,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 3)
        self.assertLinted({'E_APP_MISSING': 1,
                           'W_APP_NEED_PARENS': 1})

    def test_prio_inconsistent_n(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => 10,1,NoOp(10a)
exten => 10,n,NoOp(10b)
exten => 20,1,NoOp(20a)
exten => 10,n,NoOp(20b) ; this does not become 10,2, but gets discarded
exten => 10,n,NoOp(20c) ; this becomes 10,3
exten => 10,n,NoOp(20d) ; this becomes 10,4
exten => 10,n,NoOp(20e) ; this becomes 10,5
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts), 1)
        self.assertEqual(
            [(i.pattern.raw, i.prio, i.app.raw)
             for i in dialplan.contexts[0].by_pattern()],
            [('10', 1, 'NoOp(10a)'),
             ('10', 2, 'NoOp(10b)'),
             ('10', 3, 'NoOp(20c)'),
             ('10', 4, 'NoOp(20d)'),
             ('10', 5, 'NoOp(20e)'),
             ('20', 1, 'NoOp(20a)')])
        self.assertLinted({
            # 20b (10,2) is dupe
            'E_DP_PRIO_DUPE': 1,
            # Both 20b and 20c get a BADORDER remark.
            'W_DP_PRIO_BADORDER': 2,
        })

    def test_prio_missing_1_in_context2(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => 10,1,NoOp(10a)
exten => 10,n,NoOp(10b)

[context2a]
exten => 10,n,NoOp(10c) ; gets eaten in Ast11, gets prio 3 in Ast1.4
exten => 20,50,NoOp(20a)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts), 2)
        self.assertEqual(
            [(i.pattern.raw, i.prio, i.app.raw)
             for i in dialplan.contexts[0].by_pattern()],
            [('10', 1, 'NoOp(10a)'),
             ('10', 2, 'NoOp(10b)')])
        self.assertEqual(
            [(i.pattern.raw, i.prio, i.app.raw)
             for i in dialplan.contexts[1].by_pattern()],
            # NOTE: Works in Asterisk 1.4 only, not in Asterisk 11.
            [('10', 3, 'NoOp(10c)'),  # cross-context next prio
             ('20', 50, 'NoOp(20a)')])
        self.assertLinted({
            # TODO: should 10,3 get a E_* error because this is invalid
            # in newer Asterisk?
            # - 10c (10,3) is missing a prio
            # - 20a (20,50) should not start at 50
            'W_DP_PRIO_BADORDER': 2,
        })


class UnusualButGoodPrioTest(ALintTestCase):
    @expectedFailure
    def test_valid_prio(self):
        reader = self.create_instance_and_load_single_file(
            FileDialplanParser, 'test.conf', b'''\
[context]
exten => _X!,1,NoOp(1)
exten => _[0-3]!,2,NoOp(2)
exten => _[4-9]!,2,NoOp(2)
exten => _X!,3,NoOp(3)
''')
        dialplan = [i for i in reader][0]
        self.assertEqual(len(dialplan.contexts[0]), 4)
        # Not(!) {'W_DP_PRIO_BADORDER': 3}
        self.assertLinted({})
