# Line-Oriented JSON Metadata Carrier Format, Version 1

## 1. Scope

This specification defines a minimal, line-oriented format for attaching machine-readable metadata to files and streams.

The specification does **not** define a data model, data layout, physical units, application semantics, or required metadata vocabulary. It defines only a stable carrier format for metadata records.

Application-specific record types may be defined by separate profiles, project conventions, or consuming applications.

The goals of this format are:

1. to allow metadata records to be embedded safely in files whose legacy parsers ignore `#` comment lines;
2. to allow the same metadata records to be transmitted directly in line-oriented JSON streams;
3. to require standard JSON parsing rather than ad hoc parsing;
4. to permit future metadata extensions without breaking older tools.

This document defines version 1 of the carrier format.

---

## 2. Metadata Records

A **metadata record** is a single JSON object encoded on one physical line.

A metadata record MUST contain a field named `type`.

The value of `type` MUST be a string.

Example:

```json
{"type": "title", "value": "Experiment 42"}
```

Parsers MUST use a conforming JSON parser to parse metadata records. Implementations MUST NOT rely on ad hoc parsing of JSON syntax.

This specification assigns no universal meaning to record types other than the required presence of the string-valued `type` field. The interpretation of particular `type` values is application-defined, profile-defined, or convention-defined.

For example, this core specification does not define the semantics of the following records:

```json
{"type": "created", "value": "2026-01-26T18:44:00Z"}
{"type": "node", "index": 1, "name": "CTRL_1"}
{"type": "temperature", "value": 0.25}
```

These may be meaningful to particular applications, but they are not required by the carrier format itself.

---

## 3. File-Embedded Encoding

In files that permit comment lines beginning with `#`, a metadata record MAY be embedded in a comment line.

The canonical file-embedded form is:

```text
#@ JSON_OBJECT
```

The metadata introducer is the two-character sequence `#@` followed by at least one whitespace character.

The canonical spelling uses exactly one ASCII space after `#@`:

```text
#@ {"type": "title", "value": "Experiment 42"}
```

The JSON object begins after the metadata introducer and any additional whitespace.

A line whose first relevant content begins with `#` but does not contain the version-1 metadata introducer `#@ ` is not a version-1 metadata record.

In particular, the following lines are not version-1 metadata records:

```text
#@{"type": "title", "value": "Missing required whitespace"}
#@1 this is not a version-1 metadata record
# This is an ordinary comment
```

Producers SHOULD emit metadata records beginning at the first column of the line.

Parsers MAY accept leading whitespace before the introducer, but producers SHOULD NOT emit such whitespace unless required by a surrounding file format.

For example, producers should prefer:

```text
#@ {"type": "title", "value": "Experiment 42"}
```

over:

```text
    #@ {"type": "title", "value": "Experiment 42"}
```

Trailing whitespace after the JSON object is permitted.

A file-embedded metadata record MUST be contained on a single physical line. Multi-line JSON objects are not valid file-embedded metadata records in this format.

Ordinary comment lines remain ordinary comments. A parser implementing this format SHOULD ignore comment lines that do not contain the version-1 metadata introducer.

Example:

```text
# Ordinary comment for humans.
#@ {"type": "title", "value": "Experiment 42"}
#@ {"type": "created", "value": "2026-01-26T18:44:00Z"}

0.000  1 0.12  -1 0.44
0.100  1 0.15  -1 0.43
```

In this example, only the two lines beginning with the valid `#@ ` introducer are metadata records. The numeric data lines are outside the scope of this carrier specification.

---

## 4. Stream Encoding

In stream contexts, metadata records are transmitted directly as newline-delimited JSON objects.

The file introducer `#@ ` MUST NOT be used in stream encoding.

Each stream line MUST contain exactly one JSON object.

Example:

```json
{"type": "title", "value": "Experiment 42"}
{"type": "created", "value": "2026-01-26T18:44:00Z"}
{"type": "notes", "value": "Preliminary test run."}
```

The stream encoding is suitable for NDJSON-style processing. Each line is parsed independently as a JSON object.

This specification does not require that a stream contain only metadata records. Applications may define streams that also include data samples, control messages, acknowledgments, or other objects. Such objects are outside the scope of this core carrier specification unless they are also used as metadata records with a string-valued `type` field.

