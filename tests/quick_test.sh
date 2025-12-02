#!/bin/bash
echo "Health check:"
curl -s http://localhost:8000/api/health || true
echo
echo "QA test (replace host if needed):"
curl -s -X POST "http://localhost:8000/api/query" -H "Content-Type: application/json" -d '{
  "type":"qa",
  "question":"Why did Hamilton pit on lap 30?",
  "driver_id":"44",
  "lap":30
}'
echo
