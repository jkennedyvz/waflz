#!/bin/bash
# ----------------------------------------------------------------------------
# Copyright (C) 2014 Verizon.  All Rights Reserved.
# All Rights Reserved
#
#   Author: Reed P Morrison
#   Date:   02/07/2014
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# To build...
# ------------------------------------------------------------------------------
which cmake || {
    echo "Failed to find all required apps to build (cmake)."
    exit 1
}
# This is necessary in scenarios where the URL of the remote for a given submodule has changed.
git submodule sync || {
    echo "FAILED TO SYNC IS2 LIB"
    exit 1
}
git submodule update -f --init || {
    echo "FAILED TO UPDATE TO LATEST IS2 LIB"
    exit 1
}
mkdir -p build
pushd build && \
    cmake ../ \
    -DBUILD_APPS=ON \
    -DBUILD_TESTS=OFF && \
    make 
	popd && \
exit $?