---

## 5. Parser Modes

Parsers MAY operate in one of three modes:

1. permissive mode;
2. diagnostic mode;
3. strict mode.

Permissive mode is the default.

### 5.1 Permissive Mode

In permissive mode, a parser SHOULD ignore ordinary comments, unknown record types, unknown fields, and records that are not relevant to the consuming application.

A permissive parser MUST NOT fail merely because it encounters a well-formed metadata record with an unknown `type`.

If a line uses the version-1 metadata introducer but the following content is not a valid JSON object, a permissive parser SHOULD ignore the record and continue.

If a JSON object lacks a string-valued `type` field, a permissive parser SHOULD ignore the record and continue.

Permissive mode is intended for ordinary data processing, where the presence of additional metadata should not break existing workflows.

### 5.2 Diagnostic Mode

Diagnostic mode behaves like permissive mode, but the parser SHOULD report diagnostics when useful to the caller.

Diagnostic messages may be reported for, among other things:

- malformed JSON after a metadata introducer;
- JSON values that are not objects;
- missing `type` fields;
- non-string `type` fields;
- unknown record types;
- ignored fields;
- records that are syntactically valid but not meaningful to the consuming application.

Diagnostic mode is intended for validation, debugging, migration, and development of new metadata-producing tools.

A diagnostic parser SHOULD continue processing after recoverable problems unless configured otherwise.

### 5.3 Strict Mode

Strict mode is intended for applications that require a specific profile, vocabulary, or validation policy.

A strict parser MUST report an error when a version-1 metadata record is malformed, is not a JSON object, lacks a `type` field, or has a non-string `type` field.

A strict parser MAY also report an error for unknown record types, unknown fields, missing required application fields, invalid field values, or other violations, but only relative to a selected application profile or validation policy.

This core specification does not define a universal list of valid `type` values. Therefore, unknown `type` values are not intrinsically errors under the core carrier format alone.

---

## 6. Versioning and Extension Rules

This document defines version 1 of the metadata carrier format.

Version 1 reserves only the following core features:

1. the file-embedded metadata introducer `#@ `, meaning `#@` followed by whitespace;
2. the representation of each metadata record as a single JSON object;
3. the required string-valued `type` field;
4. the permissive default behavior for parsers.

Future versions of this carrier format SHOULD preserve the interpretation of valid version-1 metadata records whenever practical.

Applications and profiles MAY define their own version declarations as ordinary metadata records.

Example:

```json
{"type": "profile", "name": "relaxed-spin", "version": "1.0"}
```

or, in file-embedded form:

```text
#@ {"type": "profile", "name": "relaxed-spin", "version": "1.0"}
```

A parser that does not recognize a profile declaration MUST treat it like any other unknown metadata record in permissive mode.

Applications MAY define additional record types and fields. Such extensions MUST be encoded as valid JSON objects and MUST include a string-valued `type` field if they are to be treated as metadata records under this carrier format.

Unknown record types and unknown fields SHOULD NOT prevent older permissive parsers from continuing to process files or streams.

---

# Appendix A. Non-Normative Conventions and Examples

This appendix is non-normative.

The records shown here are examples and suggested conventions. They are not required by the core carrier format. A parser may fully conform to the core format without recognizing any of these record types.

Applications, projects, and lab groups may adopt some, all, or none of these conventions.

---

## A.1 Common Descriptive Metadata

The following records are broadly useful for human-readable description and basic provenance.

### Title

```json
{"type": "title", "value": "Trajectory for test run 42"}
```

Suggested meaning: a short human-readable title for the associated file, stream, run, experiment, or dataset.

Suggested fields:

- `type`: `"title"`
- `value`: string

### Created Timestamp

```json
{"type": "created", "value": "2026-01-26T18:44:00Z"}
```

Suggested meaning: time at which the file, stream, run, or metadata package was created.

Suggested fields:

- `type`: `"created"`
- `value`: string timestamp

When this convention is used, `value` should preferably be an RFC 3339 / ISO 8601 timestamp. UTC timestamps with a trailing `Z` are encouraged when appropriate.

### Notes

```json
{"type": "notes", "value": "Simulation after thermal relaxation."}
```

Suggested meaning: free-form human-readable notes.

