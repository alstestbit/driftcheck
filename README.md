# driftcheck

Detects configuration drift between deployed infrastructure state and version-controlled YAML definitions.

---

## Installation

```bash
pip install driftcheck
```

Or install from source:

```bash
git clone https://github.com/yourorg/driftcheck.git && cd driftcheck && pip install .
```

---

## Usage

Point `driftcheck` at your live infrastructure state and your local YAML definitions to surface any drift:

```bash
driftcheck --state terraform.tfstate --definitions ./config/infra.yaml
```

Example output:

```
[DRIFT DETECTED] resource: aws_security_group.web
  expected: ingress.port = 80
  actual:   ingress.port = 8080

[OK] resource: aws_s3_bucket.assets
[OK] resource: aws_iam_role.deployer

Summary: 1 drift(s) found across 3 resource(s).
```

You can also run a check against a directory of YAML files:

```bash
driftcheck --state ./state/ --definitions ./definitions/ --output json
```

### Options

| Flag | Description |
|------|-------------|
| `--state` | Path to state file or directory |
| `--definitions` | Path to YAML definition file or directory |
| `--output` | Output format: `text` (default) or `json` |
| `--strict` | Exit with non-zero code if any drift is found |

---

## License

This project is licensed under the [MIT License](LICENSE).