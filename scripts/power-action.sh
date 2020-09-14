#!/bin/sh

# Copyright (C) 2020 IT-ologia
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

host="$1"
action="$2"  # Available: on|off|reset|soft|diag|cycle

# Any text in stderr will be reflected in the log
# echo "$host: power $action" >&2

# To indicate an error use "exit 1"
exit 0
