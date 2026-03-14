# Contract Canary Matrix

Step 1 canary fixtures lock one stable parse case per contract family (active/expired where available).
These fixtures are parser canaries for later refactor steps.

## Coverage Matrix

| Contract family | detail_id(s) | Listing tipo/status snapshot | Expected extracted contract type |
|---|---|---|---|
| Borsa di studio | `4507`, `4476` | `Borsa/active`, `Borsa/expired` | `Borsa di studio` |
| Incarico di ricerca | `4490`, `4493` | `Incarico di ricerca/active`, `Incarico di ricerca/active` | `Incarico di ricerca` |
| Incarico Post-Doc | `4484` | `Incarico Post-Doc/expired` | `Incarico Post-Doc` |
| Contratto di ricerca | `4456`, `4358` | `Contratto di ricerca/expired`, `Assegno di ricerca/expired` | `Contratto di ricerca` |
| Assegno di ricerca | `4223`, `4302` | `Assegno di ricerca/expired`, `Assegno di ricerca/expired` | `Assegno di ricerca` |

## Notes

- No active canary is currently available for `Incarico Post-Doc`, `Contratto di ricerca`, and `Assegno di ricerca`.
- `detail_id=4358` is a deliberate mismatch case: listing metadata says `Assegno di ricerca` but PDF semantics must parse as `Contratto di ricerca`.
- The matrix locks parser outputs from committed text fixtures, not live site behavior.
