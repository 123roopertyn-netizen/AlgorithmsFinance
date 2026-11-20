"""All implemented versions. Tests and benchmarks iterate over this registry,
so a new version only has to be added here."""

import search_v1

VERSIONS = {
    "v1": search_v1.METHODS,
}
