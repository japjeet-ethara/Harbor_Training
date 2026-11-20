# Source and data notices

The original Python source snapshot in `environment/repo` and the titlecase
behavior ported by this task come from Patrick William Pannuto's
`python-titlecase`, commit `42f43e2de55bf003b286c6f8e8d8b2d26676a167`.
The upstream MIT notice is preserved in `environment/repo/LICENSE.txt` and the
root `LICENSE.txt`. The solved candidate retains that notice.

`solution/unicode_tables.go` is generated from character-property and
case-conversion queries to CPython 3.12, whose Unicode database is 15.0.0.
It contains character data, not benchmark answers. The Unicode copyright and
permission notice is included in `solution/UNICODE-LICENSE.txt`; `solve.sh`
also places it in the solved candidate repository.

Sources:

- https://github.com/ppannuto/python-titlecase/tree/42f43e2de55bf003b286c6f8e8d8b2d26676a167
- https://docs.python.org/3.12/library/unicodedata.html
- https://www.unicode.org/license.txt

Harbor, RewardKit, Go and the container base images are installed/downloaded
from their respective distributions. Their binaries are not bundled in this
source archive.
