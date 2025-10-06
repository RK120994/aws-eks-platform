# High Error Rate Investigation Runbook

## 📋 Alert Details

**Alert Name**: HighErrorRate  
**Severity**: Critical  
**Trigger**: HTTP error rate (5xx) > 5% for 5 minutes  
**Impact**: Customer-facing service degradation  

## 🚨 Immediate Response (First 5 Minutes)

### 1. Acknowledge Alert
```bash
# Check current error rate across all environments
kubectl get pods -A -l app.kubernetes.io/name=sample-app
```

### 2. Assess Impact Scope
```bash
# Check error rate by environment
python scripts/dev-cli.py logs --environment prod --lines 50 | grep -i error

# Quick health check
curl -f https://api.example.com/health || echo "Service unavailable"
```

### 3. Check Service Status
```bash
# Verify pod status
kubectl get pods -n prod -l app.kubernetes.io/name=sample-app

# Check recent deployments
helm history sample-app -n prod
```

## 🔍 Investigation Steps

### Step 1: Analyze Error Patterns

#### Check Application Logs
```bash
# Tail recent logs for error patterns
python scripts/dev-cli.py logs --environment prod --follow --lines 100

# Search for specific error patterns
kubectl logs -n prod -l app.kubernetes.io/name=sample-app --tail=200 | grep -E "(ERROR|CRITICAL|500|502|503|504)"
```

#### Identify Error Types
Look for common patterns:
- `HTTP 500`: Application errors
- `HTTP 502`: Bad Gateway (upstream connection issues)
- `HTTP 503`: Service Unavailable (overload or health check failures)
- `HTTP 504`: Gateway Timeout (slow responses)

#### Check Error Distribution
```bash
# Check error distribution across pods
for pod in $(kubectl get pods -n prod -l app.kubernetes.io/name=sample-app -o name); do
  echo "=== $pod ==="
  kubectl logs -n prod $pod --tail=50 | grep -c ERROR || echo "0"
done
```

### Step 2: Infrastructure Health Check

#### Pod Resource Utilization
```bash
# Check CPU and memory usage
kubectl top pods -n prod -l app.kubernetes.io/name=sample-app

# Check resource limits and requests
kubectl describe pods -n prod -l app.kubernetes.io/name=sample-app | grep -A5 "Limits\|Requests"
```

#### Node Health
```bash
# Check node status and resources
kubectl get nodes
kubectl top nodes

# Check node conditions
kubectl describe nodes | grep -E "MemoryPressure|DiskPressure|PIDPressure"
```

#### Network Connectivity
```bash
# Test internal service connectivity
kubectl exec -it -n prod deployment/sample-app -- curl localhost:8000/health

# Check service endpoints
kubectl get endpoints -n prod sample-app

# Verify ingress status
kubectl describe ingress -n prod sample-app
```

### Step 3: Application-Specific Diagnostics

#### Health Check Analysis
```bash
# Test health endpoints directly
kubectl port-forward -n prod svc/sample-app 8080:80 &
curl http://localhost:8080/health
curl http://localhost:8080/health/live
curl http://localhost:8080/health/ready
```

