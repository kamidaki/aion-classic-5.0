# Auditoria de alcance das Skills — Classic 5.0

Foram comparados **12114 IDs oficiais** com **12139 templates**.
As variantes `special`/`special2` possuem **0 divergências de alcance** contra a base.
A sincronização corrigiu **8349 Skills**.

| Atributo do servidor | Correções | Fonte oficial |
|---|---:|---|
| `awr` | 51 | `add_wpn_range` |
| `direction` | 3 | `target_range_area_type + opt4` |
| `effective_altitude` | 163 | `target_range_area_type + opt3` |
| `effective_angle` | 54 | `target_range_area_type + opt2` |
| `effective_dist` | 11 | `target_range_area_type + opt1/opt2` |
| `effective_range` | 180 | `target_range_area_type + opt1` |
| `first_target` | 897 | `first_target` |
| `first_target_range` | 7718 | `first_target_valid_distance` |
| `revision_distance` | 447 | `revision_distance` |
| `target_distance` | 485 | `target_range_opt1` |
| `target_type` | 1515 | `target_range` |

A flag `add_wpn_range` significa soma: alcance-base oficial + alcance atual da arma. O contorno legado que substituía alcances maiores pelo alcance da arma reduzia, por exemplo, 15 m para aproximadamente 2 m.

Restaram **0 Skills** cuja forma de área não concorda com o `target_type`; elas ficam enumeradas no JSON sem conversão inferida.
