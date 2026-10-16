#!/usr/bin/env python3
"""Validate the release contract and the chart that Helm actually packages."""
import pathlib
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHART = ROOT / "charts/swytch-operator"
metadata = yaml.safe_load((CHART / "Chart.yaml").read_text())
values = yaml.safe_load((CHART / "values.yaml").read_text())
version = metadata["version"]
app_version = metadata["appVersion"]


def require(condition, message):
    if not condition:
        raise SystemExit(message)


require(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version), "Invalid chart SemVer")
if len(sys.argv) > 1:
    require(sys.argv[1] == f"v{version}", "Release tag must equal v<Chart.yaml version>")
require(values["image"]["tag"] == app_version, "Operator tag must match appVersion")
require(values["swytch"]["image"] == f"ghcr.io/swytchdb/swytch:{app_version}",
        "Default Swytch image must match appVersion")
require(app_version != "latest", "Pin released images")
for field in ("home", "icon", "sources", "maintainers", "keywords", "kubeVersion"):
    require(metadata.get(field), f"Missing chart metadata: {field}")
require((ROOT / "assets/swytch.png").is_file(), "Missing logo")

subprocess.run(["helm", "lint", str(CHART), "--strict", "--kube-version", "1.33.0"], check=True)
with tempfile.TemporaryDirectory() as destination:
    subprocess.run(["helm", "package", str(CHART), "--destination", destination], check=True)
    package = pathlib.Path(destination) / f"swytch-operator-{version}.tgz"
    rendered = subprocess.check_output([
        "helm", "template", "test", str(package), "--namespace", "operators",
        "--kube-version", "1.33.0", "--include-crds",
        "--set", "swytch.imagePullSecrets[0]=registry", "--set", "nodeSelector.pool=infra",
    ], text=True)
    objects = [obj for obj in yaml.safe_load_all(rendered) if obj]
    for kind in ("CustomResourceDefinition", "Deployment", "Service", "Secret",
                 "MutatingWebhookConfiguration", "ClusterRole", "ClusterRoleBinding",
                 "Role", "RoleBinding", "ServiceAccount"):
        require(sum(obj["kind"] == kind for obj in objects) == 1, f"Expected one {kind}")
    deployment = next(obj for obj in objects if obj["kind"] == "Deployment")
    pod = deployment["spec"]["template"]["spec"]
    container = pod["containers"][0]
    require(container["image"] == f'{values["image"]["repository"]}:{app_version}',
            "Packaged operator image differs from release metadata")
    require(f'--swytch-image={values["swytch"]["image"]}' in container["args"],
            "Packaged chart does not pass the workload image")
    require("--swytch-image-pull-secrets=registry" in container["args"], "Missing pull secrets")
    require(pod["nodeSelector"] == {"pool": "infra"}, "Missing scheduling override")
    require("requests" not in container["resources"], "Unexpected default requests")
print(f"Chart {version} validated against Swytch {app_version}")
