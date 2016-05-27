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
from ..base import (
    AppBase, DelimitedArgsMixin, MinMaxArgsMixin, NoPipeDelimiterMixin,
    VarCondIfStyleApp)


class Gosub(NoPipeDelimiterMixin, MinMaxArgsMixin, DelimitedArgsMixin,
            AppBase):
    def __init__(self, **kwargs):
        super().__init__(min_args=1, max_args=3, **kwargs)

    def __call__(self, data, where, jump_destinations):
        args = super().__call__(data, where, jump_destinations)

        jumpdest = args[:]
        while len(jumpdest) != 3:
            jumpdest.insert(0, None)
        assert len(jumpdest) == 3
        jump_destinations.append(tuple(jumpdest))

        return args


class GosubIf(VarCondIfStyleApp):
    def __call__(self, data, where, jump_destinations):
        cond, iftrue, iffalse = super().__call__(
            data, where, jump_destinations)

        for args in (iftrue, iffalse):
            if args:
                jumpdest = self.separate_args(args)
                while len(jumpdest) != 3:
                    jumpdest.insert(0, None)
                assert len(jumpdest) == 3
                jump_destinations.append(tuple(jumpdest))

        return cond, iftrue, iffalse


class Return(AppBase):
    pass


class StackPop(AppBase):
    pass


def register(app_loader):
    for app in (
            Gosub, GosubIf, Return, StackPop):
        app_loader.register(app())
