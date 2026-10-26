# Changelog

## 1.6.0
- Enable SSI mode for Swytch 1.6.0

## 1.5.2

- Move the chart from `swytchdb/swytch` into its own repository, preserving its
  history with `git subtree split --prefix=operator/charts`.
- Pin the operator and Swytch images to the published `1.5.2` release.
- Add chart metadata, the Swytch icon, and an OCI publishing workflow.
- Validate packaging, image availability, and Kubernetes installation before publishing.

The initial chart version matches Swytch 1.5.2. The chart API and workload behavior
are unchanged from the original chart. Existing releases can upgrade in place
using the same Helm release name and namespace.
