# Experiment 3 — Kubernetes

Student: Raj Tripathi · Roll 16014223062 · Batch B1 AIDS · Prof. Sagar Korde · Use case KJS-AGR-01

## Verification status

| Step | Status |
|---|---|
| Manifests written (`k8s/`) | Done — parsed and structurally checked by `tests/test_deployment_files.py` |
| Deploy, access, scale, recover | **Not executed** — no `kubectl` or local cluster is available on this machine |

No pod, service or scaling output is included because none was produced.

## Manifests

| File | Purpose |
|---|---|
| `namespace.yaml` | `canesense` namespace |
| `configmap.yaml` | `CANESENSE_SEED` (optional `CANESENSE_CLOUD_URL`) |
| `deployment.yaml` | 2 replicas, rolling update (maxUnavailable 0), non-root, readiness + liveness probes on `/_stcore/health`, requests 250m CPU / 512Mi, limits 1 CPU / 1Gi |
| `service.yaml` | ClusterIP 80 → 8501 |
| `hpa.yaml` | Optional autoscaler 2–5 pods at 70% CPU (needs metrics-server) |

The resource figures come from Experiment 7: the analytics workload peaked at ~485 MB, so a 512Mi request and 1Gi limit leave headroom.

## Prerequisites

Docker Desktop with Kubernetes enabled (or minikube / kind) and the image from Experiment 2.

```powershell
# minikube:   minikube start ; minikube image load canesense-ai:1.0
# kind:       kind create cluster ; kind load docker-image canesense-ai:1.0
# Docker Desktop Kubernetes uses the local image directly.
# Using Docker Hub instead: edit image: in k8s/deployment.yaml to <user>/canesense-ai:1.0
```

## Deploy

```powershell
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml -f k8s/deployment.yaml -f k8s/service.yaml
kubectl -n canesense rollout status deployment/canesense-ai
kubectl -n canesense get pods,svc -o wide
```

## Access

```powershell
kubectl -n canesense port-forward svc/canesense-ai 8501:80
curl.exe http://localhost:8501/_stcore/health      # expect: ok
# minikube alternative: minikube service canesense-ai -n canesense --url
```

## Scale

```powershell
kubectl -n canesense scale deployment/canesense-ai --replicas=4
kubectl -n canesense get pods -w
# optional autoscaling
kubectl apply -f k8s/hpa.yaml ; kubectl -n canesense get hpa
```

## Recover (self-healing)

```powershell
kubectl -n canesense get pods
kubectl -n canesense delete pod <one-pod-name>
kubectl -n canesense get pods -w                   # a replacement pod is created and becomes Ready
```

Rolling update test: change the image tag, `kubectl apply -f k8s/deployment.yaml`, watch `kubectl rollout status`; roll back with `kubectl rollout undo deployment/canesense-ai -n canesense`.

## Note on Streamlit and multiple replicas

Streamlit keeps session state in each pod's memory. With more than one replica, browsers may reconnect to a different pod and lose the demo session; for a demo use one replica (`--replicas=1`) or enable session affinity on the Service/Ingress. This is a design limitation worth stating in the conclusion.

## Clean up

```powershell
kubectl delete -f k8s/
```
