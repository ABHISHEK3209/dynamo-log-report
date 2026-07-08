Parse the Apache-style access log at /app/access.log and write a JSON summary
report to /app/report.json.

Each non-empty line of the log is one request. A line begins with the client IP
address (the first whitespace-separated field) and contains an HTTP request line
of the form "METHOD PATH PROTOCOL", for example "GET /index.html HTTP/1.1".

Write /app/report.json as a single JSON object with exactly these three keys:

- "total_requests": integer, the number of non-empty request lines in the log.
- "unique_ips": integer, the number of distinct client IP addresses.
- "top_path": string, the request PATH that appears most often across all requests.

Success criteria:

1. /app/report.json exists and is a JSON object whose keys are exactly
   "total_requests", "unique_ips", and "top_path".
2. "total_requests" equals the number of non-empty request lines in /app/access.log.
3. "unique_ips" equals the number of distinct client IP addresses in /app/access.log.
4. "top_path" equals the most frequently requested path in /app/access.log.

Do not modify /app/access.log.

You have 120 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
