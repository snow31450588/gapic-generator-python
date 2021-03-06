# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The ``metadata`` module defines schema for where data was parsed from.
This library places every protocol buffer descriptor in a wrapper class
(see :mod:`~.wrappers`) before loading it into the :class:`~.API` object.

As we iterate over descriptors during the loading process, it is important
to know where they came from, because sometimes protocol buffer types are
referenced by fully-qualified string (e.g. ``method.input_type``), and we
want to resolve those references.

Additionally, protocol buffers stores data from the comments in the ``.proto``
in a separate structure, and this object model re-connects the comments
with the things they describe for easy access in templates.
"""

import dataclasses
from typing import Tuple

from google.protobuf import descriptor_pb2


@dataclasses.dataclass(frozen=True)
class Address:
    package: Tuple[str] = dataclasses.field(default_factory=tuple)
    module: str = ''
    parent: Tuple[str] = dataclasses.field(default_factory=tuple)

    def __str__(self):
        return '.'.join(tuple(self.package) + tuple(self.parent))

    def child(self, child_name: str) -> 'Address':
        """Return a new Address with ``child_name`` appended to its parent.

        Args:
            child_name (str): The child name to be appended to ``parent``.
                The period-separator is added automatically if ``parent``
                is non-empty.

        Returns:
            ~.Address: The new address object.
        """
        return type(self)(
            module=self.module,
            package=self.package,
            parent=self.parent + (child_name,),
        )

    def resolve(self, selector: str) -> str:
        """Resolve a potentially-relative protobuf selector.

        This takes a protobuf selector which may be fully-qualified
        (e.g. `foo.bar.v1.Baz`) or may be relative (`Baz`) and
        returns the fully-qualified version.

        This method is naive and does not check to see if the message
        actually exists.

        Args:
            selector (str): A protobuf selector, either fully-qualified
                or relative.

        Returns:
            str: An absolute selector.
        """
        if '.' not in selector:
            return f'{".".join(self.package)}.{selector}'
        return selector


@dataclasses.dataclass(frozen=True)
class Metadata:
    address: Address = dataclasses.field(default_factory=Address)
    documentation: descriptor_pb2.SourceCodeInfo.Location = dataclasses.field(
        default_factory=descriptor_pb2.SourceCodeInfo.Location,
    )

    @property
    def doc(self):
        """Return the best comment.

        This property prefers the leading comment if one is available,
        and falls back to a trailing comment or a detached comment otherwise.

        If there are no comments, return empty string. (This means a template
        is always guaranteed to get a string.)
        """
        if self.documentation.leading_comments:
            return self.documentation.leading_comments.strip()
        if self.documentation.trailing_comments:
            return self.documentation.trailing_comments.strip()
        if self.documentation.leading_detached_comments:
            return '\n\n'.join(self.documentation.leading_detached_comments)
        return ''
