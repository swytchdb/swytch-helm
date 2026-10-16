# Swytch Helm charts

Helm charts for [Swytch](https://github.com/swytchdb/swytch), a Redis-compatible
distributed cache. Operator code stays in the Swytch repository. This repository
owns the chart, its CRD manifest, packaging, and chart releases.

| Chart | Chart version | Operator / default Swytch version | Kubernetes |
| --- | --- | --- | --- |
| [swytch-operator](charts/swytch-operator) | 1.5.2 | 1.5.2 | 1.33+ |

## Install from OCI

```sh
helm install swytch oci://ghcr.io/swytchdb/charts/swytch-operator \
  --version 1.5.2 --namespace swytch-system --create-namespace --wait
```

Helm 3.8+ supports OCI without an experimental flag. No `helm repo add` is needed.
The OCI package must be public for anonymous installation. Install one operator
per cluster. cert-manager is not required.

The chart installs the operator, CRD, RBAC, and admission webhook. Create a Secret
and a namespaced `Swytch` profile to run a cache; for sidecars, annotate the
application's Pod template. Follow the
[Kubernetes quickstart](https://docs.getswytch.com/start/kubernetes/).

## Upgrade

Review release notes and your existing values before upgrading. Helm does not
upgrade CRDs from `crds/`. Fetch the exact target chart and apply its CRD first:

```sh
chart_version=1.5.2
chart_dir="$(mktemp -d)"
helm pull oci://ghcr.io/swytchdb/charts/swytch-operator \
  --version "$chart_version" --untar --untardir "$chart_dir"
kubectl apply -f "$chart_dir/swytch-operator/crds/"
helm upgrade swytch "$chart_dir/swytch-operator" \
  --namespace swytch-system --reuse-values \
  --set-string image.tag=1.5.2 \
  --set-string swytch.image=ghcr.io/swytchdb/swytch:1.5.2 --wait
```

`--reuse-values` retains old values, including image pins. The explicit image
settings above select the intended release; preserve your own registry overrides
when using mirrors. A profile's `spec.image` takes precedence over `swytch.image`.
Sidecar and Secret changes require application Pod recreation. Plan the data
recovery path before restarting workloads; this operator creates no PVCs.

To migrate from the chart formerly in `swytchdb/swytch`, use your existing release
name and namespace in these commands. Do not install a second operator. The CRD
is unchanged in this initial chart release.

## Certificates and removal

The chart creates a ten-year CA and a one-year serving certificate. Ordinary
upgrades preserve both. Before the serving certificate expires, renew it using
the **currently installed chart version**:

```sh
helm upgrade swytch oci://ghcr.io/swytchdb/charts/swytch-operator \
  --version 1.5.2 --namespace swytch-system --reuse-values \
  --set-string webhook.certificateRevision=2 --wait
```

Use a new revision value for every renewal. Do not delete the TLS Secret or
repeatedly apply offline `helm template` output: certificate reuse requires live
Helm `lookup`. Plan CA replacement before its expiry. The webhook fails closed
for annotated Pod creates when injection is unavailable.

Before uninstalling, remove profile annotations and roll affected applications;
delete server profiles only when their workloads and data can be removed. Helm
leaves the CRD and custom resources behind. Deleting the CRD deletes all profiles.
See the [operator lifecycle documentation](https://docs.getswytch.com/kubernetes/operations/).

## Kubermatic

Use Helm source URL `oci://ghcr.io/swytchdb/charts`, chart name `swytch-operator`,
and an explicit chart version in the ApplicationDefinition. Keep old version
entries: deleting one can remove installations that reference it.

Update values, including certificate revisions, through ApplicationInstallation
when KKP manages the release. CRD upgrades still need an explicit administrator
step. KKP compatibility is not yet certified: validate unchanged reconciliation
and certificate reuse, as KKP's Helm comparison may render with a different
release name from the installation.

## Development

```sh
python3 -m pip install 'PyYAML>=6,<7'
python3 scripts/check-chart.py
bash tests/smoke.sh
```

The smoke test requires Docker, kind, Helm, and kubectl. It creates a disposable
kind cluster and its own kubeconfig, tests the published images, sidecar/server
access, native-sidecar Job completion, and certificate reuse/rotation, then
deletes the cluster. `KIND_NODE_IMAGE` selects the Kubernetes test image.

For operator development, set `SWYTCH_HELM_CHART` to the absolute path of
`charts/swytch-operator` when running the tests in `swytchdb/swytch/operator`.
Changes to the Go API and CRD schema need coordinated PRs across both repositories.

## Releases

1. Publish and validate the intended operator and Swytch images in `swytchdb/swytch`.
2. Update chart `version`, `appVersion`, image defaults, this README, and the changelog.
   Chart versions are independent: a chart-only patch can retain the same appVersion
   and image versions. Never change an existing version's contents.
3. Run chart checks and Kubernetes smoke tests; commit the changes.
4. Create an annotated `v<chart-version>` tag and push `main` and that tag.
   The release workflow checks the tag against Chart.yaml, tests the chart, pushes
   the OCI package, and verifies the downloaded package matches the uploaded one.
5. On first publication, make the GHCR chart package public and verify an anonymous
   `helm pull`. Keep the repository linked to the package for Actions write access.
6. Update the pinned chart ref in Swytch's operator CI and append the version in
   the Kubermatic application definition. Publishing a chart does not upgrade clusters.

The initial release tag is `v1.5.2`. Push the new chart repository and publish this
tag before merging the Swytch CI migration or deploying documentation that uses
the new OCI URL. No Helm registry credentials belong in this repository: publishing
uses the repository's `GITHUB_TOKEN` with `packages: write`.

## License and history

AGPL-3.0-or-later, preserving the license of the original Swytch chart. See
[LICENSE](LICENSE). The icon is the existing Swytch logo from its documentation.

History was extracted from `swytchdb/swytch` at
`2e9e7ba` using `git subtree split --prefix=operator/charts`, producing split
commit `c5eb9fdad3bc17ef4daef325731137197812e9a1`. The first migration commit
relocates the extracted chart into `charts/` and adds release infrastructure.
