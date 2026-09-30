# One validated boundary for mesh skinning

Status: Accepted

## Context

Native Dem Bones expects frame-major matrix blocks and uses polygon adjacency
to initialize bone regions. Older wrappers pack poses differently, retain stale
state, and export only the first bone. A correct import flag or successful
package build does not demonstrate reconstructed motion.

## Decision

The portable API and the generic DCC interface share input validation, native
configuration and complete result extraction. Hosts own sampling and writing
their scene data. Inputs contain at least three vertices and nonzero extent; multi-bone solves
require polygon connectivity. Validation happens before native mutation.

Each solve clears native data, locks and caches while preserving scalar solver
options. Coordinate conversion accepts orthogonal axes and uniform units, using
normalized validation so the decision does not depend on unit magnitude.
The wrapper owns mesh configuration and result state; the DCC interface calls
its public methods and owns coordinate conversion. Changing coordinates after
import invalidates that import until the caller supplies host arrays again.
Output contains every frame and bone. Native regression tests verify numerical
reconstruction, including independently moving components and solver reuse.

## Consequences

Callers must supply topology for multi-bone requests and resupply it on reuse.
Warm starts remain available through the low-level native API, which has a
different stateful contract. Shared internal helpers keep legacy and portable
layouts aligned without exposing another public solver abstraction. Older
host example classes need a separate migration and do not establish live host
acceptance. The Maya acceptance script is opt-in because normal CI has no Maya.

## Alternatives

Inferring adjacency from positions would introduce an additional algorithm and
could connect unrelated mesh regions. Accepting missing topology silently loses
multi-bone motion. Retaining prior native state makes output depend on earlier
calls and mesh sizes. These options do not satisfy the documented contract.
