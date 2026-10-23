#!/usr/bin/env bash
# 通过 Prometheus HTTP API 执行 PromQL（与 Grafana 面板里填的表达式相同）
q() { echo "## $1"; curl -s "http://127.0.0.1:9090/api/v1/query" --data-urlencode "query=$1" |
      python3 -c "import json,sys;[print(r['metric'].get('job',''),r['value'][1]) for r in json.load(sys.stdin)['data']['result']]"; }
q 'up'
q 'histogram_quantile(0.95, sum by (le) (rate(mini_time_to_first_token_seconds_bucket[2m])))'
q 'histogram_quantile(0.50, sum by (le) (rate(mini_time_per_output_token_seconds_bucket[2m])))'
q 'rate(mini_generation_tokens_total[2m])'
q 'max_over_time(mini_num_requests_waiting[2m])'
