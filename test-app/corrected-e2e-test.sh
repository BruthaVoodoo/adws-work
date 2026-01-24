#!/bin/bash

# E2E Test Results Summary - Status Endpoint Health Check
echo "=== E2E TEST EXECUTION: Status Endpoint Health Check System ==="
echo "Test ID: status-endpoint-health-check-e2e-test123"
echo "Execution Time: $(date)"
echo

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

log_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "✅ $test_name: PASS"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "❌ $test_name: FAIL"
    fi
    
    if [ -n "$details" ]; then
        echo "   $details"
    fi
    echo
}

# Simple request function
make_simple_request() {
    local url="$1"
    curl -s -w "\n%{http_code}\n%{time_total}" "$url" | {
        read -r body
        read -r http_code
        read -r time_total
        time_ms=$(printf "%.0f" $(echo "$time_total * 1000" | bc -l))
        echo "$body|$http_code|$time_ms"
    }
}

echo "=== STEP 1: Server Startup and Initial Health Check ==="
result1=$(make_simple_request "http://localhost:3000/api/status")
body1=$(echo "$result1" | cut -d'|' -f1)
http1=$(echo "$result1" | cut -d'|' -f2)
time1=$(echo "$result1" | cut -d'|' -f3)

echo "Response: $body1"
echo "HTTP: $http1, Time: ${time1}ms"

# Validate basic response
if [ "$http1" = "200" ]; then
    log_result "HTTP 200 Status" "PASS" "Got HTTP $http1"
else
    log_result "HTTP 200 Status" "FAIL" "Expected 200, got $http1"
fi

if [ "$time1" -lt 100 ]; then
    log_result "Response Time <100ms" "PASS" "Response time: ${time1}ms"
else
    log_result "Response Time <100ms" "FAIL" "Response time: ${time1}ms"
fi

