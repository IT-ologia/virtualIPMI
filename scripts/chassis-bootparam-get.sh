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
param="$2"  # Only 5 (bootdev) available in the current implementation

if [ "$param" == "5" ]; then
	# device=pxe
	# device=cdrom
	device=disk

	# echo "$host: chassis bootparam get=$param" >&2

	echo "$device"  # Report the value
	exit 0  # Everything is fine
else
	# Any text in stderr will be reflected in the log
	echo "$host: chassis bootparam get=$param: Unsupported param" >&2
	exit 1  # Report an error
fi
