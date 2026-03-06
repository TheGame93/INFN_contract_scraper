# Functions & Classes Database

> **Location:** `docs/info_functions.md`
> **See also:** [Desiderata](plan_desiderata.md) · [Implementation Plan](plan_implementation.md)

---

## Purpose

This file is a searchable index of every function and class in the codebase.
It is updated manually each time a function or class is added, modified, or removed.
Use it to find where logic lives without grepping the source.

## Update Policy

- Add an entry when a new function or class is created.
- Update the entry when signature, inputs, outputs, or description change.
- Remove the entry when the function or class is deleted.
- Keep entries sorted by file path, then by order of appearance in the file.

## Entry Format

Each entry uses the following fields:

| Field | Description |
|---|---|
| **File** | Relative path from repo root (e.g. `src/infn_jobs/fetch/listing/parser.py`) |
| **Name** | Function or class name |
| **Parent** | Enclosing class, function, or `module` if top-level |
| **Inputs** | Parameter names and types |
| **Output** | Return type and brief description of what is returned |
| **Description** | One-line docstring summary |

---

## Index

<!-- Entries will be added here as code is written. -->
<!-- Format each entry as shown in the template below. -->

<!--
### `function_or_class_name`
| Field | Value |
|---|---|
| **File** | `src/infn_jobs/...` |
| **Name** | `name` |
| **Parent** | `ClassName` / `module` |
| **Inputs** | `param1: type`, `param2: type` |
| **Output** | `type` — description |
| **Description** | One-line summary. |
-->
