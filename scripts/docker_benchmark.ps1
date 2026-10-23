# Container-enforced variant of Experiment 7 (requires Docker). NOT executed on the author's machine (Docker unavailable).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/docker_benchmark.ps1
docker build -t canesense-ai:1.0 .
foreach ($p in @(@{c="1";m="1g"}, @{c="2";m="1g"}, @{c="2";m="512m"}, @{c="4";m="2g"})) {
  Write-Host "== cpus=$($p.c) memory=$($p.m)"
  docker run --rm --cpus=$($p.c) --memory=$($p.m) --entrypoint python canesense-ai:1.0 scripts/benchmark.py --worker $($p.c) --scale 6
  docker stats --no-stream 2>$null
}