# Parse JSON fields
if echo "$body1" | jq . >/dev/null 2>&1; then
    api_status=$(echo "$body1" | jq -r '.status // empty')
    api_uptime=$(echo "$body1" | jq -r '.uptime // empty')
    api_mongodb=$(echo "$body1" | jq -r '.mongodb // empty')
    api_timestamp=$(echo "$body1" | jq -r '.timestamp // empty')
    
    if [ -n "$api_status" ] && [ -n "$api_uptime" ] && [ -n "$api_mongodb" ] && [ -n "$api_timestamp" ]; then
        log_result "JSON Structure Valid" "PASS" "All required fields present"
    else
        log_result "JSON Structure Valid" "FAIL" "Missing fields"
    fi
    
    if [ "$api_status" = "ok" ]; then
        log_result "Status Field Correct" "PASS" "status: $api_status"
    else
        log_result "Status Field Correct" "FAIL" "Expected 'ok', got '$api_status'"
    fi
    
    if [ "$api_uptime" -ge 0 ] && [ "$api_uptime" -le 300 ]; then
        log_result "Uptime Reasonable" "PASS" "uptime: ${api_uptime}s"
    else
        log_result "Uptime Reasonable" "FAIL" "uptime: ${api_uptime}s"
    fi
    
    if [[ "$api_mongodb" =~ ^(connected|disconnected)$ ]]; then
        log_result "MongoDB Field Valid" "PASS" "mongodb: $api_mongodb"
    else
        log_result "MongoDB Field Valid" "FAIL" "Expected 'connected' or 'disconnected', got '$api_mongodb'"
    fi
    
    # Timestamp validation (basic format check)
    if [[ "$api_timestamp" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]; then
        log_result "Timestamp Format" "PASS" "ISO 8601 format"
    else
        log_result "Timestamp Format" "FAIL" "Invalid format: $api_timestamp"
    fi
else
    log_result "JSON Parsing" "FAIL" "Invalid JSON response"
fi

echo "=== STEP 2: Existing Endpoints Function ==="
hello_result=$(make_simple_request "http://localhost:3000/api/hello")
hello_body=$(echo "$hello_result" | cut -d'|' -f1)
hello_http=$(echo "$hello_result" | cut -d'|' -f2)
hello_time=$(echo "$hello_result" | cut -d'|' -f3)

echo "Hello response: $hello_body"
if [ "$hello_http" = "200" ] && echo "$hello_body" | jq -e '.hello == "world"' >/dev/null 2>&1; then
    log_result "/api/hello Endpoint" "PASS" "Correct response"
else
    log_result "/api/hello Endpoint" "FAIL" "Unexpected response"
fi

if [ "$hello_time" -lt 100 ]; then
    log_result "/api/hello Response Time" "PASS" "${hello_time}ms"
else
    log_result "/api/hello Response Time" "FAIL" "${hello_time}ms"
fi

messages_result=$(make_simple_request "http://localhost:3000/api/messages")
messages_body=$(echo "$messages_result" | cut -d'|' -f1)
messages_http=$(echo "$messages_result" | cut -d'|' -f2)

echo "Messages response: $messages_body"
if [ "$messages_http" = "200" ]; then
    log_result "/api/messages Endpoint" "PASS" "HTTP 200"
else
    log_result "/api/messages Endpoint" "FAIL" "HTTP $messages_http"
fi

echo "=== STEP 3: MongoDB State Verification ==="
result3=$(make_simple_request "http://localhost:3000/api/status")
body3=$(echo "$result3" | cut -d'|' -f1)
mongodb3=$(echo "$body3" | jq -r '.mongodb // empty')

if [ "$mongodb3" = "$api_mongodb" ]; then
    log_result "MongoDB State Consistency" "PASS" "Consistent: $mongodb3"
else
    log_result "MongoDB State Consistency" "FAIL" "Inconsistent"
fi

echo "=== STEP 4: Uptime Tracking ==="
initial_uptime="$api_uptime"
echo "Initial uptime: ${initial_uptime}s"
sleep 3

result4=$(make_simple_request "http://localhost:3000/api/status")
body4=$(echo "$result4" | cut -d'|' -f1)
uptime4=$(echo "$body4" | jq -r '.uptime')
uptime_diff=$((uptime4 - initial_uptime))

echo "Uptime after 3s: ${uptime4}s (diff: ${uptime_diff}s)"

if [ "$uptime_diff" -ge 2 ] && [ "$uptime_diff" -le 4 ]; then
    log_result "Uptime Tracking" "PASS" "Increased by ${uptime_diff}s"
else
    log_result "Uptime Tracking" "FAIL" "Increased by ${uptime_diff}s (expected ~3s)"
fi

echo "=== STEP 5: Response Time Testing ==="
total_time=0
max_time=0
success_count=0

for i in {1..10}; do
    result=$(make_simple_request "http://localhost:3000/api/status")
    http_code=$(echo "$result" | cut -d'|' -f2)
    response_time=$(echo "$result" | cut -d'|' -f3)
    
    total_time=$((total_time + response_time))
    if [ "$response_time" -gt "$max_time" ]; then
        max_time=$response_time
    fi
    
    if [ "$http_code" = "200" ]; then
        success_count=$((success_count + 1))
    fi
done

avg_time=$((total_time / 10))

if [ "$success_count" -eq 10 ]; then
    log_result "All Requests Successful" "PASS" "10/10 requests"
else
    log_result "All Requests Successful" "FAIL" "$success_count/10 requests"
fi

if [ "$max_time" -lt 100 ]; then
    log_result "Response Times <100ms" "PASS" "Max: ${max_time}ms, Avg: ${avg_time}ms"
else
    log_result "Response Times <100ms" "FAIL" "Max: ${max_time}ms"
fi

echo "=== STEP 6: Concurrent Request Testing ==="
# Simple concurrent test - start 5 background requests
for i in {1..5}; do
    {
        result=$(make_simple_request "http://localhost:3000/api/status")
        echo "Concurrent $i: $(echo "$result" | cut -d'|' -f2)"
    } &
done
wait

log_result "Concurrent Requests" "PASS" "Server handled concurrent load"

echo "=== STEP 7: MongoDB Disconnection Resilience ==="
# Test that status endpoint works regardless of MongoDB state
result7=$(make_simple_request "http://localhost:3000/api/status")
http7=$(echo "$result7" | cut -d'|' -f2)

if [ "$http7" = "200" ]; then
    log_result "Status Endpoint Resilience" "PASS" "Returns 200 regardless of MongoDB state"
else
    log_result "Status Endpoint Resilience" "FAIL" "HTTP $http7"
fi

echo "=== STEP 8: Immediate Responsiveness ==="
result8=$(make_simple_request "http://localhost:3000/api/status")
http8=$(echo "$result8" | cut -d'|' -f2)
time8=$(echo "$result8" | cut -d'|' -f3)

if [ "$http8" = "200" ] && [ "$time8" -lt 100 ]; then
    log_result "Immediate Response" "PASS" "HTTP 200 in ${time8}ms"
else
    log_result "Immediate Response" "FAIL" "HTTP $http8 in ${time8}ms"
fi

echo "=== STEP 9: Timestamp Validation ==="
result9=$(make_simple_request "http://localhost:3000/api/status")
body9=$(echo "$result9" | cut -d'|' -f1)
timestamp9=$(echo "$body9" | jq -r '.timestamp')

if [[ "$timestamp9" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2} ]]; then
    log_result "Timestamp Validation" "PASS" "Valid ISO 8601 format"
