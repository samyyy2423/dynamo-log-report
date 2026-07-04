There is an Apache-style access log at /app/access.log. Analyse the traffic and
write a summary report, as a single JSON object, to the file /app/report.json.
Use these exact key names: total_requests, unique_ips, top_path. Write only the
JSON object to that file, with no extra text.

Your report is correct when it meets all of the following criteria:

1. /app/report.json exists and contains a single JSON object.
2. total_requests equals the total number of request lines in /app/access.log.
3. unique_ips equals the number of distinct client IP addresses in the log,
   taking the first whitespace-separated field of each line as the client IP.
4. top_path equals the request path that appears in the greatest number of
   requests.