#### Database Connectivity (if applicable)
```bash
# Check database connection from pod
kubectl exec -it -n prod deployment/sample-app -- python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print('Database connection: OK')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### External Dependencies
```bash
# Test external API connectivity
kubectl exec -it -n prod deployment/sample-app -- curl -v https://api.external-service.com/health
```

### Step 4: Metrics Analysis

#### Application Metrics
```bash
# Check Prometheus metrics
kubectl port-forward -n prod svc/sample-app 8080:80 &
curl http://localhost:8080/metrics | grep -E "(http_requests_total|http_request_duration|http_errors_total)"
```

#### Load Balancer Metrics
```bash
# Check ALB target group health
aws elbv2 describe-target-health --target-group-arn $(kubectl get ingress -n prod sample-app -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Check CloudWatch metrics for ALB
aws logs filter-log-events --log-group-name /aws/elasticloadbalancing/app/sample-app-alb --start-time $(date -d '10 minutes ago' +%s)000
```

## 🔧 Common Root Causes & Solutions

### 1. Application Code Issues

**Symptoms**: Consistent 500 errors, specific error patterns in logs
```bash
# Check for recent deployments
helm history sample-app -n prod

# Review recent changes
git log --oneline -10
```

**Solution**: Rollback to previous version
```bash
# Rollback using CLI tool
python scripts/dev-cli.py rollback --environment prod --confirm

# Or manual rollback
helm rollback sample-app -n prod
```

### 2. Resource Exhaustion

**Symptoms**: Pod restarts, OOMKilled events, CPU throttling
```bash
# Check resource usage
kubectl top pods -n prod -l app.kubernetes.io/name=sample-app

# Check events
kubectl get events -n prod --sort-by='.lastTimestamp' | grep sample-app
```

**Solution**: Scale up resources
```bash
# Emergency scaling
kubectl scale deployment sample-app -n prod --replicas=6

# Update resource limits (requires new deployment)
helm upgrade sample-app helm/sample-app \
  --namespace prod \
  --reuse-values \
  --set resources.limits.memory=2Gi \
  --set resources.limits.cpu=2000m
```

### 3. Database Connection Issues

**Symptoms**: Database connection errors, timeout errors
```bash
# Check database connectivity
kubectl exec -it -n prod deployment/sample-app -- nslookup database-hostname

# Check connection pool status (if applicable)
kubectl logs -n prod -l app.kubernetes.io/name=sample-app | grep -i "connection pool"
```

**Solution**: Restart pods or fix database issues
```bash
# Restart deployment
kubectl rollout restart deployment/sample-app -n prod

# Check database status
aws rds describe-db-instances --db-instance-identifier prod-database
```

### 4. Load Balancer Issues

**Symptoms**: 502/504 errors, intermittent connectivity
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn YOUR_TARGET_GROUP_ARN

# Check security groups
aws ec2 describe-security-groups --group-ids YOUR_SG_ID
```

**Solution**: Fix load balancer configuration
```bash
# Update ingress annotation
kubectl annotate ingress sample-app -n prod \
  alb.ingress.kubernetes.io/healthcheck-path="/health/ready" --overwrite
```

## 📊 Monitoring Commands

### Real-time Monitoring
```bash
# Monitor error rate in real-time
watch -n 5 'kubectl logs -n prod -l app.kubernetes.io/name=sample-app --tail=100 | grep -c ERROR'

# Monitor pod status
watch -n 10 'kubectl get pods -n prod -l app.kubernetes.io/name=sample-app'

# Monitor resource usage
watch -n 15 'kubectl top pods -n prod -l app.kubernetes.io/name=sample-app'
```

### Historical Analysis
```bash
# Check CloudWatch logs for patterns
aws logs filter-log-events \
  --log-group-name /aws/eks/demo-eks-prod/cluster \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# Check application metrics over time
# (This would typically be done through Grafana or CloudWatch console)
```

## 🚀 Recovery Actions

### Immediate Recovery (High Priority)

1. **Scale Up Application**
```bash
# Increase replica count
kubectl scale deployment sample-app -n prod --replicas=8
```

2. **Enable Circuit Breaker** (if implemented)
```bash
# Update configuration to enable circuit breaker
kubectl patch configmap sample-app-config -n prod --patch='{"data":{"circuit_breaker_enabled":"true"}}'
```

3. **Rollback to Last Known Good Version**
```bash
python scripts/dev-cli.py rollback --environment prod --confirm
```

### Load Shedding (If Necessary)

1. **Rate Limiting**
```bash
# Update ingress with rate limiting
kubectl annotate ingress sample-app -n prod \
  nginx.ingress.kubernetes.io/rate-limit="10" --overwrite
```

2. **Traffic Diversion**
```bash
# Redirect traffic to maintenance page
kubectl patch ingress sample-app -n prod --patch='
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maintenance-page
            port:
              number: 80'
```

## 📝 Post-Incident Actions

### 1. Verify Recovery
```bash
# Confirm error rate has decreased
python scripts/dev-cli.py logs --environment prod --lines 50 | grep -c ERROR

# Test critical user paths
curl -f https://api.example.com/health
curl -f https://api.example.com/
```

### 2. Collect Evidence
```bash
# Export logs for analysis
kubectl logs -n prod -l app.kubernetes.io/name=sample-app --since=1h > incident-logs-$(date +%Y%m%d-%H%M).txt

# Export metrics
curl http://localhost:8080/metrics > incident-metrics-$(date +%Y%m%d-%H%M).txt
```

### 3. Document Incident
- **Timeline**: When did the issue start/end?
- **Root Cause**: What caused the high error rate?
- **Impact**: How many users were affected?
- **Resolution**: What actions resolved the issue?
- **Prevention**: How can we prevent this in the future?

## 📞 Escalation Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| On-call Engineer | Slack: @oncall | Initial response |
| Senior DevOps | Slack: @devops-lead | After 15 minutes |
| Engineering Manager | Phone: +1-xxx-xxx-xxxx | After 30 minutes |
| Incident Commander | Slack: @incident-commander | Major outage |

## 🔗 Related Resources

- [Pod Crash Loop Debugging](pod-crashloop.md)
- [Network Connectivity Issues](network-issues.md)
- [Application Performance Monitoring Dashboard](https://grafana.company.com/d/app-performance)
- [Infrastructure Monitoring](https://cloudwatch.aws.amazon.com/dashboard)
- [Incident Response Playbook](https://wiki.company.com/incident-response)

## 📚 Additional Investigation Commands

### AWS-Specific Diagnostics
```bash
# Check EKS cluster health
aws eks describe-cluster --name demo-eks-prod --query 'cluster.status'

# Check node group status
aws eks describe-nodegroup --cluster-name demo-eks-prod --nodegroup-name demo-prod-nodes

# Check CloudTrail for recent changes
aws logs filter-log-events \
  --log-group-name CloudTrail/EKSClusterAuditLog \
  --start-time $(date -d '30 minutes ago' +%s)000
```

### Advanced Kubernetes Diagnostics
```bash
# Check API server logs
kubectl logs -n kube-system -l component=kube-apiserver

# Check scheduler decisions
kubectl get events --sort-by='.lastTimestamp' -A | grep -i schedule

# Check network policies (if enabled)
kubectl get networkpolicy -A
```

---

**Last Updated**: $(date)  
**Version**: 1.0  
**Owner**: DevOps Team
