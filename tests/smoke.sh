#!/usr/bin/env bash
# Creates and deletes only its own cluster; never uses the current kubeconfig.
set -euo pipefail
cd "$(dirname "$0")/.."
chart="$PWD/charts/swytch-operator"
cluster="swytch-chart-${RANDOM}"
test_dir="$(mktemp -d)"
export KUBECONFIG="$test_dir/kubeconfig"
cleanup() {
  result=$?
  if [ "$result" -ne 0 ]; then
    kubectl get pods -A -o wide || true
    kubectl get events -A --sort-by=.lastTimestamp || true
    kubectl logs -n swytch-system deployment/test-swytch-operator || true
  fi
  kind delete cluster --name "$cluster" || true
  rm -rf "$test_dir"
  exit "$result"
}
trap cleanup EXIT
kind create cluster --name "$cluster" --image "${KIND_NODE_IMAGE:-kindest/node:v1.33.1}" \
  --kubeconfig "$KUBECONFIG" --wait 120s
helm package "$chart" --destination "$test_dir"
packages=("$test_dir"/*.tgz)
chart="${packages[0]}"
helm install test "$chart" --namespace swytch-system --create-namespace --wait --timeout 180s
kubectl create secret generic swytch-secret --from-literal=cluster-passphrase=chart-test-only-passphrase
kubectl apply -f tests/fixtures/
kubectl rollout status deployment/example-app --timeout=180s
kubectl rollout status deployment/swytch-shared-cache --timeout=180s
test "$(kubectl exec deployment/example-app -c app -- redis-cli PING)" = PONG
test "$(kubectl exec deployment/example-app -c app -- redis-cli -h swytch-shared-cache PING)" = PONG
kubectl wait --for=condition=complete job/unix-client --timeout=180s
cert_before=$(kubectl -n swytch-system get secret test-swytch-operator-tls -o jsonpath='{.data.tls\.crt}')
ca_before=$(kubectl -n swytch-system get secret test-swytch-operator-tls -o jsonpath='{.data.ca\.crt}')
helm upgrade test "$chart" --namespace swytch-system --reuse-values --wait --timeout 120s
test "$cert_before" = "$(kubectl -n swytch-system get secret test-swytch-operator-tls -o jsonpath='{.data.tls\.crt}')"
helm upgrade test "$chart" --namespace swytch-system --reuse-values \
  --set-string webhook.certificateRevision=2 --wait --timeout 120s
test "$cert_before" != "$(kubectl -n swytch-system get secret test-swytch-operator-tls -o jsonpath='{.data.tls\.crt}')"
test "$ca_before" = "$(kubectl -n swytch-system get secret test-swytch-operator-tls -o jsonpath='{.data.ca\.crt}')"
kubectl rollout restart deployment/example-app
kubectl rollout status deployment/example-app --timeout=180s
test "$(kubectl exec deployment/example-app -c app -- redis-cli PING)" = PONG
echo 'Chart installation and certificate checks passed.'