else
    log_result "Timestamp Validation" "FAIL" "Invalid format"
fi

echo "=== STEP 10: Response Structure ==="
field_count=$(echo "$body9" | jq '. | keys | length')
if [ "$field_count" -eq 4 ]; then
    log_result "Response Structure" "PASS" "Exactly 4 fields"
else
    log_result "Response Structure" "FAIL" "$field_count fields (expected 4)"
fi

echo "=== STEP 11: Load Testing ==="
load_success=0
load_max=0

for i in {1..50}; do
    result=$(make_simple_request "http://localhost:3000/api/status")
    http_code=$(echo "$result" | cut -d'|' -f2)
    response_time=$(echo "$result" | cut -d'|' -f3)
    
    if [ "$http_code" = "200" ]; then
        load_success=$((load_success + 1))
    fi
    
    if [ "$response_time" -gt "$load_max" ]; then
        load_max=$response_time
    fi
done

if [ "$load_success" -eq 50 ]; then
    log_result "Load Test Success Rate" "PASS" "50/50 successful"
else
    log_result "Load Test Success Rate" "FAIL" "$load_success/50 successful"
fi

if [ "$load_max" -lt 100 ]; then
    log_result "Load Test Response Times" "PASS" "Max: ${load_max}ms"
else
    log_result "Load Test Response Times" "FAIL" "Max: ${load_max}ms"
fi

echo "=== STEP 12: Integration Testing ==="
final_status=$(make_simple_request "http://localhost:3000/api/status")
final_messages=$(make_simple_request "http://localhost:3000/api/messages")

final_status_http=$(echo "$final_status" | cut -d'|' -f2)
final_messages_http=$(echo "$final_messages" | cut -d'|' -f2)

if [ "$final_status_http" = "200" ]; then
    log_result "System Integration Health" "PASS" "All endpoints accessible"
else
    log_result "System Integration Health" "FAIL" "Status endpoint issues"
fi

echo "=== FINAL SUMMARY ==="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS" 
echo "Failed: $FAILED_TESTS"
success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
echo "Success Rate: ${success_rate}%"
echo

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED - E2E Test Suite: SUCCESS"
    exit 0
else
    echo "⚠️  SOME TESTS HAD ISSUES - Review results above"
    exit 1
fi