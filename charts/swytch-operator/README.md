# Swytch operator

Inject native Redis sidecars or reconcile server Deployments from namespaced
`Swytch` resources. Requires Kubernetes 1.33+; install one operator per cluster.

```sh
helm install swytch oci://ghcr.io/swytchdb/charts/swytch-operator \
  --version 1.6.1 --namespace swytch-system --create-namespace --wait
```

| Value                             | Default                            | Purpose                                                        |
|-----------------------------------|------------------------------------|----------------------------------------------------------------|
| `replicaCount`                    | `1`                                | Operator replicas; leader election is enabled.                 |
| `image.repository`                | `ghcr.io/swytchdb/swytch-operator` | Operator image repository.                                     |
| `image.tag`                       | `1.6.1`                            | Operator image tag.                                            |
| `image.pullPolicy`                | `IfNotPresent`                     | Operator image pull policy.                                    |
| `imagePullSecrets`                | `[]`                               | Operator registry Secrets as `{name: ...}` objects.            |
| `swytch.image`                    | `ghcr.io/swytchdb/swytch:1.6.1`    | Default image for generated workloads.                         |
| `swytch.imagePullSecrets`         | `[]`                               | Secret names; must exist in each workload namespace.           |
| `resources`                       | Memory limit `128Mi`               | Operator resources; requests are omitted.                      |
| `nodeSelector` / `affinity`       | `{}`                               | Operator scheduling constraints.                               |
| `tolerations`                     | `[]`                               | Operator tolerations.                                          |
| `webhook.certificateRevision`     | `"1"`                              | Change to renew the serving certificate and roll the operator. |
| `webhook.certificateDurationDays` | `365`                              | Serving-certificate lifetime when generated or renewed.        |

Helm installs the CRD only on initial installation. Apply the target chart's CRD
before upgrading. Certificate renewal is manual and requires live Helm lookup.
The operator watches every namespace; the webhook fails closed for annotated Pod
creates. Installing this chart does not create cache profiles or credentials.

See [installation and upgrade procedures](https://github.com/swytchdb/swytch-helm),
[the quickstart](https://docs.getswytch.com/start/kubernetes/), and
[operator configuration](https://github.com/swytchdb/swytch/tree/main/operator).