Suggested fields:

- `type`: `"notes"`
- `value`: string

This field is intended for human interpretation. Applications should not rely on parsing the contents of `notes`.

---

## A.2 Profile Declaration Convention

Applications may use a profile declaration to state that subsequent or associated metadata records follow a particular application-defined convention.

Example:

```json
{"type": "profile", "name": "relaxed-spin", "version": "1.0"}
```

Suggested fields:

- `type`: `"profile"`
- `name`: string identifying the profile
- `version`: string or number identifying the profile version

A profile declaration does not change the core carrier format. It only provides information to tools that understand the named profile.

A permissive parser that does not recognize the profile should ignore the record and continue.

File-embedded example:

```text
#@ {"type": "profile", "name": "relaxed-spin", "version": "1.0"}
```

Stream example:

```json
{"type": "profile", "name": "relaxed-spin", "version": "1.0"}
```

---

## A.3 Example: Basic File Header

The following example shows a metadata header embedded in a file that also contains application-specific data lines.

The data lines are outside the scope of the carrier format.

```text
# Human-readable comment.
#@ {"type": "title", "value": "Trajectory for test run 42"}
#@ {"type": "created", "value": "2026-01-26T18:44:00Z"}
#@ {"type": "notes", "value": "Simulation after thermal relaxation."}

0.000  1 0.12  -1 0.44  1 0.91
0.100  1 0.15  -1 0.43  1 0.88
```

A parser implementing only the core carrier format can identify and parse the three metadata records. It does not need to understand the data lines.

A legacy parser that ignores `#` comment lines should ignore both the human-readable comment and the metadata records.

---

## A.4 Example: Stream Metadata

The same metadata records can be transmitted directly as newline-delimited JSON objects:

```json
{"type": "title", "value": "Trajectory for test run 42"}
{"type": "created", "value": "2026-01-26T18:44:00Z"}
{"type": "notes", "value": "Simulation after thermal relaxation."}
```

The `#@ ` introducer is not used in stream encoding.

---

## A.5 Example: Application-Specific Node Metadata

The following records illustrate an application-specific convention for assigning names to logical nodes.

These records are not part of the core carrier format.

```json
{"type": "node_indexing", "base": 1}
{"type": "node", "index": 1, "name": "CTRL_1"}
{"type": "node", "index": 5, "name": "pass_a"}
```

Possible application-defined interpretation:

- `node_indexing` declares whether node indices are counted from `0` or `1`;
- `node` assigns metadata to a logical node;
- `index` identifies the logical node;
- `name` provides a human-readable or application-readable node name.

A particular application profile may impose additional rules, such as:

- allowed values for `base`;
- whether `node_indexing` is required;
- whether `node_indexing` may appear more than once;
- whether node names must be unique;
- whether later records override earlier records;
- how strict parsers should treat missing or conflicting node metadata.

Those rules are intentionally not defined by the core carrier format.

File-embedded example:

```text
#@ {"type": "profile", "name": "relaxed-spin", "version": "1.0"}
#@ {"type": "node_indexing", "base": 1}
#@ {"type": "node", "index": 1, "name": "CTRL_1"}
#@ {"type": "node", "index": 5, "name": "pass_a"}

0.000  1 0.12  -1 0.44  1 0.91
0.100  1 0.15  -1 0.43  1 0.88
```

Again, the numeric data lines are application-specific and are not defined by this carrier specification.

---

## A.6 Example: Extended Application Metadata

Applications may define richer metadata records as needed.

Example:

```json
{"type": "run_parameter", "name": "temperature", "value": 0.25}
{"type": "run_parameter", "name": "seed", "value": 12345}
{"type": "source", "program": "simulate-relaxation", "version": "2.3.1"}
```

These records remain compatible with the carrier format because each is a single JSON object with a string-valued `type` field.

A parser that does not understand `run_parameter` or `source` should ignore these records in permissive mode.

---

## A.7 Design Note

The carrier format should be understood as an envelope, not as the contents of the envelope.

The core format defines how to carry metadata records:

```text
#@ {"type": "..."}
```

It does not define what every possible `type` means.

That separation is intentional. It allows different research projects, applications, and data formats to share the same metadata-carrying mechanism without prematurely imposing a universal data model.
